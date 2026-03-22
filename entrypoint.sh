#!/bin/sh
set -e

until pg_isready -h gateway-db -p 5432 -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"; do
  echo 'Database not ready yet, retrying...'
  sleep 2
done

python -m db.init_db

if [ "${DEBUG}" = "true" ]; then
  echo "[DEBUG] Starting uvicorn with --reload for live code reloading"
  exec uvicorn api:app --host 0.0.0.0 --port "${GATEWAY_PORT}" --reload
else
  exec uvicorn api:app --host 0.0.0.0 --port "${GATEWAY_PORT}"
fi