# AI Tool Gateway

> Self-hosted model + tools + project context gateway with a web UI.

⚠️ **Status:** under active development. The project is not complete and parts of the architecture are still being stabilized.

## What it is

AI Tool Gateway is intended to connect:

- a web UI
- a gateway API
- PostgreSQL persistence
- Ollama, self-hosted or remote
- project-scoped tools such as `git` and `web_search`

The goal is to let the application coordinate model requests and tool usage without giving the model direct system access.

## Current stack

- **Gateway API** — Python backend container
- **UI** — separate Python UI container
- **PostgreSQL** — persistent state in `db/`
- **Ollama** — local or remote model endpoint
- **Tools** — currently includes project git access and web search, with room for more

## Project setup

The easiest project setup is:

1. Copy `env.example` to `.env`
2. Adjust values if needed
3. Start the stack with Docker Compose

```bash
cp env.example .env
docker compose up --build
```

This is the intended local/project-level startup path.

The compose setup includes:

- gateway container
- UI container
- PostgreSQL container

It expects the external Docker network `web_network` to exist.

## System setup

If you are preparing a server with most of the required supporting services, use:

`setup_ollama_litellm_system.sh`

That script is intended to be copied to the target server and run there. It handles most of the host/system preparation work, including Docker-related setup and Ollama container provisioning.

## Environment

The main configuration file is:

`env.example`

Typical values include:

- PostgreSQL connection settings
- gateway and UI ports
- gateway base URLs
- Ollama base URL and model
- Archon base URL
- web search configuration

## Notes

- `Dockerfile` builds the gateway container
- `ui/Dockerfile` builds the UI container
- `docker-compose.yml` defines the intended project runtime stack
- the repository is still evolving, so setup details may change as lower-level modules are refined
