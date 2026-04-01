#!/usr/bin/env bash
set -euo pipefail

SOURCE_EPOCH="${SOURCE_EPOCH:-$(date +%s)}"

git pull origin
docker compose down
docker compose build --build-arg SOURCE_EPOCH="${SOURCE_EPOCH}"
docker compose up -d
