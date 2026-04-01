from __future__ import annotations

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from ProjectResolver import ProjectNotFoundError, ProjectResolutionError
from ProjectRuntimeBinder import ProjectRuntimeBindingError
from errors import FileRuntimeError, MessageRuntimeError, ProjectPersistenceError
from execution import WorkflowExecutionError
from persistence.ProjectPersistence import ProjectPersistence

from api_routes.common import error_response, log_route_error, persistence_error_response
from api_routes.project_routes.runtime import (
    bound_project_execution_runtime,
    bound_project_route_runtime,
    build_workflow_orchestrator,
)
from api_routes.project_routes.schemas import (
    ChatRequest,
    ChatResponse,
    ProjectCreateRequest,
    ProjectCreateResponse,
    ProjectDetailResponse,
    ProjectMessagesResponse,
    ProjectsListResponse,
    ProjectSummaryResponse,
    ProjectUpdateRequest,
    RepositoryFileResponse,
    RepositorySearchResponse,
    RepositoryTreeResponse,
)

projects_router = APIRouter(prefix="/projects", tags=["projects"])


def _not_found_response(route_label: str, error: Exception) -> JSONResponse:
    """Build the standard not-found route response.

    Args:
        route_label: Human-readable route identifier for logging.
        error: Exception describing the missing backend resource.

    Returns:
        JSONResponse: JSON error payload with a 404 status code.
    """
    log_route_error(route_label, error)
    return error_response(status_code=404, error_code="NOT_FOUND", message=str(error))


def _runtime_error_response(route_label: str, error: Exception, *, status_code: int = 400) -> JSONResponse:
    """Build the standard runtime-error route response.

    Args:
        route_label: Human-readable route identifier for logging.
        error: Runtime-layer exception that should be exposed to the client.
        status_code: HTTP status code to use for the error response.

    Returns:
        JSONResponse: JSON error payload using the shared runtime error shape.
    """
    log_route_error(route_label, error)
    return error_response(status_code=status_code, error_code="RUNTIME_ERROR", message=str(error))


@projects_router.post("", status_code=status.HTTP_201_CREATED, response_model=ProjectCreateResponse)
def create_project(req: ProjectCreateRequest) -> ProjectCreateResponse | JSONResponse:
    """Create a new persisted project and bootstrap its local storage.

    Args:
        req: Validated project-create payload with project name and remote URL.

    Returns:
        ProjectCreateResponse | JSONResponse: Success payload for the new project or an error response.
    """
    project_persistence = ProjectPersistence()
    try:
        new_project = project_persistence.create_project(
            name=req.name,
            remote_repo_url=req.remote_repo_url,
        )
        """
        new_project contains:
        {
            "project_id": new_project.project_id,
            "name": new_project.name,
            "remote_repo_url": new_project.remote_repo_url,
            "public_key": public_key,
        }
        """
        return ProjectCreateResponse(ok=True, **new_project)
    except ProjectPersistenceError as error:
        return persistence_error_response("POST /projects", error)


@projects_router.get("", response_model=ProjectsListResponse)
def list_projects() -> ProjectsListResponse | JSONResponse:
    """List all persisted projects for the project index route.

    Args:
        None.

    Returns:
        ProjectsListResponse | JSONResponse: Project summaries or an error response.
    """
    project_persistence = ProjectPersistence()
    try:
        all_projects = project_persistence.list_all_projects()
        return ProjectsListResponse(
            ok=True,
            projects=[ProjectSummaryResponse(**project_row) for project_row in all_projects],
        )
    except ProjectPersistenceError as error:
        return persistence_error_response("GET /projects", error)


@projects_router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(project_id: int) -> ProjectDetailResponse | JSONResponse:
    """Load one persisted project detail payload by id.

    Args:
        project_id: Persisted project identifier requested by the client.

    Returns:
        ProjectDetailResponse | JSONResponse: Project detail payload or an error response.
    """
    project_persistence = ProjectPersistence()
    try:
        project_row = project_persistence.get_project_by_id(project_id)
        if project_row is None:
            raise ProjectNotFoundError(f"Project not found for id={project_id}")

        return ProjectDetailResponse(ok=True, **project_row)
    except ProjectNotFoundError as error:
        return _not_found_response(f"GET /projects/{project_id}", error)
    except ProjectPersistenceError as error:
        return persistence_error_response(f"GET /projects/{project_id}", error)


