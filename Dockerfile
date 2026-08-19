# Imagen única: compila el frontend (Vite) y luego sirve todo desde el
# backend Flask, que en producción reparte /api/*, /uploads/* y el build de
# React desde el mismo proceso (ver backend/app.py).

FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app/backend
COPY backend/requirements.txt backend/requirements-postgres.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-postgres.txt
COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

EXPOSE 8080
CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 60
