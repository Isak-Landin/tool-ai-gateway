import datetime
import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from project_resolution import ProjectResolver, ProjectResolutionError, ProjectNotFoundError
from runtime_binding import ProjectBinder, ProjectBindingError
from execution import WorkflowOrchestrator, WorkflowExecutionError
from persistence import ProjectsRepository
from errors import PersistenceError

LOCAL_SERVER_URL = os.getenv("LOCAL_SERVER_URL")
if LOCAL_SERVER_URL is None:
    exit(1)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[LOCAL_SERVER_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# SCHEMAS
# =========================================================

class ChatRequest(BaseModel):
    message: str
    selected_files: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    ok: bool
    project_id: int
    message: str
    selected_files: list[str]
    next_layer: str


class ProjectCreateRequest(BaseModel):
    name: str
    remote_repo_url: str
    ssh_key: str


class ProjectCreateResponse(BaseModel):
    ok: bool
    project_id: int
    name: str
    remote_repo_url: str
    ssh_key: str


class ProjectDetailResponse(BaseModel):
    ok: bool
    project_id: int
    name: str
    ai_model_name: str
    orchestrator_name: str
    created_at: datetime.datetime


class ProjectsListResponse(BaseModel):
    ok: bool
    projects: list[ProjectDetailResponse]


# =========================================================
# INTERNAL WORKFLOW HELPERS
# =========================================================

def chat_workflow_entry(project_id, req: ChatRequest) -> ChatResponse:
    resolver = ProjectResolver()
    binder = ProjectBinder()
    orchestrator = WorkflowOrchestrator()

    project_row = resolver.resolve_by_id(project_id)
    handle = binder.bind(project_row)

    result = orchestrator.run_chat(
        handle=handle,
        message=req.message,
        selected_files=req.selected_files,
    )

    return ChatResponse(
        ok=result.get("ok", False),
        project_id=project_id,
        message=result.get("answer", result.get("message", "")),
        selected_files=req.selected_files,
        next_layer="execution_completed",
    )


# =========================================================
# TOOLS ROUTES
# =========================================================

@app.get("/tools/archon/search")
def http_archon_search(q: str, source: str = "", match_count: int = 5, return_mode: str = "chunks"):
    raise HTTPException(status_code=501, detail="archon_search route not wired yet")


@app.post("/tools/archon/rag-query")
def http_archon_rag_query(data: dict):
    raise HTTPException(status_code=501, detail="archon_rag_query route not wired yet")


@app.get("/tools/web/search")
def http_web_search(q: str):
    raise HTTPException(status_code=501, detail="web_search route not wired yet")


# =========================================================
# PROJECT ROUTES
# =========================================================

@app.post("/projects", status_code=status.HTTP_201_CREATED)
def create_project(req: ProjectCreateRequest) -> ProjectCreateResponse:
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


@app.get("/projects")
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


@app.get("/projects/{project_id}")
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


@app.patch("/projects/{project_id}")
def update_project(project_id: int):
    raise HTTPException(status_code=501, detail="update_project route not wired yet")


@app.delete("/projects/{project_id}")
def delete_project(project_id: int):
    raise HTTPException(status_code=501, detail="delete_project route not wired yet")


@app.post("/projects/{project_id}/run", response_model=ChatResponse)
def run(project_id: int, req: ChatRequest):
    if not str(req.message).strip():
        raise HTTPException(status_code=400, detail="message is required")

    try:
        return chat_workflow_entry(project_id, req)
    except ProjectNotFoundError as e:
        print(f"[API ERROR] POST /projects/{project_id}/run not found: {e!r}")
        raise HTTPException(status_code=404, detail=str(e))
    except (ProjectResolutionError, ProjectBindingError, WorkflowExecutionError) as e:
        print(f"[API ERROR] POST /projects/{project_id}/run workflow failure: {e!r}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[API ERROR] POST /projects/{project_id}/run unexpected failure: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug")
def debug():
    return FileResponse("index.html")
