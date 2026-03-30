#!/usr/bin/env bash
set -euo pipefail

UI_CONTAINER="${UI_CONTAINER:-ui-tool-gateway}"
API_CONTAINER="${API_CONTAINER:-ai-tool-gateway}"
DB_CONTAINER="${DB_CONTAINER:-ai-tool-gateway-db}"

UI_HOST_HEADER="${UI_HOST_HEADER:-tool_ui.isaklandin.com}"
UI_URL="${UI_URL:-http://127.0.0.1:4000/}"
API_MODELS_URL="${API_MODELS_URL:-http://127.0.0.1:4100/models}"
API_PROJECTS_URL="${API_PROJECTS_URL:-http://127.0.0.1:4100/projects}"

print_section() {
  printf '\n========== %s ==========\n' "$1"
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "$1" >&2
    exit 1
  fi
}

run_or_warn() {
  if ! "$@"; then
    printf '\n[warning] command failed: %s\n' "$*" >&2
  fi
}

require_command docker
require_command curl

print_section "docker ps"
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'

print_section "ui env"
run_or_warn docker exec "$UI_CONTAINER" sh -lc \
  "env | grep -E '^(UI_TRUSTED_HOSTS|FLASK_DEBUG|GATEWAY_BASE_URL|UI_HOST|UI_PORT|PYTHONUNBUFFERED)=' | sort"

print_section "backend env"
run_or_warn docker exec "$API_CONTAINER" sh -lc \
  "env | grep -E '^(DATABASE_URL|LOCAL_SERVER_URL|GATEWAY_PORT|PROJECTS_ROOT|OLLAMA_MODEL|OLLAMA_BASE_URL|PYTHONUNBUFFERED)=' | sort"

print_section "ui deployed config files"
run_or_warn docker exec "$UI_CONTAINER" sh -lc \
  "printf '\n--- /app/webapp/config.py ---\n'; sed -n '1,80p' /app/webapp/config.py; \
   printf '\n--- /app/webapp/__init__.py ---\n'; sed -n '1,120p' /app/webapp/__init__.py; \
   printf '\n--- /app/app.py ---\n'; sed -n '1,40p' /app/app.py"

print_section "ui trusted host curl"
run_or_warn docker exec "$UI_CONTAINER" sh -lc \
  "curl -sS -i -H 'Host: ${UI_HOST_HEADER}' '${UI_URL}' | sed -n '1,60p'"

print_section "ui localhost curl"
run_or_warn docker exec "$UI_CONTAINER" sh -lc \
  "curl -sS -i '${UI_URL}' | sed -n '1,40p'"

print_section "backend /models"
run_or_warn docker exec "$API_CONTAINER" sh -lc \
  "curl -sS -i '${API_MODELS_URL}' | sed -n '1,40p'"

print_section "backend /projects"
run_or_warn docker exec "$API_CONTAINER" sh -lc \
  "curl -sS -i '${API_PROJECTS_URL}' | sed -n '1,40p'"

print_section "ui logs (tail 200)"
run_or_warn docker logs "$UI_CONTAINER" --tail 200

print_section "backend logs (tail 200)"
run_or_warn docker logs "$API_CONTAINER" --tail 200

print_section "db logs (tail 80)"
run_or_warn docker logs "$DB_CONTAINER" --tail 80

print_section "compose config snippets"
run_or_warn docker compose -f docker-compose.yml config | sed -n '1,160p'

print_section "done"
printf 'If needed, override defaults like:\n'
printf '  UI_HOST_HEADER=tool_ui.isaklandin.com bash ./debug_runtime_hosts.sh\n'
