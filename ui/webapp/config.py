import os


class Config:
    UI_HOST = os.getenv("UI_HOST", "0.0.0.0")
    UI_PORT = int(os.getenv("UI_PORT", "4000"))
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "ui-structure-placeholder")
    GATEWAY_BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:8000").rstrip("/")
    APP_NAME = "AI Tool Gateway"
    WORKSPACE_MODEL_OPTIONS = tuple(
        option.strip()
        for option in os.getenv("UI_WORKSPACE_MODELS", "qwen3:8b,llama3.2,gpt-oss:latest").split(",")
        if option.strip()
    )
