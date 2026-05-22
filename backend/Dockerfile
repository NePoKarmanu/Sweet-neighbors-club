FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN mkdir -p /ms-playwright
RUN playwright install --with-deps firefox

COPY alembic.ini /app/alembic.ini
COPY backend /app/backend

RUN chmod +x /app/backend/docker/start-api.sh /app/backend/docker/start-worker.sh /app/backend/docker/start-beat.sh
