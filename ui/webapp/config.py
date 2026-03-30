import os


class Config:
    UI_HOST = os.getenv("UI_HOST", "0.0.0.0")
    UI_PORT = int(os.getenv("UI_PORT", "4000"))
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "ui-structure-placeholder")
    GATEWAY_BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:4100").rstrip("/")
    APP_NAME = "AI Tool Gateway"
