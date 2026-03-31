import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_routes import api_router
from api_routes.common import register_exception_handlers


def _get_allowed_origins() -> list[str]:
    """Load normalized browser origins for backend CORS.

    Args:
        None.

    Returns:
        list[str]: Comma-separated `CORS_ALLOWED_ORIGINS` values, trimmed and filtered.
    """
    configured_origins = str(os.getenv("CORS_ALLOWED_ORIGINS", "")).strip()
    if not configured_origins:
        print("Did not properly configure CORS_ALLOWED_ORIGINS")
        return []

    return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]


def create_app() -> FastAPI:
    """Create the FastAPI application and register shared middleware.

    Args:
        None.

    Returns:
        FastAPI: Configured API application with routes, handlers, and CORS middleware.
    """
    _app = FastAPI(title="AI Tool Gateway API")
    register_exception_handlers(app)
    _app.include_router(api_router)

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return _app


app = create_app()
