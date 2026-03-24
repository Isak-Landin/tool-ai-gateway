from fastapi import HTTPException, status, APIRouter
from fastapi.responses import JSONResponse

from ProjectResolver import (
    ProjectResolver,
    ProjectResolutionError,
    ProjectNotFoundError,
)
from ProjectRuntimeBinder import ProjectRuntimeBindingError, ProjectRuntimeBinder
from execution import WorkflowExecutionError, WorkflowOrchestrator
from persistence import ProjectsRepository
from errors import PersistenceError

from api_routes.project_routes.utils import chat_workflow_entry
from api_routes.project_routes.schemas import *

# =========================================================
# PROJECT ROUTES
# =========================================================

projects_router = APIRouter(prefix="/projects", tags=["projects"])

@projects_router.post("", status_code=status.HTTP_201_CREATED)
def create_project(req: ProjectCreateRequest) -> ProjectCreateResponse | JSONResponse:
    """Create a new project. Returns 201 on success."""
    try:
        project_repository = ProjectsRepository()
        new_project = project_repository.create_project(
            name=req.name,
            remote_repo_url=req.remote_repo_url,
            ssh_key=req.ssh_key,
        )
        if new_project:
            return ProjectCreateResponse(ok=True, **new_project)
        else:
            raise HTTPException(status_code=500, detail="Failed to create project")
    except PersistenceError as e:
        print(f"[API ERROR] POST /projects persistence failure: {e!r}")
        # Map error_type to HTTP status code
        if e.error_type == "duplicate":
            status_code = 409  # Conflict
        else:
            status_code = 500  # Internal Server Error

        return JSONResponse(
            status_code=status_code,
            content={
                "ok": False,
                "error_code": "DUPLICATE_FIELD" if e.error_type == "duplicate" else "PERSISTENCE_ERROR",
                "field": e.field,
                "message": e.message
            }
        )
    except Exception as e:
        print(f"[API ERROR] POST /projects unexpected failure: {e!r}")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error_code": "PERSISTENCE_ERROR",
                "message": str(e)
            }
        )


@projects_router.get("")
def list_projects():
    try:
        project_repository = ProjectsRepository()
        all_projects = project_repository.list_all_projects()
        projects_with_ok = [
            ProjectDetailResponse(ok=True, **project)
            for project in all_projects
        ]
        return ProjectsListResponse(ok=True, projects=projects_with_ok)
    except PersistenceError as e:
        print(f"[API ERROR] GET /projects persistence failure: {e!r}")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error_code": "PERSISTENCE_ERROR",
                "message": e.message
            }
        )


@projects_router.get("/{project_id}")
def get_project(project_id: int):
    try:
        project_resolver = ProjectResolver()
        project = project_resolver.resolve_by_id(project_id)
        return ProjectDetailResponse(ok=True, **project)
    except ProjectNotFoundError as e:
        print(f"[API ERROR] GET /projects/{project_id} not found: {e!r}")
        raise HTTPException(status_code=404, detail=str(e))
    except ProjectResolutionError as e:
        print(f"[API ERROR] GET /projects/{project_id} resolution failure: {e!r}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[API ERROR] GET /projects/{project_id} unexpected failure: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))


@projects_router.patch("/{project_id}")
def update_project(project_id: int):
    raise HTTPException(status_code=501, detail="update_project route not wired yet")


@projects_router.delete("/{project_id}")
def delete_project(project_id: int):
    raise HTTPException(status_code=501, detail="delete_project route not wired yet")


@projects_router.post("/{project_id}/run", response_model=ChatResponse)
def run(project_id: int, req: ChatRequest):
    if not str(req.message).strip():
        raise HTTPException(status_code=400, detail="message is required")

    try:
        resolver = ProjectResolver()
        binder = ProjectRuntimeBinder()
        orchestrator = WorkflowOrchestrator()
        return chat_workflow_entry(project_id, req, resolver, binder, orchestrator)
    except ProjectNotFoundError as e:
        print(f"[API ERROR] POST /projects/{project_id}/run not found: {e!r}")
        raise HTTPException(status_code=404, detail=str(e))
    except (ProjectResolutionError, ProjectRuntimeBindingError, WorkflowExecutionError) as e:
        print(f"[API ERROR] POST /projects/{project_id}/run workflow failure: {e!r}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[API ERROR] POST /projects/{project_id}/run unexpected failure: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))
