"""
KUKIS MODA Y ESTILO — API Backend
FastAPI + PostgreSQL (Supabase)
Autor: Juan González Mendoza
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import asyncpg
import bcrypt
import jwt
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re

# ─── Configuración ───────────────────────────────────────
DB_URL     = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost/kukis")

JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError(
        "La variable de entorno JWT_SECRET es obligatoria y no está configurada. "
        "Genera un valor seguro (por ejemplo: openssl rand -hex 32 o "
        "python -c \"import secrets; print(secrets.token_hex(32))\") y defínela "
        "como variable de entorno antes de arrancar la aplicación."
    )

JWT_EXPIRE = int(os.environ.get("JWT_EXPIRE_HOURS", 24))
ORIGINS    = os.environ.get("CORS_ORIGINS", "http://localhost,https://kukis-moda.netlify.app").split(",")

# ─── Pool de conexiones (se inicia al arrancar) ──────────
pool: asyncpg.Pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = await asyncpg.create_pool(DB_URL, min_size=2, max_size=10)
    print("✅ Conexión a PostgreSQL establecida")
    yield
    await pool.close()
    print("🔌 Pool cerrado")

app = FastAPI(
    title="Kukis API",
    description="Backend de Kukis Moda y Estilo",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


# ═══════════════════════════════════════════════════════════
#  MODELOS (Pydantic — validación automática)
# ═══════════════════════════════════════════════════════════

class RegistroIn(BaseModel):
    nombre:    str
    apellidos: Optional[str] = None
    email:     EmailStr
    telefono:  Optional[str] = None
    password:  str

    @field_validator("password")
    @classmethod
    def password_fuerte(cls, v):
        if len(v) < 8:
            raise ValueError("Mínimo 8 caracteres")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Debe tener al menos una mayúscula")
        if not re.search(r"\d", v):
            raise ValueError("Debe tener al menos un número")
        return v

class LoginIn(BaseModel):
    email:    EmailStr
    password: str

class AgregarCarritoIn(BaseModel):
    id_variante: str
    cantidad:    int = 1

class CrearPedidoIn(BaseModel):
    metodo_pago:    str
    nombre_dest:    str
    calle:          str
    numero_ext:     Optional[str] = None
    colonia:        Optional[str] = None
    ciudad:         str
    estado_rep:     str
    cp:             str
    telefono:       Optional[str] = None
    referencias:    Optional[str] = None
    codigo_cupon:   Optional[str] = None


# ═══════════════════════════════════════════════════════════
#  UTILIDADES JWT
# ═══════════════════════════════════════════════════════════

def crear_token(user_id: str, rol: str) -> str:
    payload = {
        "sub": user_id,
        "rol": rol,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

async def usuario_actual(
    creds: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    if not creds:
        raise HTTPException(status_code=401, detail="Token requerido")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
        return {"id": payload["sub"], "rol": payload["rol"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def solo_admin(user=Depends(usuario_actual)):
    if user["rol"] not in ("admin", "editor"):
        raise HTTPException(status_code=403, detail="Sin permisos de administrador")
    return user


# ═══════════════════════════════════════════════════════════
#  ENDPOINTS: HEALTH
# ═══════════════════════════════════════════════════════════

@app.get("/", tags=["General"])
async def raiz():
    return {"mensaje": "🛍 Kukis API v2.0 — En línea", "docs": "/docs"}

@app.get("/health", tags=["General"])
async def health():
    try:
        await pool.fetchval("SELECT 1")
        return {"estado": "ok", "db": "conectada"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"DB error: {e}")


# ═══════════════════════════════════════════════════════════
#  ENDPOINTS: AUTENTICACIÓN
# ═══════════════════════════════════════════════════════════

@app.post("/auth/registro", status_code=201, tags=["Auth"])
async def registro(datos: RegistroIn, req: Request):
    # Verificar si email ya existe
    existe = await pool.fetchval(
        "SELECT id FROM usuarios WHERE email = $1", datos.email
    )
    if existe:
        raise HTTPException(status_code=409, detail="Este correo ya está registrado")

    hash_pw = bcrypt.hashpw(datos.password.encode(), bcrypt.gensalt(12)).decode()

    user_id = await pool.fetchval("""
        INSERT INTO usuarios (nombre, apellidos, email, telefono, contrasena_hash, id_rol)
        VALUES ($1, $2, $3, $4, $5, 3)
        RETURNING id
    """, datos.nombre, datos.apellidos, datos.email, datos.telefono, hash_pw)

    await pool.execute("""
        INSERT INTO log_auditoria (id_usuario, accion, ip) VALUES ($1, 'registro', $2)
    """, user_id, str(req.client.host))

    token = crear_token(str(user_id), "cliente")
    return {"token": token, "nombre": datos.nombre, "rol": "cliente"}


@app.post("/auth/login", tags=["Auth"])
async def login(datos: LoginIn, req: Request):
    user = await pool.fetchrow("""
        SELECT u.id, u.nombre, u.contrasena_hash, u.activo, r.nombre as rol
        FROM usuarios u JOIN roles r ON r.id = u.id_rol
        WHERE u.email = $1
    """, datos.email)

    if not user or not bcrypt.checkpw(datos.password.encode(), user["contrasena_hash"].encode()):
        await pool.execute("""
            INSERT INTO log_auditoria (accion, ip, resultado)
            VALUES ('login_fallido', $1, 'error')
        """, str(req.client.host))
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if not user["activo"]:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    await pool.execute(
        "UPDATE usuarios SET ultimo_login = NOW() WHERE id = $1", user["id"]
    )
    await pool.execute("""
        INSERT INTO log_auditoria (id_usuario, accion, ip) VALUES ($1, 'login', $2)
    """, user["id"], str(req.client.host))

    token = crear_token(str(user["id"]), user["rol"])
    return {"token": token, "nombre": user["nombre"], "rol": user["rol"]}


# ═══════════════════════════════════════════════════════════
#  ENDPOINTS: PRODUCTOS (público)
# ═══════════════════════════════════════════════════════════

@app.get("/productos", tags=["Productos"])
async def listar_productos(
    categoria:   Optional[str] = None,
    genero:      Optional[str] = None,
    busqueda:    Optional[str] = None,
    min_precio:  Optional[float] = None,
    max_precio:  Optional[float] = None,
    solo_oferta: bool = False,
    pagina:      int = 1,
    por_pagina:  int = 20
):
    condiciones = ["p.activo = TRUE"]
    params = []
    i = 1

    if categoria:
        condiciones.append(f"c.slug = ${i}"); params.append(categoria); i += 1
    if genero:
        condiciones.append(f"p.genero = ${i}"); params.append(genero); i += 1
    if busqueda:
        condiciones.append(f"p.nombre ILIKE ${i}"); params.append(f"%{busqueda}%"); i += 1
    if min_precio:
        condiciones.append(f"COALESCE(p.precio_oferta, p.precio_base) >= ${i}"); params.append(min_precio); i += 1
    if max_precio:
        condiciones.append(f"COALESCE(p.precio_oferta, p.precio_base) <= ${i}"); params.append(max_precio); i += 1
    if solo_oferta:
        condiciones.append("p.precio_oferta IS NOT NULL")

    where = " AND ".join(condiciones)
    offset = (pagina - 1) * por_pagina

    sql = f"""
        SELECT
            p.id::TEXT, p.nombre, p.descripcion,
            c.nombre AS categoria, c.slug AS categoria_slug,
            p.genero,
            p.precio_base,
            p.precio_oferta,
            COALESCE(p.precio_oferta, p.precio_base) AS precio_final,
            CASE WHEN p.precio_oferta IS NOT NULL
                 THEN ROUND((1 - p.precio_oferta/p.precio_base)*100)::INT
                 ELSE 0 END AS descuento_pct,
            COALESCE(SUM(pv.stock),0) AS stock_total,
            p.destacado, p.nuevo, p.calificacion, p.num_resenas,
            (SELECT url FROM imagenes_producto WHERE id_producto = p.id AND es_principal = TRUE LIMIT 1) AS imagen_url
        FROM productos p
        JOIN categorias c ON c.id = p.id_categoria
        LEFT JOIN producto_variantes pv ON pv.id_producto = p.id AND pv.activo = TRUE
        WHERE {where}
        GROUP BY p.id, c.nombre, c.slug
        ORDER BY p.destacado DESC, p.creado_en DESC
        LIMIT ${i} OFFSET ${i+1}
    """
    params += [por_pagina, offset]

    rows = await pool.fetch(sql, *params)

    # Total para paginación
    count_sql = f"""
        SELECT COUNT(DISTINCT p.id) FROM productos p
        JOIN categorias c ON c.id = p.id_categoria
        WHERE {where}
    """
    total = await pool.fetchval(count_sql, *params[:-2])

    return {
        "productos": [dict(r) for r in rows],
        "total": total,
        "pagina": pagina,
        "paginas": (total + por_pagina - 1) // por_pagina
    }


@app.get("/productos/{producto_id}", tags=["Productos"])
async def detalle_producto(producto_id: str):
    prod = await pool.fetchrow("""
        SELECT
            p.id::TEXT, p.nombre, p.descripcion, p.marca, p.material,
            c.nombre AS categoria, c.slug, p.genero,
            p.precio_base, p.precio_oferta,
            p.calificacion, p.num_resenas, p.destacado, p.nuevo
        FROM productos p
        JOIN categorias c ON c.id = p.id_categoria
        WHERE p.id = $1 AND p.activo = TRUE
    """, uuid.UUID(producto_id))

    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Variantes con talla y color
    variantes = await pool.fetch("""
        SELECT
            pv.id::TEXT, ct.tipo AS tipo_talla, ct.codigo AS talla,
            ct.descripcion AS talla_desc, pv.color, pv.color_hex,
            pv.sku_variante, pv.stock,
            p.precio_base + COALESCE(pv.precio_extra, 0) AS precio
        FROM producto_variantes pv
        JOIN catalogo_tallas ct ON ct.id = pv.id_talla
        JOIN productos p ON p.id = pv.id_producto
        WHERE pv.id_producto = $1 AND pv.activo = TRUE
        ORDER BY ct.orden, pv.color
    """, uuid.UUID(producto_id))

    # Imágenes
    imagenes = await pool.fetch("""
        SELECT url, url_thumb, alt_text, es_principal, orden
        FROM imagenes_producto
        WHERE id_producto = $1
        ORDER BY es_principal DESC, orden
    """, uuid.UUID(producto_id))

    # Reseñas aprobadas
    resenas = await pool.fetch("""
        SELECT r.calificacion, r.titulo, r.comentario,
               u.nombre AS autor, r.creado_en
        FROM resenas r JOIN usuarios u ON u.id = r.id_usuario
        WHERE r.id_producto = $1 AND r.aprobada = TRUE
        ORDER BY r.creado_en DESC LIMIT 10
    """, uuid.UUID(producto_id))

    # Incrementar vistas
    await pool.execute(
        "UPDATE productos SET vistas = vistas + 1 WHERE id = $1",
        uuid.UUID(producto_id)
    )

    return {
        **dict(prod),
        "variantes": [dict(v) for v in variantes],
        "imagenes":  [dict(i) for i in imagenes],
        "resenas":   [dict(r) for r in resenas],
    }


@app.get("/tallas", tags=["Productos"])
async def listar_tallas(tipo: Optional[str] = None):
    sql = "SELECT id, tipo, codigo, descripcion, orden FROM catalogo_tallas"
    params = []
    if tipo:
        sql += " WHERE tipo = $1"
        params.append(tipo)
    sql += " ORDER BY tipo, orden"
    rows = await pool.fetch(sql, *params)
    return [dict(r) for r in rows]


@app.get("/categorias", tags=["Productos"])
async def listar_categorias():
    rows = await pool.fetch("""
        SELECT c.id, c.nombre, c.slug, c.descripcion, c.icono,
               COUNT(DISTINCT p.id) AS total_productos
        FROM categorias c
        LEFT JOIN productos p ON p.id_categoria = c.id AND p.activo = TRUE
        WHERE c.activa = TRUE
        GROUP BY c.id
        ORDER BY c.orden
    """)
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════
#  ENDPOINTS: CARRITO
# ═══════════════════════════════════════════════════════════

@app.get("/carrito", tags=["Carrito"])
async def ver_carrito(user=Depends(usuario_actual)):
    rows = await pool.fetch("""
        SELECT
            car.id::TEXT,
            car.id_variante::TEXT,
            pr.nombre AS producto,
            ct.codigo AS talla,
            pv.color,
            pv.color_hex,
            car.cantidad,
            pv.stock,
            (pr.precio_base + COALESCE(pv.precio_extra,0)) *
            CASE WHEN pr.precio_oferta IS NOT NULL
                 THEN pr.precio_oferta / pr.precio_base
                 ELSE 1 END                AS precio_unit,
            (SELECT url FROM imagenes_producto
             WHERE id_producto = pr.id AND es_principal=TRUE LIMIT 1) AS imagen
        FROM carrito car
        JOIN producto_variantes pv ON pv.id = car.id_variante
        JOIN productos pr ON pr.id = pv.id_producto
        JOIN catalogo_tallas ct ON ct.id = pv.id_talla
        WHERE car.id_usuario = $1
        ORDER BY car.agregado_en DESC
    """, uuid.UUID(user["id"]))

    items = [dict(r) for r in rows]
    subtotal = sum(i["precio_unit"] * i["cantidad"] for i in items)
    return {"items": items, "subtotal": round(subtotal, 2), "total_items": len(items)}


@app.post("/carrito", status_code=201, tags=["Carrito"])
async def agregar_carrito(datos: AgregarCarritoIn, user=Depends(usuario_actual)):
    stock = await pool.fetchval(
        "SELECT stock FROM producto_variantes WHERE id = $1 AND activo = TRUE",
        uuid.UUID(datos.id_variante)
    )
    if stock is None:
        raise HTTPException(status_code=404, detail="Variante no encontrada")
    if stock < datos.cantidad:
        raise HTTPException(status_code=400, detail=f"Solo hay {stock} piezas en stock")

    await pool.execute("""
        INSERT INTO carrito (id_usuario, id_variante, cantidad)
        VALUES ($1, $2, $3)
        ON CONFLICT (id_usuario, id_variante)
        DO UPDATE SET cantidad = carrito.cantidad + $3
    """, uuid.UUID(user["id"]), uuid.UUID(datos.id_variante), datos.cantidad)

    return {"mensaje": "Agregado al carrito"}


@app.delete("/carrito/{variante_id}", tags=["Carrito"])
async def quitar_carrito(variante_id: str, user=Depends(usuario_actual)):
    await pool.execute("""
        DELETE FROM carrito WHERE id_usuario = $1 AND id_variante = $2
    """, uuid.UUID(user["id"]), uuid.UUID(variante_id))
    return {"mensaje": "Eliminado del carrito"}


# ═══════════════════════════════════════════════════════════
#  ENDPOINTS: PEDIDOS
# ═══════════════════════════════════════════════════════════

@app.post("/pedidos", status_code=201, tags=["Pedidos"])
async def crear_pedido(datos: CrearPedidoIn, user=Depends(usuario_actual)):
    # Obtener carrito
    items = await pool.fetch("""
        SELECT car.id_variante, car.cantidad,
               pr.precio_base + COALESCE(pv.precio_extra,0) AS precio_unit,
               pr.nombre, ct.codigo AS talla, pv.color, pv.sku_variante, pv.stock
        FROM carrito car
        JOIN producto_variantes pv ON pv.id = car.id_variante
        JOIN productos pr ON pr.id = pv.id_producto
        JOIN catalogo_tallas ct ON ct.id = pv.id_talla
        WHERE car.id_usuario = $1
    """, uuid.UUID(user["id"]))

    if not items:
        raise HTTPException(status_code=400, detail="El carrito está vacío")

    # Verificar stock
    for item in items:
        if item["stock"] < item["cantidad"]:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {item['nombre']} talla {item['talla']}"
            )

    subtotal = sum(i["precio_unit"] * i["cantidad"] for i in items)
    iva      = round(subtotal * 0.16, 2)
    total    = round(subtotal + iva, 2)

    async with pool.acquire() as conn:
        async with conn.transaction():
            pedido_id = await conn.fetchval("""
                INSERT INTO pedidos
                    (id_usuario, numero_pedido, subtotal, iva, total, metodo_pago)
                VALUES ($1, '', $2, $3, $4, $5)
                RETURNING id
            """, uuid.UUID(user["id"]), subtotal, iva, total, datos.metodo_pago)

            # Actualizar número de pedido (trigger en DB)
            await conn.execute("""
                UPDATE pedidos SET numero_pedido =
                    'KUK-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' ||
                    LPAD((SELECT COUNT(*) FROM pedidos WHERE DATE_TRUNC('day',creado_en)=CURRENT_DATE)::TEXT, 4, '0')
                WHERE id = $1
            """, pedido_id)

            # Insertar detalles
            for item in items:
                await conn.execute("""
                    INSERT INTO detalle_pedido
                        (id_pedido, id_variante, nombre_producto, talla, color, sku, cantidad, precio_unit)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, pedido_id, item["id_variante"], item["nombre"],
                    item["talla"], item["color"], item["sku_variante"],
                    item["cantidad"], item["precio_unit"])

            # Dirección de envío
            await conn.execute("""
                INSERT INTO direcciones_envio
                    (id_pedido, nombre_dest, calle, numero_ext, colonia,
                     ciudad, estado_rep, cp, telefono, referencias)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            """, pedido_id, datos.nombre_dest, datos.calle, datos.numero_ext,
                datos.colonia, datos.ciudad, datos.estado_rep,
                datos.cp, datos.telefono, datos.referencias)

            # Limpiar carrito
            await conn.execute(
                "DELETE FROM carrito WHERE id_usuario = $1",
                uuid.UUID(user["id"])
            )

    numero = await pool.fetchval(
        "SELECT numero_pedido FROM pedidos WHERE id = $1", pedido_id
    )
    return {"pedido": numero, "total": total, "mensaje": "¡Pedido creado exitosamente!"}


