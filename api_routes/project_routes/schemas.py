from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """Request body for creating a new project."""

    name: str
    remote_repo_url: str


class ProjectCreateResponse(BaseModel):
    """Response body returned after successful project creation."""

    ok: bool
    project_id: int
    name: str
    remote_repo_url: str
    public_key: str


class ProjectSummaryResponse(BaseModel):
    """Compact project summary returned in project listings."""

    project_id: int
    name: str
    branch: str
    remote_repo_url: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None


class ProjectsListResponse(BaseModel):
    """Response body returned by the projects list route."""

    ok: bool
    projects: list[ProjectSummaryResponse]


class ProjectDetailResponse(BaseModel):
    """Response body returned by project detail and update routes."""

    ok: bool
    project_id: int
    name: str
    branch: str
    remote_repo_url: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None


class ProjectUpdateRequest(BaseModel):
    """Request body for updating mutable project metadata."""

    name: str | None = None
    branch: str | None = None


class MessageEntryResponse(BaseModel):
    """Serialized project message/history entry returned by message routes."""

    id: int
    sequence_no: int
    role: str
    content: str | None = None
    thinking: str | None = None
    tool_name: str | None = None
    tool_calls_json: list[dict[str, Any]] | None = None
    images_json: list[dict[str, Any]] | None = None
    ai_model_name: str | None = None
    ollama_created_at: datetime.datetime | None = None
    done: bool | None = None
    done_reason: str | None = None
    total_duration: int | None = None
    load_duration: int | None = None
    prompt_eval_count: int | None = None
    prompt_eval_duration: int | None = None
    eval_count: int | None = None
    eval_duration: int | None = None
    raw_message_json: dict[str, Any] | None = None
    raw_response_json: dict[str, Any] | None = None
    created_at: datetime.datetime


class ProjectMessagesResponse(BaseModel):
    """Response body returned by the project messages route."""

    ok: bool
    project_id: int
    branch: str
    messages: list[MessageEntryResponse]


class RepositoryTreeEntryResponse(BaseModel):
    """Single repository tree entry returned by tree-listing routes."""

    name: str
    path: str
    is_dir: bool
    is_file: bool
    depth: int


class RepositoryTreeResponse(BaseModel):
    """Response body returned by the repository tree route."""

    ok: bool
    project_id: int
    branch: str
    path: str
    entries: list[RepositoryTreeEntryResponse]


class RepositoryFileResponse(BaseModel):
    """Response body returned by the repository file-read route."""

    ok: bool
    project_id: int
    branch: str
    name: str
    path: str
    content: str
    start_line: int
    end_line: int
    total_lines: int


class RepositorySearchMatchResponse(BaseModel):
    """Single repository text-search match returned by search routes."""

    path: str
    line_number: int
    line_text: str


class RepositorySearchResponse(BaseModel):
    """Response body returned by the repository search route."""

    ok: bool
    project_id: int
    branch: str
    query: str
    matches: list[RepositorySearchMatchResponse]


class ChatRequest(BaseModel):
    """Request body for one project-scoped chat run."""

    message: str
    selected_files: list[str] = Field(default_factory=list)
    branch: str | None = None
    ai_model_name: str | None = None


class ChatResponse(BaseModel):
    """Response body returned after one project-scoped chat run."""

    ok: bool
    project_id: int
    message: str
    selected_files: list[str]
    branch: str
    ai_model_name: str
    execution_type: str | None = None
    return_to_user: dict[str, Any] | None = None
