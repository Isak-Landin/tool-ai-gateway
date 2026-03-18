#!/bin/sh
set -e

until pg_isready -h gateway-db -p 5432 -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"; do
  echo 'Database not ready yet, retrying...'
  sleep 2
done

python -m db.init_db

exec uvicorn api:app --host 0.0.0.0 --port "${GATEWAY_PORT}"