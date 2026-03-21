import os
import requests
from flask import Flask, jsonify, render_template, request, redirect, url_for, message_flashed

app = Flask(__name__, template_folder="templates", static_folder="static")

# Load environment variables
GATEWAY_BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:8000").rstrip("/")
UI_HOST = os.getenv("UI_HOST", "0.0.0.0")
UI_PORT = int(os.getenv("UI_PORT", "4000"))

# Session/auth (for MVP, using simple session storage)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-prod")

class ErrorManagement(Exception):
    def __init__(self, error):
        super.__init__(error)



@app.route("/")
def index():
    """List all projects or show empty state."""
    try:
        response = requests.get(
            f"{GATEWAY_BASE_URL}/projects",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        projects = data.get("projects", []) if data.get("ok") else []
    except requests.RequestException as e:
        print(f"Error fetching projects: {e}")
        projects = []
        error_msg = "Failed to connect to gateway"
    else:
        error_msg = None

    return render_template(
        "projects_list.html",
        projects=projects,
        gateway_base_url=GATEWAY_BASE_URL,
        error_msg=error_msg
    )


@app.route("/projects/new", methods=["GET", "POST"])
def create_project():
    """Create a new project."""
    if request.method == "GET":
        return render_template("create_project.html", gateway_base_url=GATEWAY_BASE_URL)

    # Handle POST request
    data = request.get_json() if request.is_json else request.form.to_dict()

    try:
        response = requests.post(
            f"{GATEWAY_BASE_URL}/projects/create",
            json={
                "name": data.get("name"),
                "remote_repo_url": data.get("remote_repo_url"),
                "ssh_key": data.get("ssh_key"),
            },
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        print("Result that was processed: ", result)

        if result.get("ok"):
            # Redirect directly to project detail page
            project_id = result.get("project_id")
            return redirect(url_for('project_detail', project_id=project_id))
        else:
            return jsonify({
                "ok": False,
                "field": result.get("field"),
                "message": result.get("message", "Unknown error")
            }), 409

    except requests.RequestException as e:
        return jsonify({
            "ok": False,
            "error": f"Gateway connection failed: {str(e)}"
        }), 502


@app.route("/projects/<int:project_id>")
def project_detail(project_id):
    """Show project detail page (stub for MVP)."""
    try:
        response = requests.get(
            f"{GATEWAY_BASE_URL}/projects/{project_id}",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        project = data if data.get("ok") else None
    except requests.RequestException as e:
        print(f"Error fetching project {project_id}: {e}")
        project = None
        error_msg = "Failed to load project"
    else:
        error_msg = None

    if not project:
        return render_template(
            "error.html",
            message=error_msg or "Project not found",
            gateway_base_url=GATEWAY_BASE_URL
        ), 404

    return render_template(
        "project_detail.html",
        project=project,
        project_id=project_id,
        gateway_base_url=GATEWAY_BASE_URL
    )


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "ok": True,
        "gateway_url": GATEWAY_BASE_URL,
        "version": "1.0.0"
    })


if __name__ == "__main__":
    app.run(
        host=UI_HOST,
        port=UI_PORT,
        debug=os.getenv("FLASK_DEBUG", "true").lower() == "true"
    )