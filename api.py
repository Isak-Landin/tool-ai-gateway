import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_routes import api_router
from api_routes.common import register_exception_handlers


def _get_allowed_origins() -> list[str]:
    """Load normalized CORS origins from environment configuration.

    Args:
        None.

    Returns:
        list[str]: Comma-separated `LOCAL_SERVER_URL` values, trimmed and filtered.
    """
    configured_origins = str(os.getenv("LOCAL_SERVER_URL", "")).strip()
    if not configured_origins:
        return []

    return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]


def create_app() -> FastAPI:
    """Create the FastAPI application and register shared middleware.

    Args:
        None.

    Returns:
        FastAPI: Configured API application with routes, handlers, and CORS middleware.
    """
    app = FastAPI(title="AI Tool Gateway API")
    register_exception_handlers(app)
    app.include_router(api_router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()
