# AI Tool Gateway

> Self-hosted project workspace gateway with a split UI/backend architecture.

⚠️ **Status:** under active development. The repository is intentionally incomplete while route ownership and lower-layer boundaries are being stabilized.

## Intent

AI Tool Gateway is building toward one workspace-centered application made of:

- a Flask UI shell in `ui/`
- a FastAPI gateway/backend in the repository root
- PostgreSQL-backed persistence
- Ollama-backed model execution
- project-scoped runtime capabilities such as repository reads, repository search, and chat execution

The main architectural intent is:

- browser JS should talk to UI-owned routes
- the UI layer should own page rendering and UI-specific JSON/action routes
- the backend API should own runtime and persistence-facing contracts
- the model should not receive direct unrestricted system access

## Current runtime shape

- **UI container** — Flask + Jinja shell in `ui/`
- **Gateway container** — FastAPI backend and runtime orchestration
- **PostgreSQL** — persisted project/message state
- **Ollama** — local or remote model endpoint

The UI and backend are intentionally separate services. The current direction is for the UI to mediate browser-facing interactions instead of having browser JS call backend API routes directly.

## Current product focus

The current live focus is the project workspace flow:

- list projects
- create/bootstrap a project
- load one project workspace
- browse repository tree/file/search views
- inspect project message history
- run project chat against the bound runtime

Auth, account, invitation, and application-settings flows are present as UI shells but are not yet backed by finished backend contracts.

## Local/project setup

1. Copy `env.example` to `.env`
2. Adjust values for your environment
3. Start the stack with Docker Compose

```bash
cp env.example .env
docker compose up --build
```

The intended compose stack includes:

- gateway container
- UI container
- PostgreSQL container

It expects the external Docker network `web_network` to exist.

## Environment notes

Primary runtime configuration lives in `env.example`.

Important examples include:

- `DATABASE_URL`
- `GATEWAY_PORT`
- `UI_PORT`
- `GATEWAY_URL`
- `CORS_ALLOWED_ORIGINS`
- `PROJECTS_HOST_ROOT`
- `PROJECTS_ROOT`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `UI_TRUSTED_HOSTS`

## Repository notes

- `Dockerfile` builds the backend container
- `ui/Dockerfile` builds the UI container
- `docker-compose.yml` defines the intended runtime stack
- `ARCHITECTURAL_MISMATCHES_AND_CONCERNS.md` is the active register of unresolved route/ownership gaps
- setup details may continue to shift while route ownership and runtime boundaries are hardened
