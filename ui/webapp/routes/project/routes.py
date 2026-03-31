from __future__ import annotations

from flask import Blueprint, render_template

from webapp.gateway_api import GatewayUnavailableError, gateway_message, perform_gateway_request

project_bp = Blueprint("project", __name__, url_prefix="/projects/<int:project_id>")


def _render_not_found():
    return render_template("pages/support/404.html"), 404


def _render_unavailable():
    return render_template("pages/support/503.html"), 503


def _load_required_project(project_id: int):
    try:
        response = perform_gateway_request("GET", f"/projects/{project_id}")
    except GatewayUnavailableError:
        return None, _render_unavailable()

    if response.status_code == 404:
        return None, _render_not_found()

    if not response.ok:
        return None, _render_unavailable()

    return response.payload, None


def _load_optional_payload(
    method: str,
    path: str,
    *,
    params: dict[str, str] | None = None,
    fallback_message: str,
) -> tuple[dict | None, str | None]:
    try:
        response = perform_gateway_request(method, path, params=params)
    except GatewayUnavailableError as error:
        return None, str(error)

    if response.ok:
        return response.payload, None

    return None, gateway_message(response, fallback_message)

@project_bp.get("")
def workspace(project_id: int):
    project, error_response = _load_required_project(project_id)
    if error_response is not None:
        return error_response

    branch = str(project.get("branch") or "main")
    models_payload, model_error_message = _load_optional_payload(
        "GET",
        "/models",
        fallback_message="Failed to load backend model options.",
    )
    tree_payload, tree_error_message = _load_optional_payload(
        "GET",
        f"/projects/{project_id}/repository/tree",
        params={"branch": branch},
        fallback_message="Failed to load repository tree.",
    )
    messages_payload, chat_error_message = _load_optional_payload(
        "GET",
        f"/projects/{project_id}/messages",
        params={"branch": branch},
        fallback_message="Failed to load project history.",
    )

    model_options = list((models_payload or {}).get("models", []))
    model_default_model = str((models_payload or {}).get("default_model", "")).strip()
    model_default_selection = str((models_payload or {}).get("default_selection", "auto")).strip() or "auto"
    tree_entries = list((tree_payload or {}).get("entries", []))
    chat_messages = list((messages_payload or {}).get("messages", []))

    current_file = None
    current_file_lines: list[str] = []
    file_error_message = None
    first_file = next((entry for entry in tree_entries if entry.get("is_file")), None)
    if first_file is not None:
        file_payload, file_error_message = _load_optional_payload(
            "GET",
            f"/projects/{project_id}/repository/file",
            params={"branch": branch, "path": str(first_file.get("path", ""))},
            fallback_message="Failed to load file content.",
        )
        if file_payload is not None:
            current_file = file_payload
            current_file_lines = str(current_file.get("content", "")).split("\n")

    return render_template(
        "pages/project/workspace.html",
        project_id=project_id,
        project=project,
        model_options=model_options,
        model_default_model=model_default_model,
        model_default_selection=model_default_selection,
        model_error_message=model_error_message,
        tree_entries=tree_entries,
        tree_error_message=tree_error_message,
        chat_messages=chat_messages,
        chat_error_message=chat_error_message,
        current_file=current_file,
        current_file_lines=current_file_lines,
        file_error_message=file_error_message,
        ui_page_data={
            "project": project,
            "models": model_options,
            "defaultModel": model_default_model,
            "defaultSelection": model_default_selection,
            "treeEntries": tree_entries,
            "currentFilePath": current_file.get("path") if current_file else None,
        },
        project_page_label="Project Workspace",
        project_page_description="Repository, file, history, and run controls stay connected here.",
    )


@project_bp.get("/activity")
def activity(project_id: int):
    project, error_response = _load_required_project(project_id)
    if error_response is not None:
        return error_response

    branch = str(project.get("branch") or "main")
    messages_payload, chat_error_message = _load_optional_payload(
        "GET",
        f"/projects/{project_id}/messages",
        params={"branch": branch},
        fallback_message="Failed to load project history.",
    )
    chat_messages = list((messages_payload or {}).get("messages", []))

    return render_template(
        "pages/project/activity.html",
        project_id=project_id,
        project=project,
        chat_messages=chat_messages,
        chat_error_message=chat_error_message,
        ui_page_data={"project": project},
        project_page_label="Project Activity",
        project_page_description="Ordered message history and execution artifacts live here.",
    )


@project_bp.get("/settings")
def settings(project_id: int):
    project, error_response = _load_required_project(project_id)
    if error_response is not None:
        return error_response

    return render_template(
        "pages/project/settings.html",
        project_id=project_id,
        project=project,
        ui_page_data={"project": project},
        project_page_label="Project Settings",
        project_page_description="Only truly project-scoped fields should be edited here.",
    )
