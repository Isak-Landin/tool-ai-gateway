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
        return []

    origin_list = []
    for origin in configured_origins.split(","):
        origin_str = origin.strip()
        origin_list = origin_str.split(",")

        origin_all_routes_list = [_origin + "/*" for _origin in origin_list]
        for _origin in origin_all_routes_list:
            origin_list.append(_origin.strip())

    return origin_list


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
