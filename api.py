import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from project_resolution import ProjectResolver, ProjectResolutionError, ProjectNotFoundError
from runtime_binding import ProjectBinder, ProjectBindingError
from execution import WorkflowOrchestrator, WorkflowExecutionError
from persistence import ProjectsRepository, DuplicationError, PersistenceError

from typing import Any

LOCAL_SERVER_URL = os.getenv("LOCAL_SERVER_URL")
if LOCAL_SERVER_URL is None:
    print("COULD NOT FIND LOCAL IP OR URL")
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
    """For GET /projects/{project_id}"""
    ok: bool
    id: int
    name: str
    ai_model_name: str
    orchestrator_name: str
    created_at: str

class ProjectsListResponse(BaseModel):
    """For GET /projects"""
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
# /tools
# =========================================================
@app.get("/tools/archon/search")
def http_archon_search(
    q: str,
    source: str = "",
    match_count: int = 5,
    return_mode: str = "chunks",
):
    raise HTTPException(status_code=501, detail="archon_search route not wired yet")


@app.post("/tools/archon/rag-query")
def http_archon_rag_query(data: dict):
    raise HTTPException(status_code=501, detail="archon_rag_query route not wired yet")


@app.get("/tools/web/search")
def http_web_search(q: str):
    raise HTTPException(status_code=501, detail="web_search route not wired yet")

"""
end of TOOLS ROUTES
"""

# =========================================================
# PROJECT ROUTES
# /projects
# =========================================================

@app.post("/projects/create")
def create_project(req: ProjectCreateRequest) -> (ProjectCreateResponse | Any):
    new_project = None
    try:
        name = req.name
        remote_repo_url = req.remote_repo_url
        ssh_key = req.ssh_key
        project_repository = ProjectsRepository()


        new_project = project_repository.create_project(
            name=name,
            remote_repo_url=remote_repo_url,
            ssh_key=ssh_key,
        )
        """
        class ProjectCreateResponse(BaseModel):
        ok: bool
        project_id: int
        name: str
        remote_repo_url: str
        ssh_key: str
        """

        if new_project:
            return ProjectCreateResponse(ok=True, **new_project)
    except KeyError as e:
        return HTTPException(status_code=400, detail=str(e))
    except DuplicationError as e:
        return HTTPException(status_code=400, detail=str(e))

    if new_project:
        return HTTPException(
            status_code=500,
            detail="Reached end of post.projects new_project exists, but reached end without returning it or raising other error"
        )
    else:
        return HTTPException(
            status_code=500,
            detail="Reached end of post.projects without existing new_project and without having returned error earlier"
        )



@app.get("/projects")
def list_projects():
    """
    1. Instantiate ProjectsRepository()
    2. Call list_all_projects() → returns list[dict]
    3. Try/except for PersistenceError → 500
    4. Return ProjectsListResponse(ok=True, projects=[...])
       - NO ProjectResolver needed here (just listing, not validating a specific project)
    """
    try:
        project_repository = ProjectsRepository()
        all_projects = project_repository.list_all_projects()
        # Wrap each project dict to add 'ok' field
        projects_with_ok = [{'ok': True, **project} for project in all_projects]
        return ProjectsListResponse(ok=True, projects=projects_with_ok)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ProjectResolutionError, ProjectBindingError, WorkflowExecutionError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PersistenceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}")
def get_project(project_id: int):
    """
    1. Instantiate ProjectResolver()
    2. Call resolve_by_id(project_id)
       - If ProjectNotFoundError → 404
       - If ProjectResolutionError → 400
    3. Return ProjectDetailResponse(ok=True, ...)
       - DO NOT call ProjectBinder here (not executing workflow)
       - DO NOT call WorkflowOrchestrator here
       - Just return project metadata
    """
    try:
        project_resolver = ProjectResolver()
        project = project_resolver.resolve_by_id(project_id)
        return ProjectDetailResponse(ok=True, **project)
    except ProjectNotFoundError as e:
        return HTTPException(status_code=404, detail=str(e))
    except ProjectResolutionError as e:
        return HTTPException(status_code=400, detail=str(e))



@app.patch("/projects/{project_id}")
def update_project(project_id: int):
    raise HTTPException(status_code=501, detail="update_project route not wired yet")


@app.delete("/projects/{project_id}")
def delete_project(project_id: int):
    raise HTTPException(status_code=501, detail="delete_project route not wired yet")


@app.post("/projects/{project_id}/run",response_model=ChatResponse)
def run(project_id: int, req: ChatRequest):
    if not str(req.message).strip():
        raise HTTPException(status_code=400, detail="message is required")

    try:
        return chat_workflow_entry(project_id, req)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ProjectResolutionError, ProjectBindingError, WorkflowExecutionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

"""
end of PROJECT ROUTES
"""

# =========================================================
# FILES ROUTES
# /files
# =========================================================
"""
end of FILE ROUTES
"""


@app.get("/debug")
def debug():
    return FileResponse("index.html")