#!/bin/sh
set -e

until python -c "from db.session import engine; from sqlalchemy import text; \
with engine.connect() as conn: conn.execute(text('SELECT 1'))"; do
  echo "Database not ready yet, retrying..."
  sleep 2
done

python /app/db/init_db.py

exec uvicorn tool_gateway:app --host 0.0.0.0 --port "${GATEWAY_PORT}"