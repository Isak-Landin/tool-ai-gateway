from flask import Flask

from webapp.config import Config
from webapp.navigation import build_navigation_context
from webapp.routes import register_blueprints


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        static_url_path="/static",
    )
    app.config.from_object(Config)

    register_blueprints(app)

    @app.context_processor
    def inject_shell_context():
        return build_navigation_context()

    return app
