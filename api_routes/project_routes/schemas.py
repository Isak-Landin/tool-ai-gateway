from pydantic import BaseModel, Field
import datetime


# =========================================================
# SCHEMAS
# =========================================================

class ChatRequest(BaseModel):
    message: str
    selected_files: list[str] = Field(default_factory=list)
    branch: str | None = None
    ai_model_name: str | None = None


class ChatResponse(BaseModel):
    ok: bool
    project_id: int
    message: str
    selected_files: list[str]
    branch: str
    ai_model_name: str
    next_layer: str


class ProjectCreateRequest(BaseModel):
    name: str
    remote_repo_url: str


class ProjectCreateResponse(BaseModel):
    ok: bool
    project_id: int
    name: str
    remote_repo_url: str
    public_key: str


class ProjectDetailResponse(BaseModel):
    ok: bool
    project_id: int
    name: str
    branch: str
    created_at: datetime.datetime


class ProjectsListResponse(BaseModel):
    ok: bool
    projects: list[ProjectDetailResponse]
