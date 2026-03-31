from flask import Flask
from werkzeug.debug import DebuggedApplication

from webapp.config import Config
from webapp.formatting import format_timestamp
from webapp.navigation import build_navigation_context
from webapp.routes import register_blueprints
from webapp.trusted_hosts import TrustedHostMiddleware


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        static_url_path="/static",
    )
    app.config.from_object(Config)
    app.jinja_env.filters["datetime"] = format_timestamp
    trusted_hosts = list(app.config["UI_TRUSTED_HOSTS"])

    app.wsgi_app = TrustedHostMiddleware(app.wsgi_app, trusted_hosts)

    if app.config["DEBUG"]:
        debug_app = DebuggedApplication(app.wsgi_app, evalex=True)
        for trusted_host in trusted_hosts:
            if trusted_host not in debug_app.trusted_hosts:
                debug_app.trusted_hosts.append(trusted_host)
        app.wsgi_app = debug_app

    register_blueprints(app)

    @app.context_processor
    def inject_shell_context():
        context = build_navigation_context()
        context["app_name"] = app.config["APP_NAME"]
        return context

    return app
