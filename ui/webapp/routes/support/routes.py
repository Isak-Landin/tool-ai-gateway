from flask import Blueprint, render_template

support_bp = Blueprint("support", __name__)


@support_bp.get("/403")
def forbidden():
    return render_template("pages/support/403.html"), 403


@support_bp.get("/404")
def not_found():
    return render_template("pages/support/404.html"), 404


@support_bp.get("/503")
def unavailable():
    return render_template("pages/support/503.html"), 503


@support_bp.get("/support/empty-states")
def empty_states():
    return render_template("pages/support/empty_states.html")
