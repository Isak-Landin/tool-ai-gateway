import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from project_resolution import ProjectResolver, ProjectResolutionError, ProjectNotFoundError
from runtime_binding import ProjectBinder, ProjectBindingError
from execution import WorkflowOrchestrator, WorkflowExecutionError


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


class ChatRequest(BaseModel):
    project_id: int
    message: str
    selected_files: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    ok: bool
    project_id: int
    message: str
    selected_files: list[str]
    next_layer: str


def chat_workflow_entry(req: ChatRequest) -> ChatResponse:
    resolver = ProjectResolver()
    binder = ProjectBinder()
    orchestrator = WorkflowOrchestrator()

    project_row = resolver.resolve_by_id(req.project_id)
    handle = binder.bind(project_row)

    result = orchestrator.run_chat(
        handle=handle,
        message=req.message,
        selected_files=req.selected_files,
    )

    return ChatResponse(
        ok=result.get("ok", False),
        project_id=req.project_id,
        message=result.get("answer", result.get("message", "")),
        selected_files=req.selected_files,
        next_layer="execution_completed",
    )


@app.get("/archon_search")
def http_archon_search(
    q: str,
    source: str = "",
    match_count: int = 5,
    return_mode: str = "chunks",
):
    raise HTTPException(status_code=501, detail="archon_search route not wired yet")


@app.post("/archon_rag_query")
def http_archon_rag_query(data: dict):
    raise HTTPException(status_code=501, detail="archon_rag_query route not wired yet")


@app.get("/web_search")
def http_web_search(q: str):
    raise HTTPException(status_code=501, detail="web_search route not wired yet")


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not str(req.message).strip():
        raise HTTPException(status_code=400, detail="message is required")

    try:
        return chat_workflow_entry(req)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ProjectResolutionError, ProjectBindingError, WorkflowExecutionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/debug")
def debug():
    return FileResponse("index.html")