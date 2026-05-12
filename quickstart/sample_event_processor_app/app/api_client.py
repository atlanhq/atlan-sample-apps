"""Calls a public hello-world API.

Default endpoint is ``https://httpbin.org/anything`` which echoes back the
request body — perfect for a demo. Override via ``HELLO_API_URL`` env var.
"""

from __future__ import annotations

import os

import httpx

_DEFAULT_URL = "https://httpbin.org/anything"


class HelloApiCaller:
    """Thin async wrapper around an example HTTP API."""

    def __init__(self, url: str | None = None, timeout_seconds: float = 10.0) -> None:
        self._url = url or os.environ.get("HELLO_API_URL", _DEFAULT_URL)
        self._timeout = timeout_seconds

    async def call(self, event_id: str, payload: str) -> int:
        """POST the event to the API; return the HTTP status code."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self._url,
                json={"event_id": event_id, "payload": payload},
            )
            return response.status_code