@projects_router.patch("/{project_id}", response_model=ProjectDetailResponse)
def update_project(project_id: int, req: ProjectUpdateRequest) -> ProjectDetailResponse | JSONResponse:
    """Update mutable project metadata such as name or branch.

    Args:
        project_id: Persisted project identifier requested by the client.
        req: Validated update payload containing mutable project fields.

    Returns:
        ProjectDetailResponse | JSONResponse: Updated project detail payload or an error response.
    """
    project_persistence = ProjectPersistence()
    try:
        project_row = project_persistence.update_project(
            project_id,
            name=req.name,
            branch=req.branch,
        )
        if project_row is None:
            raise ProjectNotFoundError(f"Project not found for id={project_id}")

        return ProjectDetailResponse(ok=True, **project_row)
    except ProjectNotFoundError as error:
        return _not_found_response(f"PATCH /projects/{project_id}", error)
    except ProjectPersistenceError as error:
        return persistence_error_response(f"PATCH /projects/{project_id}", error)


@projects_router.get("/{project_id}/messages", response_model=ProjectMessagesResponse)
def list_project_messages(
    project_id: int,
    limit: int | None = Query(default=None, ge=1),
    before_sequence_no: int | None = Query(default=None, ge=1),
    after_sequence_no: int | None = Query(default=None, ge=1),
    branch: str | None = Query(default=None),
) -> ProjectMessagesResponse | JSONResponse:
    """List ordered project message history for a route consumer.

    Args:
        project_id: Persisted project identifier requested by the client.
        limit: Optional maximum number of history rows to return.
        before_sequence_no: Optional upper sequence boundary for older rows.
        after_sequence_no: Optional lower sequence boundary for newer rows.
        branch: Optional branch override used while binding the route runtime.

    Returns:
        ProjectMessagesResponse | JSONResponse: Ordered history payload or an error response.
    """
    route_label = f"GET /projects/{project_id}/messages"
    try:
        with bound_project_route_runtime(project_id, branch_override=branch) as handle:
            history_rows = handle.require_message_runtime().list_history(
                limit=limit,
                before_sequence_no=before_sequence_no,
                after_sequence_no=after_sequence_no,
            )
            return ProjectMessagesResponse(
                ok=True,
                project_id=project_id,
                branch=handle.branch,
                messages=history_rows,
            )
    except ProjectNotFoundError as error:
        return _not_found_response(route_label, error)
    except (ProjectResolutionError, ProjectRuntimeBindingError, MessageRuntimeError) as error:
        return _runtime_error_response(route_label, error)


@projects_router.get("/{project_id}/repository/tree", response_model=RepositoryTreeResponse)
def get_repository_tree(
    project_id: int,
    path: str | None = Query(default=None),
    branch: str | None = Query(default=None),
) -> RepositoryTreeResponse | JSONResponse:
    """List live repository tree entries for the requested project path.

    Args:
        project_id: Persisted project identifier requested by the client.
        path: Optional repo-relative directory path to list from.
        branch: Optional branch override used while binding the route runtime.

    Returns:
        RepositoryTreeResponse | JSONResponse: Tree-entry payload or an error response.
    """
    route_label = f"GET /projects/{project_id}/repository/tree"
    try:
        with bound_project_route_runtime(project_id, branch_override=branch) as handle:
            tree_entries = handle.require_file_runtime().list_tree(relative_repo_path=path)
            return RepositoryTreeResponse(
                ok=True,
                project_id=project_id,
                branch=handle.branch,
                path=path or "/",
                entries=tree_entries,
            )
    except ProjectNotFoundError as error:
        return _not_found_response(route_label, error)
    except (ProjectResolutionError, ProjectRuntimeBindingError) as error:
        return _runtime_error_response(route_label, error)
    except FileRuntimeError as error:
        status_code = 404 if "does not exist in branch" in str(error) or "is not a directory" in str(error) else 400
        return _runtime_error_response(route_label, error, status_code=status_code)


