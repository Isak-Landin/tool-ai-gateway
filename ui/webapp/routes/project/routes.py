from flask import Blueprint, render_template

project_bp = Blueprint("project", __name__, url_prefix="/projects/<int:project_id>")

@project_bp.get("")
def workspace(project_id: int):
    return render_template(
        "pages/project/workspace.html",
        project_id=project_id,
        project_page_label="Project Workspace",
        project_page_description="Repository, file, history, and run controls stay connected here.",
    )


@project_bp.get("/activity")
def activity(project_id: int):
    return render_template(
        "pages/project/activity.html",
        project_id=project_id,
        project_page_label="Project Activity",
        project_page_description="Ordered message history and execution artifacts live here.",
    )


@project_bp.get("/settings")
def settings(project_id: int):
    return render_template(
        "pages/project/settings.html",
        project_id=project_id,
        project_page_label="Project Settings",
        project_page_description="Only truly project-scoped fields should be edited here.",
    )
