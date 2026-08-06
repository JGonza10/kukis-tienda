# Kukis — Moda y Estilo

Tienda en línea de ropa, calzado y accesorios (mujer, hombre, niños y bebé), compuesta por una API REST en FastAPI y un frontend estático de una sola página (SPA) que consume esa API.

## Estado actual

**En desarrollo / prototipo funcional.** El backend expone un flujo de e-commerce completo (catálogo, carrito, pedidos, panel admin) y el frontend ya lo consume, pero hay señales claras de que el proyecto no está listo para producción real:

- El `JWT_SECRET` tiene un valor por defecto inseguro en el código (`main.py`) que debe sustituirse por variable de entorno real.
- El usuario administrador se inserta en `schema.sql` con un hash de contraseña de relleno (`$2b$12$REEMPLAZA_CON_HASH_BCRYPT_REAL`) que debe generarse y actualizarse manualmente.
- No hay integración de pago real: el método de pago se guarda como dato, pero no existe cobro efectivo con pasarela (PayPal, Stripe, etc.) — está listado como mejora futura en `DEPLOY.md`.
- No hay subida de imágenes implementada en el backend (las URLs de imágenes se guardan en tabla, pero la integración con Cloudinary es un paso pendiente descrito en `DEPLOY.md`).
- No se encontraron pruebas automatizadas, `.env.example`, `Procfile` ni configuración de CI en la raíz del proyecto (sí se mencionan en `DEPLOY.md` como parte de una estructura de carpetas `backend/`/`frontend/`/`db/` que hoy no existe; en este repositorio todos los archivos están en la raíz).

## Características principales

Basado en los endpoints reales de `main.py`:

- **Autenticación**: registro (`POST /auth/registro`) y login (`POST /auth/login`) con contraseñas hasheadas (bcrypt) y tokens JWT; validación de contraseña fuerte (mínimo 8 caracteres, mayúscula y número).
- **Catálogo de productos**: listado con filtros por categoría, género, búsqueda de texto, rango de precio y ofertas, con paginación (`GET /productos`); detalle de producto con variantes (talla/color/stock), imágenes y reseñas aprobadas (`GET /productos/{id}`).
- **Categorías y tallas**: catálogo de categorías (`GET /categorias`) y de tallas por tipo — ropa adulto/niño, calzado adulto/niño/bebé, talla única (`GET /tallas`).
- **Carrito de compras**: ver (`GET /carrito`), agregar con validación de stock (`POST /carrito`) y eliminar (`DELETE /carrito/{variante_id}`), asociado al usuario autenticado.
- **Pedidos**: creación de pedido a partir del carrito con verificación de stock, cálculo de IVA (16%) y número de pedido autogenerado (`POST /pedidos`); historial de pedidos del usuario (`GET /pedidos`).
- **Panel de administración** (roles `admin`/`editor`): dashboard con ventas del mes, pedidos pendientes y alertas de stock bajo (`GET /admin/dashboard`), listado y filtro de pedidos (`GET /admin/pedidos`), actualización de estado de pedido (`PATCH /admin/pedidos/{numero}`) y reporte de stock bajo (`GET /admin/stock-bajo`).
- **Frontend SPA** (`index.html`): catálogo navegable, modal de producto con selección de talla/color, carrito con `localStorage`, login/registro, flujo de checkout y una sección de administración integrada en la misma página.
- **Auditoría**: registro de acciones (login, registro, etc.) en tabla `log_auditoria`.
- **Reseñas y favoritos**: modelo de datos ya definido en `schema.sql` (tablas `resenas`, `favoritos`), aunque no todos tienen endpoint expuesto todavía en `main.py`.
- **Cupones de descuento**: tabla y datos de ejemplo en `schema.sql` (`cupones`), referenciados en el modelo de creación de pedido, pero sin lógica de aplicación de descuento implementada en el endpoint actual.

## Stack tecnológico

