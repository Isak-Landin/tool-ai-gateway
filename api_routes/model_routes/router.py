from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ollama.config import get_ollama_default_model

from api_routes.common import error_response, log_route_error
from api_routes.model_routes.schemas import ModelOptionResponse, ModelsListResponse

models_router = APIRouter(tags=["models"])


def _resolve_default_model() -> str:
    """Return the configured backend default model name.

    Args:
        None.

    Returns:
        str: Normalized configured model name from backend environment.
    """
    return str(get_ollama_default_model()).strip()


@models_router.get("/models", response_model=ModelsListResponse)
def list_models() -> ModelsListResponse | JSONResponse:
    """List backend-owned model selections for UI/runtime callers.

    Args:
        None.

    Returns:
        ModelsListResponse | JSONResponse: Backend-owned model catalog or a configuration error.
    """
    default_model = _resolve_default_model()
    if not default_model:
        error = ValueError("OLLAMA_MODEL must not be blank")
        log_route_error("GET /models", error)
        return error_response(
            status_code=500,
            error_code="CONFIGURATION_ERROR",
            message="Backend default model is not configured.",
        )

    return ModelsListResponse(
        ok=True,
        default_model=default_model,
        default_selection="auto",
        models=[
            ModelOptionResponse(
                value="auto",
                label=f"Auto ({default_model})",
                resolved_model=default_model,
                uses_backend_default=True,
            ),
            ModelOptionResponse(
                value=default_model,
                label=default_model,
                resolved_model=default_model,
                uses_backend_default=False,
            ),
        ],
    )
