# Multi-stage build: compile the React frontend, then run it from the same
# FastAPI process that serves the API (see app/main.py's StaticFiles mount).
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS backend
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY templates/ templates/
COPY --from=frontend-build /app/frontend/dist frontend/dist

WORKDIR /app/backend
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# .env (secrets) is mounted/injected at runtime, never baked into the image.
# Most PaaS hosts (Render, Railway, Heroku-style) inject a $PORT the container MUST
# bind to and override it at deploy time — falls back to 8000 for plain `docker run`.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