- **Backend**: Python + [FastAPI](https://fastapi.tiangolo.com/) 0.111, servido con Uvicorn.
- **Base de datos**: PostgreSQL, alojada en [Supabase](https://supabase.com) (confirmado en `main.py`, `schema.sql` y `DEPLOY.md`). Acceso mediante `asyncpg` con pool de conexiones asíncrono.
- **Autenticación**: JWT (`PyJWT`) + hashing de contraseñas con `bcrypt`.
- **Validación de datos**: Pydantic v2 (`pydantic[email]`).
- **Frontend**: HTML/CSS/JavaScript puro en un único archivo (`index.html`), sin framework ni build step; consume la API vía `fetch`.
- **Despliegue previsto** (ver `DEPLOY.md`): API en Render.com, frontend en Netlify, base de datos en Supabase e imágenes en Cloudinary — todo dentro de planes gratuitos.

Dependencias exactas (`requirements.txt`):

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
asyncpg==0.29.0
bcrypt==4.1.3
pyjwt==2.8.0
pydantic[email]==2.7.1
python-multipart==0.0.9
```

## Estructura del proyecto

```
07 Tienda en Linea Kukis/
├── main.py         # API FastAPI completa (auth, productos, carrito, pedidos, admin)
├── requirements.txt# Dependencias Python del backend
├── schema.sql       # Esquema completo de PostgreSQL (tablas, triggers, vistas, datos semilla)
├── index.html       # Frontend SPA (tienda + carrito + checkout + panel admin)
└── DEPLOY.md         # Guía paso a paso de despliegue (Supabase + Render + Netlify + Cloudinary)
```

> Nota: `DEPLOY.md` describe una organización en carpetas `backend/`, `frontend/` y `db/`; en este repositorio, tal como está hoy, todos los archivos viven en la raíz.

## Cómo instalar y ejecutar en local

### Requisitos previos

- Python 3.10+
- Una base de datos PostgreSQL accesible (puede ser un proyecto gratuito de Supabase, o PostgreSQL local)

### Pasos

1. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

2. Crear el esquema de base de datos ejecutando `schema.sql` contra tu instancia PostgreSQL (por ejemplo, desde el SQL Editor de Supabase o con `psql`):

   ```bash
   psql "postgresql://usuario:password@host:5432/basedatos" -f schema.sql
   ```

3. Definir las variables de entorno necesarias (ver detalle en `main.py`):

   | Variable | Descripción | Valor por defecto |
   |---|---|---|
   | `DATABASE_URL` | Cadena de conexión a PostgreSQL | `postgresql://user:pass@localhost/kukis` (solo referencia, no usar en producción) |
   | `JWT_SECRET` | Secreto para firmar los tokens JWT | inseguro por defecto — **debe cambiarse** |
   | `JWT_EXPIRE_HOURS` | Horas de vigencia del token | `24` |
   | `CORS_ORIGINS` | Orígenes permitidos por CORS, separados por coma | `http://localhost,https://kukis-moda.netlify.app` |

   Ejemplo en PowerShell:

   ```powershell
   $env:DATABASE_URL = "postgresql://usuario:password@host:5432/basedatos"
   $env:JWT_SECRET = "genera-un-valor-con-openssl-rand-hex-32"
   $env:JWT_EXPIRE_HOURS = "24"
   $env:CORS_ORIGINS = "http://localhost"
   ```

4. Levantar la API:

   ```bash
   uvicorn main:app --reload --port 8000
   ```

5. Verificar que responde:

   - `http://localhost:8000/health`
   - Documentación interactiva: `http://localhost:8000/docs`

6. Abrir el frontend: `index.html` puede abrirse directamente en el navegador o servirse con cualquier servidor estático. Por defecto apunta a `https://kukis-api.onrender.com`; para usar la API local hay que cambiar la URL desde el propio panel de la tienda (menú Admin → Configuración) o editar la constante `API_URL` en `index.html`.

7. (Opcional) Generar el hash de la contraseña del usuario administrador y actualizarlo en la base de datos, ya que `schema.sql` inserta un hash de relleno:

   ```bash
   python -c "import bcrypt; print(bcrypt.hashpw(b'TuPassword', bcrypt.gensalt(12)).decode())"
   ```

## Documentación relacionada

Para el despliegue completo a producción (Supabase + Render + Netlify + Cloudinary, variables de entorno de cada servicio, comandos de prueba con `curl` y el roadmap de mejoras futuras) consulta **[`DEPLOY.md`](./DEPLOY.md)**, que incluye la guía paso a paso completa.

## Notas relevantes

- El backend no incluye por sí mismo endpoints de subida de imágenes ni integración con Cloudinary; esa integración es un paso pendiente documentado en `DEPLOY.md`.
- No se detectaron archivos de pruebas automatizadas (`tests/`, `pytest`, etc.) en el proyecto.
- Nunca subas valores reales de `DATABASE_URL`, `JWT_SECRET` ni contraseñas al repositorio; usa siempre variables de entorno.
- Autor: Juan González Mendoza (según cabeceras de `main.py` y `schema.sql`).
