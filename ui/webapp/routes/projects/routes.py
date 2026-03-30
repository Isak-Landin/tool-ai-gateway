from flask import Blueprint, render_template

projects_bp = Blueprint("projects_pages", __name__)


@projects_bp.get("/projects")
def projects():
    return render_template("pages/projects/index.html")


@projects_bp.get("/projects/new")
def create_project():
    return render_template("pages/projects/create.html")


@projects_bp.get("/projects/bootstrap-complete")
def bootstrap_complete():
    return render_template("pages/projects/bootstrap_complete.html")
