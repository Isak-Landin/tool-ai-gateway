import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from project_resolution import ProjectResolver, ProjectResolutionError, ProjectNotFoundError
from runtime_binding import ProjectBinder, ProjectBindingError
from execution import WorkflowOrchestrator, WorkflowExecutionError
from persistence import ProjectsRepository, DuplicationError


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
def create_project(req: ProjectCreateRequest) -> ProjectCreateResponse:
    """
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
    """
    response = HTTPException(status_code=500, detail="Create Project reached a separate return end to intended")
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
        if new_project:
            response = ProjectCreateResponse(
                ok=True,
                project_id=new_project.project_id,
                name=new_project.name,
                remote_repo_url=new_project.remote_repo_url,
                ssh_key=new_project.ssh_key,
            )
    except KeyError as e:
        response = HTTPException(status_code=400, detail=str(e))
    except DuplicationError as e:
        response = HTTPException(status_code=400, detail=str(e))
    finally:
        return response


@app.get("/projects")
def list_projects():
    raise HTTPException(status_code=501, detail="list_projects route not wired yet")


@app.get("/projects/{project_id}")
def get_project(project_id: int):
    raise HTTPException(status_code=501, detail="get_project route not wired yet")


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