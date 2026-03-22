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

@app.before_request
def before():
    print(f"[REQ IN] {request.method} {request.path}")

@app.after_request
def after(response):
    print(f"[REQ OUT] {request.method} {request.path} -> {response.status})")
    return response


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

    data = request.get_json() if request.is_json else request.form.to_dict()

    try:
        response = requests.post(
            f"{GATEWAY_BASE_URL}/projects",
            json={
                "name": data.get("name"),
                "remote_repo_url": data.get("remote_repo_url"),
                "ssh_key": data.get("ssh_key"),
            },
            timeout=10
        )

        try:
            result = response.json()
        except requests.exceptions.JSONDecodeError:
            return jsonify({
                "ok": False,
                "message": "Gateway returned invalid response format"
            }), 502

        if response.ok and result.get("ok") is True:
            # Redirect to newly created project
            project_id = result.get("project_id")
            return redirect(url_for('project_detail', project_id=project_id))

        elif not result.get("ok"):
            return jsonify({
                "ok": False,
                "field": result.get("field"),
                "error_code": result.get("error_code"),
                "message": result.get("message", "Project creation failed")
            }), response.status_code
        else:
            return jsonify({
                "ok": False,
                "message": "Gateway returned unexpected response"
            }), 500

    except requests.exceptions.Timeout:
        return jsonify({
            "ok": False,
            "message": "Gateway request timed out"
        }), 504
    except requests.RequestException as e:
        return jsonify({
            "ok": False,
            "message": f"Gateway unavailable: {str(e)}"
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