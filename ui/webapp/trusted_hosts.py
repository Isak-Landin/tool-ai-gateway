from __future__ import annotations

from collections.abc import Iterable

from werkzeug.exceptions import SecurityError
from werkzeug.wsgi import get_host


class TrustedHostMiddleware:
    """Validate incoming request hosts against an allowed host list."""

    def __init__(self, app, trusted_hosts: Iterable[str]):
        """Create the trusted-host middleware.

        Args:
            app: Wrapped WSGI application to call after host validation succeeds.
            trusted_hosts: Allowed host patterns for incoming requests.

        Returns:
            None: The middleware stores the wrapped app and normalized hosts.
        """
        self.app = app
        self.trusted_hosts = [host for host in trusted_hosts if str(host).strip()]

    def __call__(self, environ, start_response):
        """Validate the request host before delegating to the wrapped app.

        Args:
            environ: WSGI environment for the incoming request.
            start_response: WSGI response starter callback.

        Returns:
            Any: The wrapped application response when the host is trusted.
        """
        try:
            get_host(environ, trusted_hosts=self.trusted_hosts)
        except SecurityError as error:
            return error(environ, start_response)

        return self.app(environ, start_response)
