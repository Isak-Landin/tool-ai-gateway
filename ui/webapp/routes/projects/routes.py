from flask import Blueprint, render_template, request, session

from webapp.gateway_api import GatewayUnavailableError, gateway_message, perform_gateway_request

projects_bp = Blueprint("projects_pages", __name__)

@projects_bp.get("/projects")
def projects():
    projects_list: list[dict] = []
    projects_error: str | None = None
    status_code = 200

    try:
        response = perform_gateway_request("GET", "/projects")
        if response.ok:
            projects_list = list(response.payload.get("projects", []))
        else:
            projects_error = gateway_message(response, "Failed to load projects.")
            status_code = response.status_code
    except GatewayUnavailableError as error:
        projects_error = str(error)
        status_code = 503

    return render_template(
        "pages/projects/index.html",
        projects=projects_list,
        projects_error=projects_error,
    ), status_code


@projects_bp.get("/projects/new")
def create_project():
    return render_template("pages/projects/create.html")


@projects_bp.get("/projects/bootstrap-complete")
def bootstrap_complete():
    expected_project_id = str(request.args.get("project_id", "")).strip()
    bootstrap_result = session.get("latest_project_bootstrap_result")
    bootstrap_error: str | None = None
    status_code = 200

    if not isinstance(bootstrap_result, dict):
        bootstrap_result = None
        bootstrap_error = "No recent bootstrap result is available in the current UI session."
        status_code = 404
    elif expected_project_id and str(bootstrap_result.get("project_id")) != expected_project_id:
        bootstrap_result = None
        bootstrap_error = "The stored bootstrap result does not match this project page."
        status_code = 404

    return render_template(
        "pages/projects/bootstrap_complete.html",
        bootstrap_result=bootstrap_result,
        bootstrap_error=bootstrap_error,
    ), status_code