@app.get("/pedidos", tags=["Pedidos"])
async def mis_pedidos(user=Depends(usuario_actual)):
    rows = await pool.fetch("""
        SELECT p.numero_pedido, p.estado, p.total, p.metodo_pago,
               p.creado_en, d.guia_envio, d.paqueteria
        FROM pedidos p
        LEFT JOIN direcciones_envio d ON d.id_pedido = p.id
        WHERE p.id_usuario = $1
        ORDER BY p.creado_en DESC
    """, uuid.UUID(user["id"]))
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════
#  ENDPOINTS: ADMIN
# ═══════════════════════════════════════════════════════════

@app.get("/admin/dashboard", tags=["Admin"])
async def dashboard(admin=Depends(solo_admin)):
    hoy = await pool.fetchrow("""
        SELECT
            COUNT(*) FILTER (WHERE DATE_TRUNC('day', creado_en) = CURRENT_DATE) AS pedidos_hoy,
            COALESCE(SUM(total) FILTER (WHERE DATE_TRUNC('month', creado_en) = DATE_TRUNC('month', NOW())), 0) AS ventas_mes,
            COUNT(*) FILTER (WHERE estado = 'pendiente') AS pendientes
        FROM pedidos
    """)
    productos = await pool.fetchval("SELECT COUNT(*) FROM productos WHERE activo = TRUE")
    usuarios  = await pool.fetchval("SELECT COUNT(*) FROM usuarios WHERE id_rol = 3")
    bajo_stock = await pool.fetch("SELECT * FROM v_alerta_stock LIMIT 5")

    return {
        "pedidos_hoy":  hoy["pedidos_hoy"],
        "ventas_mes":   float(hoy["ventas_mes"]),
        "pendientes":   hoy["pendientes"],
        "productos":    productos,
        "usuarios":     usuarios,
        "alerta_stock": [dict(r) for r in bajo_stock]
    }