@projects_router.get("/{project_id}/repository/file", response_model=RepositoryFileResponse)
def get_repository_file(
    project_id: int,
    path: str = Query(...),
    branch: str | None = Query(default=None),
    start_line: int | None = Query(default=None, ge=1),
    number_of_lines: int | None = Query(default=None, ge=1),
    end_line: int | None = Query(default=None, ge=1),
) -> RepositoryFileResponse | JSONResponse:
    """Read live file content for the requested project path and line range.

    Args:
        project_id: Persisted project identifier requested by the client.
        path: Required repo-relative file path to read.
        branch: Optional branch override used while binding the route runtime.
        start_line: Optional first line number to include.
        number_of_lines: Optional count of lines to include from `start_line`.
        end_line: Optional inclusive last line number to include.

    Returns:
        RepositoryFileResponse | JSONResponse: File-content payload or an error response.
    """
    route_label = f"GET /projects/{project_id}/repository/file"
    normalized_path = str(path).strip()
    if not normalized_path:
        return error_response(status_code=400, error_code="INVALID_REQUEST", message="path is required", field="path")

    try:
        with bound_project_route_runtime(project_id, branch_override=branch) as handle:
            file_row = handle.require_file_runtime().read_file(
                relative_repo_path=normalized_path,
                start_line=start_line,
                number_of_lines=number_of_lines,
                end_line=end_line,
            )
            return RepositoryFileResponse(ok=True, project_id=project_id, branch=handle.branch, **file_row)
    except ProjectNotFoundError as error:
        return _not_found_response(route_label, error)
    except (ProjectResolutionError, ProjectRuntimeBindingError) as error:
        return _runtime_error_response(route_label, error)
    except FileRuntimeError as error:
        status_code = 404 if "does not exist in branch" in str(error) or "is not a file" in str(error) else 400
        return _runtime_error_response(route_label, error, status_code=status_code)


@projects_router.get("/{project_id}/repository/search", response_model=RepositorySearchResponse)
def search_repository_text(
    project_id: int,
    query: str = Query(...),
    path: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    case_sensitive: bool = Query(default=False),
    max_results: int = Query(default=100, ge=1),
) -> RepositorySearchResponse | JSONResponse:
    """Search live repository text for the requested project and optional path.

    Args:
        project_id: Persisted project identifier requested by the client.
        query: Required text query to search for.
        path: Optional repo-relative path to limit the search scope.
        branch: Optional branch override used while binding the route runtime.
        case_sensitive: Whether the text search should preserve letter case.
        max_results: Maximum number of search matches to return.

    Returns:
        RepositorySearchResponse | JSONResponse: Search-result payload or an error response.
    """
    route_label = f"GET /projects/{project_id}/repository/search"
    normalized_query = str(query).strip()
    if not normalized_query:
        return error_response(status_code=400, error_code="INVALID_REQUEST", message="query is required", field="query")

    try:
        with bound_project_route_runtime(project_id, branch_override=branch) as handle:
            matches = handle.require_file_runtime().search_text(
                query=normalized_query,
                relative_repo_path=path,
                case_sensitive=case_sensitive,
                max_results=max_results,
            )
            return RepositorySearchResponse(
                ok=True,
                project_id=project_id,
                branch=handle.branch,
                query=normalized_query,
                matches=matches,
            )
    except ProjectNotFoundError as error:
        return _not_found_response(route_label, error)
    except (ProjectResolutionError, ProjectRuntimeBindingError) as error:
        return _runtime_error_response(route_label, error)
    except FileRuntimeError as error:
        status_code = 404 if "does not exist in branch" in str(error) else 400
        return _runtime_error_response(route_label, error, status_code=status_code)


@projects_router.post("/{project_id}/run", response_model=ChatResponse)
def run_project_chat(project_id: int, req: ChatRequest) -> ChatResponse | JSONResponse:
    """Run one project-scoped chat execution against the bound runtime.

    Args:
        project_id: Persisted project identifier requested by the client.
        req: Validated chat-run payload including message, selected files, and optional model/branch.

    Returns:
        ChatResponse | JSONResponse: Execution result payload or an error response.
    """
    route_label = f"POST /projects/{project_id}/run"
    if not str(req.message).strip():
        return error_response(status_code=400, error_code="INVALID_REQUEST", message="message is required", field="message")

    if req.branch is not None and not str(req.branch).strip():
        return error_response(status_code=400, error_code="INVALID_REQUEST", message="branch must not be blank", field="branch")

    if req.ai_model_name is not None and not str(req.ai_model_name).strip():
        return error_response(
            status_code=400,
            error_code="INVALID_REQUEST",
            message="ai_model_name must not be blank",
            field="ai_model_name",
        )

    try:
        with bound_project_execution_runtime(project_id, branch_override=req.branch) as handle:
            result = build_workflow_orchestrator().run_chat(
                handle=handle,
                message=req.message,
                selected_files=req.selected_files,
                ai_model_name=req.ai_model_name,
            )
            return ChatResponse(
                ok=result.get("ok", False),
                project_id=project_id,
                message=result.get("answer", result.get("message", "")),
                selected_files=req.selected_files,
                branch=handle.branch,
                ai_model_name=result.get("ai_model_name") or "",
                execution_type=result.get("execution_type"),
                return_to_user=result.get("return_to_user"),
            )
    except ProjectNotFoundError as error:
        return _not_found_response(route_label, error)
    except (ProjectResolutionError, ProjectRuntimeBindingError, WorkflowExecutionError) as error:
        return _runtime_error_response(route_label, error)
