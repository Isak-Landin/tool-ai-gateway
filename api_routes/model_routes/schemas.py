from pydantic import BaseModel


class ModelOptionResponse(BaseModel):
    """Single backend-owned model option returned by model discovery routes."""

    value: str
    label: str
    resolved_model: str
    uses_backend_default: bool


class ModelsListResponse(BaseModel):
    """Response body returned by backend model discovery routes."""

    ok: bool
    default_model: str
    default_selection: str
    models: list[ModelOptionResponse]
