# Kukis · tienda en línea con apartados

Tienda en línea para una vendedora de tianguis (solo vende los domingos en un horarios de 9 a 15:30).
Las clientas ven el catálogo, apartan una prenda (talla y color) dejando su
nombre y teléfono, y pagan/recogen en persona el domingo. La vendedora
administra su inventario, sube fotos y gestiona los apartados desde un panel
con su propio login. Todo el sistema (catálogo, apartados y panel) opera solo
de 9:00 a 22:00, todos los días.

Funciona en escritorio y en móvil (diseño responsive).

## Estructura

```
07 Tienda en Linea Kukis/
├── backend/     Flask + SQLAlchemy (API + panel de administración)
└── frontend/    React + Vite (catálogo público y panel de la vendedora)
```

## Correr en tu computadora

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # en Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Esto crea la base de datos (SQLite por default), un usuario inicial
`vendedora` / `kukis2026` (cámbialo apenas entres), y deja la API corriendo
en `http://localhost:5000`.

Para cargar 3 prendas de ejemplo y probar el catálogo:

```bash
python seed_demo.py
```

### 2. Frontend

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5180`. El catálogo es público; el panel de la
vendedora está en `/admin`.

## Cómo funciona el horario

El sistema (apartar una prenda y el panel de la vendedora) solo funciona de
9:00 a 22:00, todos los días, hora de Ciudad de México. Fuera de ese horario
el catálogo se puede seguir viendo, pero no se pueden hacer ni confirmar
apartados. Esto se controla en `backend/horario.py`.

## Aviso por Telegram de apartados nuevos

Es opcional. Si `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` están vacíos en el
`.env`, el sistema simplemente no manda ningún aviso (y los apartados se
siguen creando normal). Para activarlo:

1. En Telegram, habla con **@BotFather**, manda `/newbot` y sigue los pasos.
   Al final te da un token — cópialo en `TELEGRAM_BOT_TOKEN`.
2. Mándale cualquier mensaje a tu bot recién creado (para que Telegram sepa
   que puede escribirte).
3. Entra en el navegador a
   `https://api.telegram.org/bot<TU_TOKEN>/getUpdates` y busca el número en
   `"chat":{"id": ...}` — ese es tu `TELEGRAM_CHAT_ID`. También puedes
   obtenerlo hablando con **@userinfobot**.

## Contacto configurado

- WhatsApp: 55 2417 7160 (enlace `wa.me` en el pie de página y junto a cada
  apartado en el panel, para escribirle directo a la clienta)
- Instagram: @kukis

## Antes de publicarla en internet

1. Cambia la contraseña del usuario `vendedora` (créala de nuevo con
   `PASSWORD_INICIAL` en el `.env`, o agrega un endpoint de cambio de
   contraseña más adelante).
2. Cambia `SECRET_KEY` en el `.env` por algo largo y aleatorio.
3. Las fotos que suba la vendedora se guardan en `backend/uploads/` — en
   Railway eso se borra en cada deploy, así que para producción conviene
   moverlas a un almacenamiento externo (por ejemplo Cloudinary o un bucket
   S3). Mientras tanto funciona para pruebas.
4. Para desplegar en Railway con base de datos PostgreSQL, usa la skill
   `web-deploy-db` — este backend ya lee `DATABASE_URL` y sirve el build de
   React (`frontend/dist`) desde el mismo servicio, así que basta con un solo
   servicio de Railway. Antes de desplegar, instala también
   `pip install -r requirements-postgres.txt` (ese paquete no está en el
   `requirements.txt` normal porque en Windows suele fallar al compilar y no
   se necesita para desarrollar en local con SQLite).

## Problemas comunes

- **"Ocurrió un error inesperado" al iniciar sesión en el panel:** casi
  siempre significa que el navegador no pudo llegar al backend en JSON.
  Revisa que tengas las dos terminales corriendo al mismo tiempo (`python
  app.py` en una y `npm run dev` en otra) y entra a `http://localhost:5000/api/health`
  directo en el navegador — debe mostrar `{"ok": true, ...}`. Si no carga,
  el backend no está corriendo o truena al iniciar.
- **`pip install` truena en `psycopg2-binary`:** ese paquete se movió a
  `requirements-postgres.txt` porque solo se necesita para desplegar con
  PostgreSQL, no para desarrollar en local. Con el `requirements.txt` actual
  ya no debería intentar instalarlo.
