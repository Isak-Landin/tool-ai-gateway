import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from errors import PersistenceError

logger = logging.getLogger(__name__)


def log_route_error(route_label: str, error: Exception) -> None:
    """Log an API error with the route label that triggered it.

    Args:
        route_label: Human-readable route identifier for the failing request.
        error: Raised exception instance to include in the log output.

    Returns:
        None: This helper logs the error and does not return data.
    """
    logger.exception("[API ERROR] %s", route_label, exc_info=error)


def error_response(
    *,
    status_code: int,
    error_code: str,
    message: str,
    field: str | None = None,
    extra: dict | None = None,
) -> JSONResponse:
    """Build a JSON-first API error response payload.

    Args:
        status_code: HTTP status code to send with the response.
        error_code: Stable application error code for the client payload.
        message: Human-readable error message for the client.
        field: Optional request field name related to the error.
        extra: Optional extra payload fields to merge into the response body.

    Returns:
        JSONResponse: Structured error payload with `ok=False` and error metadata.
    """
    content = {
        "ok": False,
        "error_code": error_code,
        "message": message,
    }
    if field is not None:
        content["field"] = field
    if extra:
        content.update(extra)

    return JSONResponse(status_code=status_code, content=content)


def persistence_error_response(route_label: str, error: PersistenceError) -> JSONResponse:
    """Translate a persistence-layer error into the API error contract.

    Args:
        route_label: Human-readable route identifier for logging.
        error: Persistence-shaped error carrying message and error-type metadata.

    Returns:
        JSONResponse: JSON error payload mapped from the persistence error shape.
    """
    log_route_error(route_label, error)

    error_type = getattr(error, "error_type", None)
    if error_type == "duplicate":
        status_code = 409
        error_code = "DUPLICATE_FIELD"
    elif error_type in {"missing value", "missing project id"}:
        status_code = 400
        error_code = "INVALID_REQUEST"
    elif error_type == "missing configuration":
        status_code = 500
        error_code = "CONFIGURATION_ERROR"
    else:
        status_code = 500
        error_code = "PERSISTENCE_ERROR"

    return error_response(
        status_code=status_code,
        error_code=error_code,
        message=error.message,
        field=getattr(error, "field", None),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register shared exception handlers on the FastAPI application.

    Args:
        app: FastAPI application that should own the handlers.

    Returns:
        None: The handlers are attached to `app` in place.
    """
    @app.exception_handler(RequestValidationError)
    async def _handle_request_validation_error(  # noqa: ANN202
        request: Request,
        error: RequestValidationError,
    ):
        """Convert request validation failures into the shared JSON error shape.

        Args:
            request: Incoming FastAPI request that failed validation.
            error: Validation exception containing field-level error details.

        Returns:
            JSONResponse: Validation-error payload for the client.
        """
        log_route_error(f"{request.method} {request.url.path}", error)
        return error_response(
            status_code=422,
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            extra={"details": error.errors()},
        )

    @app.exception_handler(HTTPException)
    async def _handle_http_exception(  # noqa: ANN202
        request: Request,
        error: HTTPException,
    ):
        """Convert FastAPI HTTP exceptions into the shared JSON error shape.

        Args:
            request: Incoming FastAPI request that raised the HTTP exception.
            error: HTTP exception carrying status code and detail content.

        Returns:
            JSONResponse: HTTP-error payload for the client.
        """
        detail = error.detail if isinstance(error.detail, str) else "HTTP error"
        log_route_error(f"{request.method} {request.url.path}", error)
        return error_response(
            status_code=error.status_code,
            error_code="HTTP_ERROR",
            message=detail,
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected_exception(  # noqa: ANN202
        request: Request,
        error: Exception,
    ):
        """Convert unexpected backend failures into the shared JSON error shape.

        Args:
            request: Incoming FastAPI request that triggered the failure.
            error: Unexpected exception instance raised during request handling.

        Returns:
            JSONResponse: Internal-error payload for the client.
        """
        log_route_error(f"{request.method} {request.url.path}", error)
        return error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="Internal server error",
        )
