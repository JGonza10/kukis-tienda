# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es esto

Tienda en línea de "apartados" (reservaciones) para una vendedora de tianguis que solo vende los domingos. Las clientas ven el catálogo, apartan una prenda (talla + color) dejando nombre y teléfono, y pagan/recogen en persona el domingo. La vendedora administra inventario, sube fotos y gestiona apartados desde un panel propio (`/admin`). No hay pagos en línea ni carrito de compras — es solo reservación.

Backend Flask + SQLAlchemy (`backend/`), frontend React + Vite (`frontend/`). Todo el código, comentarios y mensajes están en español.

## Comandos

**Backend** (`backend/`):
```bash
cd backend
python -m venv venv && venv\Scripts\activate      # Windows; source venv/bin/activate en Linux/macOS
pip install -r requirements.txt
cp .env.example .env
python app.py                    # dev server en http://localhost:5000, crea kukis.db y usuario "vendedora"
python seed_demo.py              # opcional: carga 3 prendas de ejemplo
```
`requirements-postgres.txt` (con `psycopg2-binary`) es aparte de `requirements.txt` porque suele fallar al compilar en Windows y solo hace falta para desplegar con PostgreSQL — instálalo solo al desplegar, no en desarrollo local.

**Frontend** (`frontend/`):
```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173, proxy a /api y /uploads hacia el backend
npm run build                    # build de producción a frontend/dist
```

No hay tests ni linter configurados en ninguno de los dos lados.

## Arquitectura

**Un solo servicio en producción, dos procesos en desarrollo.** En Railway, `backend/app.py` sirve la API (`/api/...`), las imágenes subidas (`/uploads/...`) y el build de React (`frontend/dist`) desde el mismo proceso Flask (ver el bloque `if os.path.isdir(FRONTEND_DIST)` en `create_app()`). En desarrollo local corren dos procesos separados (Flask en 5000, Vite en 5173) y Vite hace proxy de `/api` y `/uploads` al backend.

**Modelo de datos** (`backend/models.py`): `Usuario` (una sola cuenta, la vendedora) → `Producto` → `Variante` (talla+color+stock, es la unidad real de inventario) → `Apartado` (reservación de una variante específica, con `cliente_nombre`/`cliente_telefono`, estado `pendiente|confirmado|entregado|cancelado`, y `fecha_entrega` que por defecto es el próximo domingo). `Imagen` cuelga de `Producto`.

- **Disponibilidad vs. stock físico son cosas distintas.** `Variante.disponible()` resta del `stock` los apartados con estado `pendiente`/`confirmado` (`apartados_activos()`) — es lo que se le muestra a una clienta nueva. `stock` en sí solo se decrementa cuando un apartado pasa a `entregado` (y se restaura si se revierte desde `entregado`), en `routes/admin.py::actualizar_apartado`. Si tocas la lógica de estados de apartado, respeta esta separación: no confundas "comprometido" con "ya entregado físicamente".
- **Horario de negocio** (`backend/horario.py`): todo el sistema (crear apartados y todo el panel `/api/admin/*` salvo el login) solo opera 9:00–22:00 hora de Ciudad de México (`ZoneInfo("America/Mexico_City")`, para que el horario tenga sentido sin importar la zona del servidor). Se aplica con un `before_request` en el blueprint admin y una verificación explícita en `crear_apartado`. El catálogo público (`GET /api/productos`) sí funciona fuera de horario; solo se bloquean las acciones de escritura.
- **Auth**: sesión de Flask (cookie, `SESSION_COOKIE_SAMESITE=Lax`, 7 días), una sola cuenta (`Usuario`), sin roles ni registro — no está pensado para múltiples administradoras. `login_requerido` en `auth.py` protege las rutas del blueprint admin.
- **Imágenes**: subida a `backend/uploads/` con nombre único (`uuid4().hex + nombre_seguro`), servidas por la propia ruta `/uploads/<archivo>`. En Railway ese directorio se borra en cada deploy — el propio README ya lo marca como pendiente de mover a almacenamiento externo (Cloudinary/S3) antes de producción real.
- **`SECRET_KEY`, `PASSWORD_INICIAL` y `DATABASE_URL`** vienen de variables de entorno (`.env`, ver `backend/.env.example`); en local caen a defaults inseguros (`"cambia-esto-en-produccion"`, `kukis2026`, SQLite local) — no asumas que esos defaults son válidos para producción.