@app.get("/admin/pedidos", tags=["Admin"])
async def admin_pedidos(estado: Optional[str] = None, admin=Depends(solo_admin)):
    sql = """
        SELECT p.numero_pedido, p.estado, p.total, p.metodo_pago,
               p.creado_en, u.nombre AS cliente, u.email
        FROM pedidos p JOIN usuarios u ON u.id = p.id_usuario
    """
    params = []
    if estado:
        sql += " WHERE p.estado = $1"
        params.append(estado)
    sql += " ORDER BY p.creado_en DESC LIMIT 100"
    rows = await pool.fetch(sql, *params)
    return [dict(r) for r in rows]


@app.patch("/admin/pedidos/{numero}", tags=["Admin"])
async def actualizar_estado_pedido(
    numero: str, estado: str, admin=Depends(solo_admin)
):
    estados_validos = ['pendiente','pagado','preparando','enviado','entregado','cancelado','devuelto']
    if estado not in estados_validos:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Usa: {estados_validos}")

    result = await pool.execute("""
        UPDATE pedidos SET estado = $1, actualizado_en = NOW()
        WHERE numero_pedido = $2
    """, estado, numero)

    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"mensaje": f"Pedido {numero} actualizado a '{estado}'"}


@app.get("/admin/stock-bajo", tags=["Admin"])
async def stock_bajo(admin=Depends(solo_admin)):
    rows = await pool.fetch("SELECT * FROM v_alerta_stock")
    return [dict(r) for r in rows]
