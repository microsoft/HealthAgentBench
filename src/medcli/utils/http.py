"""Shared HTTP helpers with lightweight retry behavior."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class HttpRetryPolicy:
    attempts: int = 3
    base_backoff_s: float = 0.5
    retry_statuses: tuple[int, ...] = (408, 409, 425, 429, 500, 502, 503, 504)


class HttpRequestError(RuntimeError):
    """Raised when an HTTP request fails after retries."""

    def __init__(
        self, message: str, *, status_code: int | None = None, body: str | None = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class JsonHttpClient:
    """Small JSON-focused HTTP client wrapper."""

    def __init__(
        self,
        *,
        timeout_s: float = 30.0,
        retry_policy: HttpRetryPolicy | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout_s = timeout_s
        self.retry_policy = retry_policy or HttpRetryPolicy()
        self._session = session or requests.Session()

    def request_json(
        self,
        *,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        last_error: Exception | None = None

        for attempt in range(1, self.retry_policy.attempts + 1):
            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_body,
                    headers=headers,
                    timeout=self.timeout_s,
                )
            except requests.RequestException as exc:
                last_error = exc
                if attempt == self.retry_policy.attempts:
                    break
                self._sleep_backoff(attempt)
                continue

            if response.ok:
                return self._decode_json_or_raise(
                    response.text, response.status_code, url
                )

            if (
                response.status_code in self.retry_policy.retry_statuses
                and attempt < self.retry_policy.attempts
            ):
                self._sleep_backoff(attempt)
                continue

            raise HttpRequestError(
                f"HTTP {response.status_code} for {method} {url}",
                status_code=response.status_code,
                body=response.text,
            )

        raise HttpRequestError(
            f"HTTP request failed for {method} {url}: {last_error}",
        )

    def _sleep_backoff(self, attempt: int) -> None:
        time.sleep(self.retry_policy.base_backoff_s * (2 ** (attempt - 1)))

    @staticmethod
    def _decode_json_or_raise(text: str, status_code: int, url: str) -> dict[str, Any]:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:  # noqa: PERF203
            raise HttpRequestError(
                f"Non-JSON response for {url}",
                status_code=status_code,
                body=text,
            ) from exc
        if not isinstance(payload, dict):
            raise HttpRequestError(
                f"Expected JSON object response for {url}",
                status_code=status_code,
                body=text,
            )
        return payload
