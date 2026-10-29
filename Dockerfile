FROM node:22-alpine AS astro-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/astro.config.mjs frontend/tsconfig.json ./
COPY frontend/src ./src
RUN npm run build

FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 app \
    && mkdir -p /var/lib/celery \
    && chown app:app /app /var/lib/celery

COPY --chown=app:app . .
COPY --from=astro-build --chown=app:app /frontend/dist /app/frontend/dist
USER app

EXPOSE 8000
CMD ["uvicorn", "inet_ivs.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
