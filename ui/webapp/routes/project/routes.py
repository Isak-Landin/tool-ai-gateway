from flask import Blueprint, render_template

project_bp = Blueprint("project", __name__, url_prefix="/projects/<int:project_id>")


def _project_shell(project_id: int) -> dict:
    return {
        "project_id": project_id,
        "name": f"Project {project_id}",
        "active_branch": "main",
        "active_model": "qwen3:8b",
    }


@project_bp.get("")
def workspace(project_id: int):
    project = _project_shell(project_id)
    repo_tree = [
        {"label": "README.md", "type": "file"},
        {"label": "api.py", "type": "file"},
        {
            "label": "execution",
            "type": "directory",
            "children": [
                {"label": "workflow_orchestrator.py", "type": "file"},
                {"label": "runtime_execution.md", "type": "file"},
            ],
        },
        {
            "label": "ui",
            "type": "directory",
            "children": [
                {"label": "UI_INTENT.md", "type": "file"},
            ],
        },
    ]
    chat_entries = [
        {"role": "user", "label": "You", "content": "Map the UI workspace for this project."},
        {
            "role": "assistant",
            "label": "Model",
            "content": "The workspace should keep repository tree, central presenter, and chat controls visible together.",
            "thought": "Reason about one integrated project page before splitting into secondary pages.",
        },
    ]
    return render_template(
        "pages/project/workspace.html",
        project=project,
        repo_tree=repo_tree,
        chat_entries=chat_entries,
        models=["qwen3:8b", "llama3.2", "gpt-oss:latest"],
        branches=["main", "develop", "feature/ui-structure"],
    )


@project_bp.get("/activity")
def activity(project_id: int):
    return render_template("pages/project/activity.html", project=_project_shell(project_id))


@project_bp.get("/settings")
def settings(project_id: int):
    return render_template("pages/project/settings.html", project=_project_shell(project_id))
