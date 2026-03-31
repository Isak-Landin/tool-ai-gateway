from flask import Flask

from webapp.routes.account import account_bp
from webapp.routes.app_pages import app_pages_bp
from webapp.routes.project import project_bp
from webapp.routes.projects import projects_bp
from webapp.routes.public import public_bp
from webapp.routes.support import support_bp
from webapp.routes.ui_api import ui_api_bp

BLUEPRINTS = (
    ui_api_bp,
    public_bp,
    app_pages_bp,
    projects_bp,
    account_bp,
    project_bp,
    support_bp,
)


def register_blueprints(app: Flask) -> None:
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)


__all__ = ["BLUEPRINTS", "register_blueprints"]
