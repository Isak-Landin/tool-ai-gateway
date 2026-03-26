from flask import Blueprint, render_template

projects_bp = Blueprint("projects_pages", __name__)


@projects_bp.get("/projects")
def projects():
    sample_projects = [
        {"project_id": 14, "name": "Gateway UI", "status": "Active", "model": "qwen3:8b"},
        {"project_id": 22, "name": "Runtime Binder", "status": "Bootstrap pending", "model": "llama3.2"},
        {"project_id": 31, "name": "Execution MVP", "status": "Shared", "model": "qwen3:8b"},
    ]
    return render_template("pages/projects/index.html", projects=sample_projects)


@projects_bp.get("/projects/new")
def create_project():
    return render_template("pages/projects/create.html")


@projects_bp.get("/projects/shared")
def shared_projects():
    return render_template("pages/projects/shared.html")


@projects_bp.get("/projects/archived")
def archived_projects():
    return render_template("pages/projects/archived.html")


@projects_bp.get("/projects/bootstrap-complete")
def bootstrap_complete():
    return render_template("pages/projects/bootstrap_complete.html")
