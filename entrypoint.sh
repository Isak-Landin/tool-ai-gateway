#!/bin/sh
set -e

DB_HOST="${POSTGRES_HOST:-gateway-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
GATEWAY_BIND_PORT="${GATEWAY_PORT:-4100}"
PROJECTS_ROOT_PATH="${PROJECTS_ROOT:-/srv/tool-ai-gateway/projects}"

case "${PROJECTS_ROOT_PATH}" in
  /*) ;;
  *)
    echo "PROJECTS_ROOT must be an absolute path inside the container: ${PROJECTS_ROOT_PATH}" >&2
    exit 1
    ;;
esac

mkdir -p "${PROJECTS_ROOT_PATH}"

until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"; do
  echo 'Database not ready yet, retrying...'
  sleep 2
done

python -m db.init_db

exec uvicorn api:app --host 0.0.0.0 --port "${GATEWAY_BIND_PORT}"
