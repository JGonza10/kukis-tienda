# KUKIS MODA Y ESTILO — Guía de despliegue completo
# Stack: FastAPI + PostgreSQL (Supabase) + Netlify
# Tiempo estimado: 45-60 minutos

## ══════════════════════════════════════════════
##  PASO 0 — Estructura final del proyecto
## ══════════════════════════════════════════════

kukis_v2/
├── frontend/
│   └── index.html          ← La tienda completa
├── backend/
│   ├── main.py             ← API FastAPI
│   ├── requirements.txt    ← Dependencias Python
│   ├── Procfile            ← Arranque en Render
│   └── .env.example        ← Variables de entorno (plantilla)
└── db/
    └── schema.sql          ← Base de datos PostgreSQL completa


## ══════════════════════════════════════════════
##  PASO 1 — BASE DE DATOS en Supabase (GRATIS)
## ══════════════════════════════════════════════

1. Ve a https://supabase.com y crea cuenta gratis (con tu Gmail)

2. Haz clic en "New project":
   - Organization: Personal
   - Name: kukis-tienda
   - Database Password: (guárdala, la necesitarás)
   - Region: South America (São Paulo)  ← más cerca de México
   - Plan: Free

3. Espera ~2 minutos a que se cree el proyecto

4. Ejecutar el schema.sql:
   - En el panel de Supabase: menú izquierdo → "SQL Editor"
   - Haz clic en "New query"
   - Copia y pega el contenido de db/schema.sql
   - Haz clic en "RUN" (o Ctrl+Enter)
   - Deberías ver: "Success. No rows returned"

5. Obtener la URL de conexión:
   - Menú izquierdo → "Settings" → "Database"
   - Sección "Connection string" → pestaña "URI"
   - Copia la cadena que empieza con: postgresql://postgres:...
   - GUÁRDALA — la usarás en el Paso 2

   Ejemplo: postgresql://postgres:TuPassword@db.abcdefgh.supabase.co:5432/postgres

6. Verificar tablas creadas:
   - Menú izquierdo → "Table Editor"
   - Debes ver: usuarios, productos, producto_variantes, pedidos, etc.


## ══════════════════════════════════════════════
##  PASO 2 — API en Render.com (GRATIS)
## ══════════════════════════════════════════════

### 2a. Preparar GitHub (necesario para Render)

1. Ve a https://github.com y crea cuenta (si no tienes)

2. Crea repositorio nuevo:
   - Nombre: kukis-api
   - Visibilidad: Private  ← importante, no public
   - NO inicialices con README

3. En tu computadora, instala Git si no lo tienes:
   https://git-scm.com/download/win

4. Sube el backend a GitHub:

   Abre CMD o PowerShell en la carpeta kukis_v2/backend/ y ejecuta:

   git init
   git add .
   git commit -m "Kukis API v2 inicial"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/kukis-api.git
   git push -u origin main

### 2b. Crear servicio en Render

1. Ve a https://render.com y crea cuenta (con GitHub)

2. Dashboard → "New +" → "Web Service"

3. Conecta tu repositorio kukis-api

4. Configuración del servicio:
   - Name: kukis-api
   - Region: Ohio (US East)
   - Branch: main
   - Runtime: Python 3
   - Build Command: pip install -r requirements.txt
   - Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   - Instance Type: Free

5. Agregar variables de entorno (sección "Environment"):
   Haz clic en "Add Environment Variable" para cada una:

   DATABASE_URL  = postgresql://postgres:TuPass@db.xxxxx.supabase.co:5432/postgres
   JWT_SECRET    = (genera con: python -c "import secrets; print(secrets.token_hex(32))")
   JWT_EXPIRE_HOURS = 24
   CORS_ORIGINS  = http://localhost,https://TU-SITIO.netlify.app

6. Haz clic en "Create Web Service"
   → Render instala dependencias y arranca la API (~3-5 min)

7. Tu API quedará en: https://kukis-api.onrender.com
   Prueba: https://kukis-api.onrender.com/health
   Docs:   https://kukis-api.onrender.com/docs

   ⚠️ NOTA: En el plan gratuito de Render, la API "duerme" después
   de 15 min sin tráfico. El primer request tarda ~30 seg en despertar.
   Para producción real, considera el plan Starter ($7/mes).


## ══════════════════════════════════════════════
##  PASO 3 — FRONTEND en Netlify (GRATIS)
## ══════════════════════════════════════════════

### Opción A — Arrastrar y soltar (más fácil, 2 minutos)

1. Ve a https://netlify.com y crea cuenta (con Gmail o GitHub)

