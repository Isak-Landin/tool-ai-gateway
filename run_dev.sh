#!/bin/sh
# Development mode: mounts host source into containers for live-reload.
# For production, use: docker compose up -d
set -e

docker compose down --remove-orphans
docker compose build

# Gateway with host source mounted + DEBUG for uvicorn --reload
docker compose run -d --service-ports --name ai-tool-gateway \
  -v "$(pwd)/api.py:/app/api.py" \
  -v "$(pwd)/project_resolution.py:/app/project_resolution.py" \
  -v "$(pwd)/runtime_binding.py:/app/runtime_binding.py" \
  -v "$(pwd)/project_handle.py:/app/project_handle.py" \
  -v "$(pwd)/execution.py:/app/execution.py" \
  -v "$(pwd)/persistence.py:/app/persistence.py" \
  -v "$(pwd)/errors.py:/app/errors.py" \
  -v "$(pwd)/db:/app/db" \
  -v "$(pwd)/git:/app/git" \
  -v "$(pwd)/ollama:/app/ollama" \
  -v "$(pwd)/archon:/app/archon" \
  -v "$(pwd)/web_search:/app/web_search" \
  -v "$(pwd)/index.html:/app/index.html" \
  -e DEBUG=true \
  tool-gateway

# UI with host source mounted + FLASK_DEBUG for Flask reload
docker compose run -d --service-ports --name ui-tool-gateway \
  -v "$(pwd)/ui/app.py:/app/app.py" \
  -v "$(pwd)/ui/templates:/app/templates" \
  -v "$(pwd)/ui/static:/app/static" \
  -e FLASK_DEBUG=true \
  tool-gateway-ui

echo "Dev containers running with live-reload."
