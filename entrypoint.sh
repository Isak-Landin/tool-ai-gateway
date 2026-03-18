#!/bin/sh
set -e

until pg_isready -h gateway-db -p 5432 -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"; do
  echo 'Database not ready yet, retrying...'
  sleep 2
done

# python /app/db/init_db.py

exec uvicorn tool_gateway:app --host 0.0.0.0 --port "${GATEWAY_PORT}"