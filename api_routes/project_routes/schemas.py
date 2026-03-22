from pydantic import BaseModel, Field
import datetime


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