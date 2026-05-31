"""Shared request/response utilities for sync and async clients."""

from __future__ import annotations

from typing import Any, TypeVar

import httpx

from .errors import KlaaroAPIError

DEFAULT_BASE_URL = "https://klaaro.ai/api/v1"

T = TypeVar("T")


def build_headers(api_key: str | None, idempotency_key: str | None = None) -> dict[str, str]:
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers


def build_params(mapping: dict[str, Any]) -> dict[str, str]:
    """Filter None values and coerce remaining to strings."""
    return {k: str(v) for k, v in mapping.items() if v is not None}


def raise_for_response(response: httpx.Response) -> None:
    """Parse and raise KlaaroAPIError for non-2xx responses."""
    if response.is_success:
        return
    try:
        body = response.json()
        err = body.get("error", {})
        code = err.get("code", "unknown_error")
        message = err.get("message", f"HTTP {response.status_code}")
        param = err.get("param")
        request_id = err.get("requestId")
    except Exception:
        code = "unknown_error"
        message = f"HTTP {response.status_code}"
        param = None
        request_id = None

    raise KlaaroAPIError(
        status=response.status_code,
        code=code,
        message=message,
        param=param,
        request_id=request_id,
    )
