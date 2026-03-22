#!/bin/sh
# Development mode: mounts host source into containers for live-reload.
# For production, use: docker compose up -d
set -e

docker compose down --remove-orphans

docker compose run -d --service-ports --name ai-tool-gateway \
  -v "$(pwd):/app" \
  -e DEBUG=true \
  tool-gateway

docker compose run -d --service-ports --name ui-tool-gateway \
  -v "$(pwd)/ui:/app" \
  -e FLASK_DEBUG=true \
  tool-gateway-ui

echo "Dev containers running with live-reload."
