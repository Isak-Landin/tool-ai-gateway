FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /app/requirements.txt

COPY api.py /app/api.py
COPY ProjectResolver /app/ProjectResolver
COPY ProjectRuntimeBinder /app/ProjectRuntimeBinder
COPY BoundProjectRuntime /app/BoundProjectRuntime
COPY repository_runtime /app/repository_runtime
COPY execution /app/execution
COPY persistence.py /app/persistence.py
COPY errors.py /app/errors.py
COPY db/* /app/db/
COPY ollama /app/ollama
COPY archon /app/archon
COPY web_search /app/web_search
COPY tools /app/tools
COPY index.html /app/index.html
COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1

CMD ["/app/entrypoint.sh"]
