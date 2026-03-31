import os


class Config:
    UI_HOST = os.getenv("UI_HOST", "0.0.0.0")
    UI_PORT = int(os.getenv("UI_PORT", "4000"))
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "ui-structure-placeholder")
    GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:4100").rstrip("/")
    APP_NAME = "AI Tool Gateway"
    UI_TRUSTED_HOSTS = tuple(
        host.strip()
        for host in os.getenv("UI_TRUSTED_HOSTS", "localhost,127.0.0.1").split(",")
        if host.strip()
    )
