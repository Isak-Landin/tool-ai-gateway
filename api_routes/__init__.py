from fastapi import APIRouter

from api_routes.model_routes import models_router
from api_routes.project_routes import projects_router

api_router = APIRouter()
api_router.include_router(models_router)
api_router.include_router(projects_router)

__all__ = ["api_router"]
