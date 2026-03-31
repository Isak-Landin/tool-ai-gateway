from flask import Blueprint, render_template

projects_bp = Blueprint("projects_pages", __name__)

@projects_bp.get("/projects")
def projects():
    """
    TODO
    We need to insert ui backend communication with the api.
    It's possible we do not insert it here directly, instead we will create new projects
    specific routes rersponsible for serving the js.
    """
    return render_template("pages/projects/index.html")


@projects_bp.get("/projects/new")
def create_project():
    """
    TODO
    We need to insert ui backend communication with the api.
    It's possible we do not insert it here directly, instead we will create new projects
    specific routes rersponsible for serving the js.
    """
    return render_template("pages/projects/create.html")


@projects_bp.get("/projects/bootstrap-complete")
def bootstrap_complete():
    """
    TODO
    We need to insert ui backend communication with the api.
    It's possible we do not insert it here directly, instead we will create new projects
    specific routes rersponsible for serving the js.
    """
    return render_template("pages/projects/bootstrap_complete.html")
