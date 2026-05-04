#!/bin/sh
set -e

until pg_isready -h postgres -p 5432 -U "${POSTGRES_USER:-postgres}"; do
  echo "Waiting for postgres..."
  sleep 1
done

alembic upgrade head
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --no-access-log