2. En el Dashboard, busca la zona que dice:
   "Want to deploy a new site without connecting to Git?
    Drag and drop your site output folder here"

3. Arrastra la CARPETA frontend/ completa a esa zona

4. ¡Listo! Netlify te dará una URL como:
   https://radiant-cookie-abc123.netlify.app

5. Para cambiar el nombre:
   Site settings → General → Site details → Change site name
   Ejemplo: kukis-moda  →  https://kukis-moda.netlify.app

### Opción B — Con GitHub (deploy automático en cada cambio)

1. Crea otro repo: kukis-frontend
2. Sube la carpeta frontend/
3. En Netlify: "New site from Git" → selecciona el repo
4. Build command: (vacío)
5. Publish directory: .
6. Deploy site


## ══════════════════════════════════════════════
##  PASO 4 — CONECTAR FRONTEND CON LA API
## ══════════════════════════════════════════════

Una vez que tengas la URL de tu API de Render:

1. Abre la tienda en el navegador
2. Ve al menú Admin → Configuración
3. En el campo "URL de la API" escribe:
   https://kukis-api.onrender.com
4. Haz clic en "Guardar"

O edita directamente en index.html:
   Línea: const API_URL = 'https://kukis-api.onrender.com';

También actualiza CORS_ORIGINS en Render con tu URL de Netlify.


## ══════════════════════════════════════════════
##  PASO 5 — GENERAR HASH PARA EL ADMIN
## ══════════════════════════════════════════════

Antes de usar el panel admin, genera el hash real de tu contraseña:

1. Instala Python si no lo tienes: https://python.org
2. Abre CMD y ejecuta:

   pip install bcrypt
   python -c "import bcrypt; print(bcrypt.hashpw(b'TuPassword', bcrypt.gensalt(12)).decode())"

3. Copia el hash generado (empieza con $2b$12$...)

4. En Supabase → SQL Editor, ejecuta:

   UPDATE usuarios
   SET contrasena_hash = '$2b$12$TU_HASH_AQUI'
   WHERE email = 'juangonzamen10@gmail.com';


## ══════════════════════════════════════════════
##  PASO 6 — IMÁGENES con Cloudinary (GRATIS)
## ══════════════════════════════════════════════

Para subir imágenes reales de productos:

1. Crea cuenta gratis en https://cloudinary.com
   (25GB gratis, más que suficiente para comenzar)

2. Ve a Dashboard → copia:
   - Cloud Name
   - API Key
   - API Secret

3. En Render → Environment, agrega:
   CLOUDINARY_CLOUD_NAME = tu_cloud_name
   CLOUDINARY_API_KEY    = tu_api_key
   CLOUDINARY_API_SECRET = tu_api_secret

4. El endpoint POST /admin/productos aceptará imágenes
   y las subirá automáticamente a Cloudinary


## ══════════════════════════════════════════════
##  RESUMEN DE URLS FINALES
## ══════════════════════════════════════════════

Servicio          URL                                     Costo
────────────────────────────────────────────────────────────────
Tienda web        https://kukis-moda.netlify.app          GRATIS
API REST          https://kukis-api.onrender.com          GRATIS
Base de datos     Supabase (PostgreSQL)                   GRATIS
Imágenes          Cloudinary (25 GB)                      GRATIS
────────────────────────────────────────────────────────────────
TOTAL MENSUAL:                                            $0.00


## ══════════════════════════════════════════════
##  COMANDOS DE PRUEBA (postman / curl)
## ══════════════════════════════════════════════

# Health check
curl https://kukis-api.onrender.com/health

# Listar productos
curl https://kukis-api.onrender.com/productos

# Login admin
curl -X POST https://kukis-api.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"juangonzamen10@gmail.com","password":"TuPassword"}'

# Dashboard admin (necesitas el token del login)
curl https://kukis-api.onrender.com/admin/dashboard \
  -H "Authorization: Bearer TU_TOKEN_JWT"

# Docs interactivos de la API
Abre en tu navegador: https://kukis-api.onrender.com/docs


## ══════════════════════════════════════════════
##  MEJORAS FUTURAS (roadmap)
## ══════════════════════════════════════════════

v2.1 — Integración PayPal real (SDK JavaScript)
v2.2 — Notificaciones por email (SendGrid gratis 100/día)
v2.3 — WhatsApp Business API (Twilio sandbox gratis)
v2.4 — Panel admin subida de imágenes a Cloudinary
v2.5 — Google Analytics + Meta Pixel
v2.6 — Sistema de cupones activo
v2.7 — Reseñas de compradores verificados
v2.8 — App móvil con PWA (Progressive Web App)
