-- ═══════════════════════════════════════════════════════════════════════════
--  KUKIS MODA Y ESTILO — Base de Datos de Producción
--  Motor: PostgreSQL 15+  (Supabase / Railway / Render)
--  Autor: Sistema generado para Juan González Mendoza
--  Versión: 2.0 — Producción completa
-- ═══════════════════════════════════════════════════════════════════════════

-- Extensión para UUIDs (IDs más seguros que enteros auto-incrementales)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────────────────────
--  ENUMERACIONES  (tipos fijos del negocio)
-- ─────────────────────────────────────────────────────────

CREATE TYPE rol_usuario   AS ENUM ('admin', 'editor', 'cliente');
CREATE TYPE estado_pedido AS ENUM ('pendiente','pagado','preparando','enviado','entregado','cancelado','devuelto');
CREATE TYPE metodo_pago   AS ENUM ('paypal','tarjeta_credito','tarjeta_debito','oxxo','transferencia','efectivo');
CREATE TYPE tipo_talla    AS ENUM ('ropa_adulto','ropa_nino','calzado_adulto','calzado_nino','calzado_bebe','unica');
CREATE TYPE genero_prod   AS ENUM ('mujer','hombre','nino','nina','unisex','bebe');


-- ─────────────────────────────────────────────────────────
--  TABLA: roles  (permisos del sistema)
-- ─────────────────────────────────────────────────────────
CREATE TABLE roles (
    id          SERIAL PRIMARY KEY,
    nombre      rol_usuario NOT NULL UNIQUE,
    descripcion TEXT,
    permisos    JSONB DEFAULT '{}',   -- {"productos":true,"pedidos":true,"usuarios":false}
    creado_en   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO roles (nombre, descripcion, permisos) VALUES
    ('admin',  'Control total del sistema',
     '{"productos":true,"pedidos":true,"usuarios":true,"reportes":true,"config":true}'),
    ('editor', 'Gestiona catálogo y pedidos',
     '{"productos":true,"pedidos":true,"usuarios":false,"reportes":true,"config":false}'),
    ('cliente','Usuario comprador',
     '{"productos":false,"pedidos":false,"usuarios":false,"reportes":false,"config":false}');


-- ─────────────────────────────────────────────────────────
--  TABLA: usuarios
-- ─────────────────────────────────────────────────────────
CREATE TABLE usuarios (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre          VARCHAR(120) NOT NULL,
    apellidos       VARCHAR(120),
    email           VARCHAR(200) NOT NULL UNIQUE,
    telefono        VARCHAR(20),
    contrasena_hash VARCHAR(255) NOT NULL,          -- bcrypt $2b$12$...
    id_rol          INTEGER NOT NULL DEFAULT 3      -- 3 = cliente
                    REFERENCES roles(id) ON UPDATE CASCADE,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    verificado      BOOLEAN NOT NULL DEFAULT FALSE, -- email verificado
    avatar_url      TEXT,
    token_verificar VARCHAR(100),                   -- para confirmar email
    token_reset     VARCHAR(100),                   -- recuperar contraseña
    token_expira    TIMESTAMPTZ,
    ultimo_login    TIMESTAMPTZ,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Admin inicial — password: Admin.Kukis2025! (cámbiala en producción)
-- Hash generado con bcrypt rounds=12
INSERT INTO usuarios (nombre, apellidos, email, telefono, contrasena_hash, id_rol, activo, verificado)
VALUES (
    'Juan', 'González Mendoza',
    'juangonzamen10@gmail.com',
    '5573744800',
    '$2b$12$REEMPLAZA_CON_HASH_BCRYPT_REAL',   -- genera con: python -c "import bcrypt; print(bcrypt.hashpw(b'Admin.Kukis2025!', bcrypt.gensalt(12)).decode())"
    1, TRUE, TRUE
);

CREATE INDEX idx_usuarios_email  ON usuarios(email);
CREATE INDEX idx_usuarios_rol    ON usuarios(id_rol);
CREATE INDEX idx_usuarios_activo ON usuarios(activo);


-- ─────────────────────────────────────────────────────────
--  TABLA: categorias
-- ─────────────────────────────────────────────────────────
CREATE TABLE categorias (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(80)  NOT NULL UNIQUE,
    slug        VARCHAR(80)  NOT NULL UNIQUE,    -- para URLs: /categoria/mujer
    descripcion TEXT,
    icono       VARCHAR(10),                     -- emoji
    imagen_url  TEXT,
    padre_id    INTEGER REFERENCES categorias(id) ON DELETE SET NULL, -- subcategorías
    orden       SMALLINT NOT NULL DEFAULT 0,
    activa      BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO categorias (nombre, slug, descripcion, icono, orden) VALUES
    ('Mujer',           'mujer',       'Ropa y accesorios femeninos',           '👗', 1),
    ('Hombre',          'hombre',      'Ropa y accesorios masculinos',           '👔', 2),
    ('Niñas',           'ninas',       'Ropa para niñas',                        '👧', 3),
    ('Niños',           'ninos',       'Ropa para niños',                        '🧒', 4),
    ('Bebé',            'bebe',        'Ropa para bebés 0-24 meses',             '👶', 5),
    ('Accesorios',      'accesorios',  'Bolsas, bufandas, cinturones, sombreros','👜', 6),
    ('Calzado Mujer',   'calzado-mujer',   'Zapatos, botas, zapatillas femeninas','👠', 7),
    ('Calzado Hombre',  'calzado-hombre',  'Zapatos, botas, tenis masculinos',   '👞', 8),
    ('Calzado Niños',   'calzado-ninos',   'Calzado infantil',                   '👟', 9),
    ('Deportes',        'deportes',    'Ropa y calzado deportivo',               '🏃',10),
    ('Plus Size',       'plus-size',   'Tallas grandes para todos',              '✨',11);


-- ─────────────────────────────────────────────────────────
--  CATÁLOGO DE TALLAS  (maestro reutilizable)
-- ─────────────────────────────────────────────────────────
CREATE TABLE catalogo_tallas (
    id          SERIAL PRIMARY KEY,
    tipo        tipo_talla NOT NULL,
    codigo      VARCHAR(10) NOT NULL,    -- XS, S, M, L, 38, 24, etc.
    descripcion VARCHAR(80),             -- "Chica / Pecho 80-84cm"
    orden       SMALLINT NOT NULL DEFAULT 0,
    UNIQUE(tipo, codigo)
);

-- Tallas ropa adulto
INSERT INTO catalogo_tallas (tipo, codigo, descripcion, orden) VALUES
    ('ropa_adulto','XS',  'Extra chica  / Pecho 76-80 cm',  1),
    ('ropa_adulto','S',   'Chica        / Pecho 80-84 cm',  2),
    ('ropa_adulto','M',   'Mediana      / Pecho 84-88 cm',  3),
    ('ropa_adulto','L',   'Grande       / Pecho 88-96 cm',  4),
    ('ropa_adulto','XL',  'Extra grande / Pecho 96-104 cm', 5),
    ('ropa_adulto','XXL', '2X grande    / Pecho 104-114 cm',6),
    ('ropa_adulto','3XL', '3X grande    / Pecho 114-124 cm',7),
    ('ropa_adulto','4XL', '4X grande    / Pecho 124-134 cm',8),
    ('ropa_adulto','26',  'Cintura 26"  (jeans/pantalón)',  9),
    ('ropa_adulto','28',  'Cintura 28"  (jeans/pantalón)', 10),
    ('ropa_adulto','30',  'Cintura 30"  (jeans/pantalón)', 11),
    ('ropa_adulto','32',  'Cintura 32"  (jeans/pantalón)', 12),
    ('ropa_adulto','34',  'Cintura 34"  (jeans/pantalón)', 13),
    ('ropa_adulto','36',  'Cintura 36"  (jeans/pantalón)', 14);

-- Tallas ropa niño (por edad/número mexicano)
INSERT INTO catalogo_tallas (tipo, codigo, descripcion, orden) VALUES
    ('ropa_nino','2',   '2 años  / Talla 2',   1),
    ('ropa_nino','4',   '4 años  / Talla 4',   2),
    ('ropa_nino','6',   '6 años  / Talla 6',   3),
    ('ropa_nino','8',   '8 años  / Talla 8',   4),
    ('ropa_nino','10',  '10 años / Talla 10',  5),
    ('ropa_nino','12',  '12 años / Talla 12',  6),
    ('ropa_nino','14',  '14 años / Talla 14',  7),
    ('ropa_nino','16',  '16 años / Talla 16',  8);

-- Calzado adulto (numeración mexicana)
INSERT INTO catalogo_tallas (tipo, codigo, descripcion, orden) VALUES
    ('calzado_adulto','22',  'Talla 22 MX / EU 34.5',  1),
    ('calzado_adulto','22.5','Talla 22.5',              2),
    ('calzado_adulto','23',  'Talla 23 MX / EU 35.5',  3),
    ('calzado_adulto','23.5','Talla 23.5',              4),
    ('calzado_adulto','24',  'Talla 24 MX / EU 36.5',  5),
    ('calzado_adulto','24.5','Talla 24.5',              6),
    ('calzado_adulto','25',  'Talla 25 MX / EU 38',    7),
    ('calzado_adulto','25.5','Talla 25.5',              8),
    ('calzado_adulto','26',  'Talla 26 MX / EU 39',    9),
    ('calzado_adulto','26.5','Talla 26.5',             10),
    ('calzado_adulto','27',  'Talla 27 MX / EU 40',   11),
    ('calzado_adulto','27.5','Talla 27.5',             12),
    ('calzado_adulto','28',  'Talla 28 MX / EU 41',   13),
    ('calzado_adulto','28.5','Talla 28.5',             14),
    ('calzado_adulto','29',  'Talla 29 MX / EU 42',   15),
    ('calzado_adulto','29.5','Talla 29.5',             16),
    ('calzado_adulto','30',  'Talla 30 MX / EU 44',   17);

-- Calzado niño
INSERT INTO catalogo_tallas (tipo, codigo, descripcion, orden) VALUES
    ('calzado_nino','12',  'Talla 12 (niño ~1 año)',  1),
    ('calzado_nino','13',  'Talla 13 (niño ~2 años)', 2),
    ('calzado_nino','14',  'Talla 14 (niño ~2-3 a)',  3),
    ('calzado_nino','15',  'Talla 15 (niño ~3 años)', 4),
    ('calzado_nino','16',  'Talla 16 (niño ~3-4 a)',  5),
    ('calzado_nino','17',  'Talla 17 (niño ~4 años)', 6),
    ('calzado_nino','18',  'Talla 18 (niño ~4-5 a)',  7),
    ('calzado_nino','19',  'Talla 19 (niño ~5 años)', 8),
    ('calzado_nino','20',  'Talla 20 (niño ~6 años)', 9),
    ('calzado_nino','21',  'Talla 21 (niño ~7 años)',10);

-- Calzado bebé
INSERT INTO catalogo_tallas (tipo, codigo, descripcion, orden) VALUES
    ('calzado_bebe','6',   '6 cm  — 0-3 meses',  1),
    ('calzado_bebe','7',   '7 cm  — 3-6 meses',  2),
    ('calzado_bebe','8',   '8 cm  — 6-9 meses',  3),
    ('calzado_bebe','9',   '9 cm  — 9-12 meses', 4),
    ('calzado_bebe','10',  '10 cm — 12-18 meses', 5),
    ('calzado_bebe','11',  '11 cm — 18-24 meses', 6);

-- Talla única
INSERT INTO catalogo_tallas (tipo, codigo, descripcion, orden) VALUES
    ('unica','UNICA', 'Talla única / Talla libre', 1);


-- ─────────────────────────────────────────────────────────
--  TABLA: productos  (catálogo principal)
-- ─────────────────────────────────────────────────────────
CREATE TABLE productos (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre          VARCHAR(200) NOT NULL,
    descripcion     TEXT,
    id_categoria    INTEGER NOT NULL REFERENCES categorias(id) ON UPDATE CASCADE,
    genero          genero_prod NOT NULL DEFAULT 'unisex',
    marca           VARCHAR(80),
    material        VARCHAR(150),
    precio_base     NUMERIC(10,2) NOT NULL CHECK(precio_base >= 0),
    precio_oferta   NUMERIC(10,2) CHECK(precio_oferta >= 0),
    sku_base        VARCHAR(40) UNIQUE,              -- código base del producto
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    destacado       BOOLEAN NOT NULL DEFAULT FALSE,
    nuevo           BOOLEAN NOT NULL DEFAULT TRUE,
    meta_titulo     VARCHAR(200),                    -- SEO
    meta_descripcion VARCHAR(400),                   -- SEO
    vistas          INTEGER NOT NULL DEFAULT 0,
    ventas_total    INTEGER NOT NULL DEFAULT 0,
    calificacion    NUMERIC(3,2) DEFAULT 0.00,       -- promedio 1-5
    num_resenas     INTEGER NOT NULL DEFAULT 0,
    creado_por      UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_prod_categoria ON productos(id_categoria);
CREATE INDEX idx_prod_activo    ON productos(activo);
CREATE INDEX idx_prod_destacado ON productos(destacado);
CREATE INDEX idx_prod_genero    ON productos(genero);
CREATE INDEX idx_prod_nombre    ON productos USING gin(to_tsvector('spanish', nombre));

-- Productos de ejemplo
INSERT INTO productos (nombre, descripcion, id_categoria, genero, precio_base, precio_oferta, sku_base, activo, destacado, nuevo) VALUES
    ('Blusa floral primavera',   'Blusa ligera algodón 100%, estampado floral multicolor',         1, 'mujer',   389.00, 280.00, 'KUK-BLU-001', TRUE, TRUE,  TRUE),
    ('Vestido midi elegante',    'Vestido de corte midi, tela satinada, ideal para eventos',        1, 'mujer',   780.00,   NULL, 'KUK-VES-001', TRUE, TRUE,  FALSE),
    ('Camisa slim fit Oxford',   'Camisa de algodón Oxford, corte moderno, varios colores',         2, 'hombre',  450.00,   NULL, 'KUK-CAM-001', TRUE, FALSE, TRUE),
    ('Jeans skinny premium',     'Denim de alta calidad con 2% elastano, muy cómodos',             2, 'hombre',  695.00, 550.00, 'KUK-JNS-001', TRUE, TRUE,  FALSE),
    ('Conjunto niña flores',     'Set de playera y falda con motivos florales, lavable',            3, 'nina',    320.00,   NULL, 'KUK-CON-001', TRUE, FALSE, TRUE),
    ('Playera deportiva niño',   'Tela DryFit transpirable, ideal para actividades',               4, 'nino',    195.00,   NULL, 'KUK-PLY-001', TRUE, FALSE, TRUE),
    ('Pijama bebé algodón',      'Pijama suave algodón orgánico, sin costuras internas',           5, 'bebe',    280.00,   NULL, 'KUK-PIJ-001', TRUE, FALSE, TRUE),
    ('Bolsa tote cuero sint.',   'Bolsa elegante cuero sintético, compartimento laptop 13"',       6, 'mujer',   580.00, 420.00, 'KUK-BOL-001', TRUE, TRUE,  FALSE),
    ('Zapatillas tenis moda',    'Suela de goma, puntera reforzada, plantilla anatómica',          7, 'mujer',   890.00, 720.00, 'KUK-ZAP-001', TRUE, TRUE,  TRUE),
    ('Tacones fiesta dorados',   'Tacón de aguja 7cm, punta cerrada, tela brillante dorada',       7, 'mujer',   650.00,   NULL, 'KUK-TAC-001', TRUE, FALSE, TRUE),
    ('Tenis urbanos hombre',     'Tenis casuales suela vulcanizada, varios colores',               8, 'hombre',  750.00, 620.00, 'KUK-TEN-001', TRUE, TRUE,  TRUE),
    ('Pants jogger hombre',      'Pants deportivo tela French Terry, bolsillos con cierre',        10,'hombre',  355.00,   NULL, 'KUK-PAN-001', TRUE, FALSE, TRUE),
    ('Blusa plus size floral',   'Blusa tallas grandes, misma calidad y estilo',                  11,'mujer',   420.00,   NULL, 'KUK-BPS-001', TRUE, FALSE, TRUE);


-- ─────────────────────────────────────────────────────────
--  TABLA: producto_variantes
--  La pieza clave: cada combinación talla+color tiene su propio stock y SKU
-- ─────────────────────────────────────────────────────────
CREATE TABLE producto_variantes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_producto     UUID NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    id_talla        INTEGER NOT NULL REFERENCES catalogo_tallas(id),
    color           VARCHAR(50),          -- "Rosa chicle", "Azul marino"
    color_hex       CHAR(7),              -- "#FF6B9E" para mostrar en UI
    sku_variante    VARCHAR(60) UNIQUE,   -- "KUK-BLU-001-M-ROSA"
    stock           SMALLINT NOT NULL DEFAULT 0 CHECK(stock >= 0),
    stock_minimo    SMALLINT NOT NULL DEFAULT 2,  -- alerta de bajo stock
    precio_extra    NUMERIC(8,2) DEFAULT 0.00,    -- sobrecargo por talla grande
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE(id_producto, id_talla, color)          -- no duplicados
);

CREATE INDEX idx_variante_producto ON producto_variantes(id_producto);
CREATE INDEX idx_variante_talla    ON producto_variantes(id_talla);
CREATE INDEX idx_variante_stock    ON producto_variantes(stock);

-- Variantes de ejemplo: Blusa floral (tallas S, M, L en rosa y blanco)
WITH blusa AS (SELECT id FROM productos WHERE sku_base = 'KUK-BLU-001'),
     t_s   AS (SELECT id FROM catalogo_tallas WHERE tipo='ropa_adulto' AND codigo='S'),
     t_m   AS (SELECT id FROM catalogo_tallas WHERE tipo='ropa_adulto' AND codigo='M'),
     t_l   AS (SELECT id FROM catalogo_tallas WHERE tipo='ropa_adulto' AND codigo='L'),
     t_xl  AS (SELECT id FROM catalogo_tallas WHERE tipo='ropa_adulto' AND codigo='XL')
INSERT INTO producto_variantes (id_producto, id_talla, color, color_hex, sku_variante, stock) VALUES
    ((SELECT id FROM blusa),(SELECT id FROM t_s), 'Rosa',   '#F48FB1','KUK-BLU-001-S-ROSA',  8),
    ((SELECT id FROM blusa),(SELECT id FROM t_s), 'Blanco', '#FFFFFF', 'KUK-BLU-001-S-BCO',  6),
    ((SELECT id FROM blusa),(SELECT id FROM t_m), 'Rosa',   '#F48FB1','KUK-BLU-001-M-ROSA', 12),
    ((SELECT id FROM blusa),(SELECT id FROM t_m), 'Blanco', '#FFFFFF', 'KUK-BLU-001-M-BCO',  9),
    ((SELECT id FROM blusa),(SELECT id FROM t_l), 'Rosa',   '#F48FB1','KUK-BLU-001-L-ROSA',  5),
    ((SELECT id FROM blusa),(SELECT id FROM t_xl),'Rosa',   '#F48FB1','KUK-BLU-001-XL-ROSA', 3);


-- ─────────────────────────────────────────────────────────
--  TABLA: imagenes_producto
-- ─────────────────────────────────────────────────────────
CREATE TABLE imagenes_producto (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_producto   UUID NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    id_variante   UUID REFERENCES producto_variantes(id) ON DELETE CASCADE, -- NULL = imagen general
    url           TEXT NOT NULL,
    url_thumb     TEXT,          -- versión miniatura (Cloudinary lo genera automático)
    alt_text      VARCHAR(200),
    es_principal  BOOLEAN NOT NULL DEFAULT FALSE,
    orden         SMALLINT NOT NULL DEFAULT 0,
    creado_en     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_img_producto  ON imagenes_producto(id_producto);
CREATE INDEX idx_img_principal ON imagenes_producto(es_principal);


-- ─────────────────────────────────────────────────────────
--  TABLA: pedidos
-- ─────────────────────────────────────────────────────────
CREATE TABLE pedidos (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    numero_pedido   VARCHAR(25) NOT NULL UNIQUE,  -- KUK-20250611-0001
    id_usuario      UUID NOT NULL REFERENCES usuarios(id),
    estado          estado_pedido NOT NULL DEFAULT 'pendiente',
    subtotal        NUMERIC(10,2) NOT NULL CHECK(subtotal >= 0),
    descuento       NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    iva             NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    costo_envio     NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    total           NUMERIC(10,2) NOT NULL CHECK(total >= 0),
    metodo_pago     metodo_pago NOT NULL,
    referencia_pago VARCHAR(120),    -- ID de transacción PayPal / Stripe
    codigo_cupon    VARCHAR(30),
    notas_cliente   TEXT,
    notas_internas  TEXT,
    ip_cliente      INET,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    pagado_en       TIMESTAMPTZ,
    enviado_en      TIMESTAMPTZ,
    entregado_en    TIMESTAMPTZ,
    actualizado_en  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pedido_usuario ON pedidos(id_usuario);
CREATE INDEX idx_pedido_estado  ON pedidos(estado);
CREATE INDEX idx_pedido_fecha   ON pedidos(creado_en DESC);

-- Auto-generar número de pedido
CREATE OR REPLACE FUNCTION generar_numero_pedido()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    contador INTEGER;
BEGIN
    SELECT COUNT(*) + 1 INTO contador FROM pedidos
    WHERE DATE_TRUNC('day', creado_en) = DATE_TRUNC('day', NOW());
    NEW.numero_pedido := 'KUK-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(contador::TEXT, 4, '0');
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_numero_pedido
    BEFORE INSERT ON pedidos
    FOR EACH ROW WHEN (NEW.numero_pedido IS NULL OR NEW.numero_pedido = '')
    EXECUTE FUNCTION generar_numero_pedido();


-- ─────────────────────────────────────────────────────────
--  TABLA: detalle_pedido
-- ─────────────────────────────────────────────────────────
CREATE TABLE detalle_pedido (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_pedido       UUID NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    id_variante     UUID NOT NULL REFERENCES producto_variantes(id),
    nombre_producto VARCHAR(200) NOT NULL,  -- snapshot del nombre al comprar
    talla           VARCHAR(10)  NOT NULL,  -- snapshot de talla al comprar
    color           VARCHAR(50),            -- snapshot de color
    sku             VARCHAR(60),
    cantidad        SMALLINT NOT NULL CHECK(cantidad > 0),
    precio_unit     NUMERIC(10,2) NOT NULL,
    subtotal        NUMERIC(10,2) GENERATED ALWAYS AS (cantidad * precio_unit) STORED
);

CREATE INDEX idx_detalle_pedido   ON detalle_pedido(id_pedido);
CREATE INDEX idx_detalle_variante ON detalle_pedido(id_variante);

-- Trigger: descontar stock al confirmar pedido
CREATE OR REPLACE FUNCTION descontar_stock()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    UPDATE producto_variantes
    SET stock = stock - NEW.cantidad
    WHERE id = NEW.id_variante;

    IF (SELECT stock FROM producto_variantes WHERE id = NEW.id_variante) < 0 THEN
        RAISE EXCEPTION 'Stock insuficiente para variante %', NEW.id_variante;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_descontar_stock
    AFTER INSERT ON detalle_pedido
    FOR EACH ROW
    EXECUTE FUNCTION descontar_stock();

-- Trigger: reponer stock si se cancela pedido
CREATE OR REPLACE FUNCTION reponer_stock()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.estado IN ('cancelado','devuelto') AND OLD.estado NOT IN ('cancelado','devuelto') THEN
        UPDATE producto_variantes pv
        SET stock = stock + dp.cantidad
        FROM detalle_pedido dp
        WHERE dp.id_pedido = NEW.id AND dp.id_variante = pv.id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_reponer_stock
    AFTER UPDATE ON pedidos
    FOR EACH ROW
    EXECUTE FUNCTION reponer_stock();


-- ─────────────────────────────────────────────────────────
--  TABLA: direcciones_envio
-- ─────────────────────────────────────────────────────────
CREATE TABLE direcciones_envio (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_pedido       UUID NOT NULL UNIQUE REFERENCES pedidos(id) ON DELETE CASCADE,
    nombre_dest     VARCHAR(150) NOT NULL,
    calle           VARCHAR(200) NOT NULL,
    numero_ext      VARCHAR(20),
    numero_int      VARCHAR(20),
    colonia         VARCHAR(100),
    ciudad          VARCHAR(100) NOT NULL,
    estado_rep      VARCHAR(80)  NOT NULL,
    cp              VARCHAR(10)  NOT NULL,
    pais            VARCHAR(60)  NOT NULL DEFAULT 'México',
    telefono        VARCHAR(20),
    referencias     TEXT,        -- "Entre calle Roble y Encino, portón azul"
    guia_envio      VARCHAR(80), -- número de rastreo de paquetería
    paqueteria      VARCHAR(60)  -- "FedEx", "DHL", "Estafeta", "Correos MX"
);


-- ─────────────────────────────────────────────────────────
--  TABLA: direcciones_usuario  (libreta de direcciones)
-- ─────────────────────────────────────────────────────────
CREATE TABLE direcciones_usuario (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_usuario      UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    alias           VARCHAR(60) DEFAULT 'Mi domicilio',  -- "Casa", "Trabajo"
    calle           VARCHAR(200) NOT NULL,
    numero_ext      VARCHAR(20),
    numero_int      VARCHAR(20),
    colonia         VARCHAR(100),
    ciudad          VARCHAR(100) NOT NULL,
    estado_rep      VARCHAR(80)  NOT NULL,
    cp              VARCHAR(10)  NOT NULL,
    telefono        VARCHAR(20),
    es_principal    BOOLEAN NOT NULL DEFAULT FALSE,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dir_usuario ON direcciones_usuario(id_usuario);


-- ─────────────────────────────────────────────────────────
--  TABLA: cupones_descuento
-- ─────────────────────────────────────────────────────────
CREATE TABLE cupones (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(30) NOT NULL UNIQUE,
    descripcion     VARCHAR(150),
    tipo            VARCHAR(20) NOT NULL DEFAULT 'porcentaje', -- 'porcentaje' | 'fijo'
    valor           NUMERIC(8,2) NOT NULL,   -- 15.00 = 15% o $15 fijo
    minimo_compra   NUMERIC(10,2) DEFAULT 0.00,
    usos_maximos    INTEGER,                 -- NULL = ilimitado
    usos_actuales   INTEGER NOT NULL DEFAULT 0,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_inicio    DATE,
    fecha_fin       DATE,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO cupones (codigo, descripcion, tipo, valor, minimo_compra) VALUES
    ('KUKIS10', 'Descuento 10% primera compra', 'porcentaje', 10.00, 300.00),
    ('ENVIOGRATIS', 'Envío gratis en tu pedido', 'fijo', 99.00, 500.00);


-- ─────────────────────────────────────────────────────────
--  TABLA: reseñas / calificaciones
-- ─────────────────────────────────────────────────────────
CREATE TABLE resenas (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_producto     UUID NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    id_usuario      UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    id_pedido       UUID REFERENCES pedidos(id),    -- solo pueden reseñar si compraron
    calificacion    SMALLINT NOT NULL CHECK(calificacion BETWEEN 1 AND 5),
    titulo          VARCHAR(100),
    comentario      TEXT,
    aprobada        BOOLEAN NOT NULL DEFAULT FALSE, -- moderación
    util_count      INTEGER NOT NULL DEFAULT 0,     -- "¿Fue útil?"
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(id_producto, id_usuario)
);

CREATE INDEX idx_resena_producto ON resenas(id_producto);
CREATE INDEX idx_resena_aprobada ON resenas(aprobada);

-- Trigger: actualizar calificación promedio del producto
CREATE OR REPLACE FUNCTION actualizar_calificacion()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    UPDATE productos SET
        calificacion = (SELECT AVG(calificacion) FROM resenas WHERE id_producto = NEW.id_producto AND aprobada = TRUE),
        num_resenas  = (SELECT COUNT(*)           FROM resenas WHERE id_producto = NEW.id_producto AND aprobada = TRUE)
    WHERE id = NEW.id_producto;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_calificacion
    AFTER INSERT OR UPDATE ON resenas
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_calificacion();


-- ─────────────────────────────────────────────────────────
--  TABLA: favoritos  (wishlist)
-- ─────────────────────────────────────────────────────────
CREATE TABLE favoritos (
    id_usuario      UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    id_producto     UUID NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    agregado_en     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id_usuario, id_producto)
);


-- ─────────────────────────────────────────────────────────
--  TABLA: carrito_persistente  (guardar carrito aunque cierre el navegador)
-- ─────────────────────────────────────────────────────────
CREATE TABLE carrito (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_usuario      UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    id_variante     UUID NOT NULL REFERENCES producto_variantes(id) ON DELETE CASCADE,
    cantidad        SMALLINT NOT NULL DEFAULT 1 CHECK(cantidad > 0),
    agregado_en     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(id_usuario, id_variante)
);

CREATE INDEX idx_carrito_usuario ON carrito(id_usuario);


-- ─────────────────────────────────────────────────────────
--  TABLA: sesiones  (tokens JWT refresh / sesiones activas)
-- ─────────────────────────────────────────────────────────
CREATE TABLE sesiones (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_usuario      UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token_refresh   VARCHAR(200) NOT NULL UNIQUE,
    ip              INET,
    agente          TEXT,        -- User-Agent del navegador
    activa          BOOLEAN NOT NULL DEFAULT TRUE,
    expira_en       TIMESTAMPTZ NOT NULL,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sesion_usuario ON sesiones(id_usuario);
CREATE INDEX idx_sesion_token   ON sesiones(token_refresh);


-- ─────────────────────────────────────────────────────────
--  TABLA: log_auditoria  (todo queda registrado)
-- ─────────────────────────────────────────────────────────
CREATE TABLE log_auditoria (
    id              BIGSERIAL PRIMARY KEY,
    id_usuario      UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    accion          VARCHAR(80) NOT NULL,    -- 'login','logout','crear_producto','eliminar_pedido'
    tabla_afectada  VARCHAR(60),
    registro_id     TEXT,                   -- UUID del registro modificado
    datos_antes     JSONB,                  -- snapshot antes del cambio
    datos_despues   JSONB,                  -- snapshot después
    ip              INET,
    resultado       VARCHAR(20) DEFAULT 'ok', -- 'ok' | 'error'
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_log_usuario ON log_auditoria(id_usuario);
CREATE INDEX idx_log_accion  ON log_auditoria(accion);
CREATE INDEX idx_log_fecha   ON log_auditoria(creado_en DESC);


-- ─────────────────────────────────────────────────────────
--  VISTAS DE CONSULTA RÁPIDA
-- ─────────────────────────────────────────────────────────

-- Vista: productos con stock total y precio final
CREATE VIEW v_productos_completo AS
SELECT
    p.id,
    p.nombre,
    p.descripcion,
    c.nombre                                AS categoria,
    p.genero,
    p.precio_base,
    COALESCE(p.precio_oferta, p.precio_base) AS precio_final,
    CASE WHEN p.precio_oferta IS NOT NULL
         THEN ROUND((1 - p.precio_oferta/p.precio_base)*100)::INT
         ELSE 0 END                          AS descuento_pct,
    COALESCE(SUM(pv.stock), 0)              AS stock_total,
    COUNT(DISTINCT pv.id)                   AS num_variantes,
    p.destacado,
    p.nuevo,
    p.calificacion,
    p.num_resenas,
    p.activo
FROM productos p
JOIN categorias c ON c.id = p.id_categoria
LEFT JOIN producto_variantes pv ON pv.id_producto = p.id AND pv.activo = TRUE
GROUP BY p.id, c.nombre;

-- Vista: detalle de variantes con nombre de talla
CREATE VIEW v_variantes_detalle AS
SELECT
    pv.id,
    pv.id_producto,
    p.nombre                                AS producto,
    ct.tipo                                 AS tipo_talla,
    ct.codigo                               AS talla,
    ct.descripcion                          AS talla_descripcion,
    pv.color,
    pv.color_hex,
    pv.sku_variante,
    pv.stock,
    pv.stock_minimo,
    CASE WHEN pv.stock <= pv.stock_minimo
         THEN TRUE ELSE FALSE END           AS bajo_stock,
    p.precio_base + COALESCE(pv.precio_extra,0) AS precio_final
FROM producto_variantes pv
JOIN productos p ON p.id = pv.id_producto
JOIN catalogo_tallas ct ON ct.id = pv.id_talla;

-- Vista: resumen ventas por categoría
CREATE VIEW v_ventas_categoria AS
SELECT
    c.nombre                    AS categoria,
    COUNT(DISTINCT p.id_pedido) AS pedidos,
    SUM(p.cantidad)             AS unidades,
    SUM(p.subtotal)             AS ingresos
FROM detalle_pedido p
JOIN producto_variantes pv ON pv.id = p.id_variante
JOIN productos pr ON pr.id = pv.id_producto
JOIN categorias c  ON c.id  = pr.id_categoria
GROUP BY c.nombre
ORDER BY ingresos DESC;

-- Vista: alertas de bajo stock
CREATE VIEW v_alerta_stock AS
SELECT
    pv.sku_variante,
    pr.nombre   AS producto,
    ct.codigo   AS talla,
    pv.color,
    pv.stock,
    pv.stock_minimo
FROM producto_variantes pv
JOIN productos pr      ON pr.id = pv.id_producto
JOIN catalogo_tallas ct ON ct.id = pv.id_talla
WHERE pv.stock <= pv.stock_minimo AND pv.activo = TRUE
ORDER BY pv.stock ASC;
