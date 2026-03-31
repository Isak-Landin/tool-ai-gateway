from __future__ import annotations

from flask import Blueprint, jsonify, request, session, url_for

from webapp.gateway_api import GatewayUnavailableError, perform_gateway_request

ui_api_bp = Blueprint("ui_api", __name__, url_prefix="/ui/api")


def _json_response(payload: dict, status_code: int):
    return jsonify(payload), status_code


def _proxy_gateway(method: str, path: str):
    try:
        response = perform_gateway_request(
            method,
            path,
            params=request.args.to_dict(flat=True) or None,
            json_body=request.get_json(silent=True),
        )
    except GatewayUnavailableError as error:
        return _json_response(
            {"ok": False, "error_code": "GATEWAY_UNAVAILABLE", "message": str(error)},
            503,
        )

    return _json_response(response.payload, response.status_code)


@ui_api_bp.get("/projects")
def list_projects():
    return _proxy_gateway("GET", "/projects")


@ui_api_bp.post("/projects")
def create_project():
    try:
        response = perform_gateway_request(
            "POST",
            "/projects",
            json_body=request.get_json(silent=True),
        )
    except GatewayUnavailableError as error:
        return _json_response(
            {"ok": False, "error_code": "GATEWAY_UNAVAILABLE", "message": str(error)},
            503,
        )

    payload = dict(response.payload)
    if response.ok:
        session["latest_project_bootstrap_result"] = payload
        payload["redirect_url"] = url_for(
            "projects_pages.bootstrap_complete",
            project_id=payload.get("project_id"),
        )

    return _json_response(payload, response.status_code)


@ui_api_bp.get("/projects/<int:project_id>")
def get_project(project_id: int):
    return _proxy_gateway("GET", f"/projects/{project_id}")


@ui_api_bp.patch("/projects/<int:project_id>")
def update_project(project_id: int):
    return _proxy_gateway("PATCH", f"/projects/{project_id}")


@ui_api_bp.get("/projects/<int:project_id>/messages")
def list_project_messages(project_id: int):
    return _proxy_gateway("GET", f"/projects/{project_id}/messages")


@ui_api_bp.get("/projects/<int:project_id>/repository/tree")
def get_repository_tree(project_id: int):
    return _proxy_gateway("GET", f"/projects/{project_id}/repository/tree")


@ui_api_bp.get("/projects/<int:project_id>/repository/file")
def get_repository_file(project_id: int):
    return _proxy_gateway("GET", f"/projects/{project_id}/repository/file")


@ui_api_bp.get("/projects/<int:project_id>/repository/search")
def search_repository_text(project_id: int):
    return _proxy_gateway("GET", f"/projects/{project_id}/repository/search")


@ui_api_bp.post("/projects/<int:project_id>/run")
def run_project_chat(project_id: int):
    return _proxy_gateway("POST", f"/projects/{project_id}/run")


@ui_api_bp.get("/models")
def list_models():
    return _proxy_gateway("GET", "/models")
