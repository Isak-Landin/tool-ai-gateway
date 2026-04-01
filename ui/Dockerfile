FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

ARG SOURCE_EPOCH=0

COPY app.py /app/app.py
COPY webapp /app/webapp
COPY templates /app/templates
COPY static /app/static
COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
