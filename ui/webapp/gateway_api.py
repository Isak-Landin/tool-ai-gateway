from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from flask import current_app


@dataclass(frozen=True)
class GatewayResponse:
    status_code: int
    payload: dict[str, Any]

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


class GatewayUnavailableError(RuntimeError):
    """Raised when the UI cannot reach the gateway backend."""


def perform_gateway_request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    timeout: int = 30,
) -> GatewayResponse:
    normalized_path = str(path).strip()
    if not normalized_path.startswith("/"):
        normalized_path = f"/{normalized_path}"

    GATEWAY_URL = str(current_app.config["GATEWAY_URL"]).rstrip("/")
    gateway_url = f"{GATEWAY_URL}{normalized_path}"

    try:
        response = requests.request(
            method=method.upper(),
            url=gateway_url,
            params=params,
            json=json_body,
            timeout=timeout,
        )
    except requests.RequestException as error:
        raise GatewayUnavailableError("UI could not reach the gateway backend.") from error

    try:
        payload = response.json()
    except ValueError as error:
        raise GatewayUnavailableError("Gateway returned a non-JSON response.") from error

    if not isinstance(payload, dict):
        raise GatewayUnavailableError("Gateway returned an unexpected response shape.")

    return GatewayResponse(status_code=response.status_code, payload=payload)


def gateway_message(response: GatewayResponse, fallback: str) -> str:
    payload_message = response.payload.get("message")
    if isinstance(payload_message, str) and payload_message.strip():
        return payload_message

    return fallback
