from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import random
import time
from email.utils import parsedate_to_datetime
from typing import Any, Mapping

import httpx

from .config import RetryConfig
from .errors import OAHTTPError, OARetryExhaustedError


@dataclass
class TransportResult:
    status_code: int
    data: Any
    text: str
    headers: Mapping[str, str]


class HTTPTransport:
    def __init__(self, *, timeout_seconds: float, retry: RetryConfig) -> None:
        self._timeout_seconds = timeout_seconds
        self._retry = retry
        self._client = httpx.Client(timeout=timeout_seconds)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HTTPTransport:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def request_json(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        json_body: Mapping[str, Any] | None = None,
        allow_retry: bool = True,
        context: str = "request",
    ) -> TransportResult:
        attempts = self._retry.max_attempts if allow_retry else 1
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                response = self._client.request(method, url, headers=headers, json=json_body)
                text = response.text
                data = _safe_parse_json(response)

                if response.status_code in self._retry.retryable_status_codes and attempt < attempts:
                    _sleep_backoff(
                        attempt=attempt,
                        response=response,
                        retry=self._retry,
                    )
                    continue

                return TransportResult(
                    status_code=response.status_code,
                    data=data,
                    text=text,
                    headers=dict(response.headers),
                )
            except httpx.RequestError as exc:
                last_error = exc
                if attempt >= attempts:
                    break
                _sleep_backoff(attempt=attempt, response=None, retry=self._retry)

        if last_error is not None:
            raise OARetryExhaustedError(f"{context} failed after {attempts} attempts: {last_error}")
        raise OARetryExhaustedError(f"{context} failed after {attempts} attempts")


class AsyncHTTPTransport:
    def __init__(self, *, timeout_seconds: float, retry: RetryConfig) -> None:
        self._timeout_seconds = timeout_seconds
        self._retry = retry
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncHTTPTransport:
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.aclose()

    async def request_json(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        json_body: Mapping[str, Any] | None = None,
        allow_retry: bool = True,
        context: str = "request",
    ) -> TransportResult:
        attempts = self._retry.max_attempts if allow_retry else 1
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                response = await self._client.request(method, url, headers=headers, json=json_body)
                text = response.text
                data = _safe_parse_json(response)

                if response.status_code in self._retry.retryable_status_codes and attempt < attempts:
                    _sleep_backoff(
                        attempt=attempt,
                        response=response,
                        retry=self._retry,
                    )
                    continue

                return TransportResult(
                    status_code=response.status_code,
                    data=data,
                    text=text,
                    headers=dict(response.headers),
                )
            except httpx.RequestError as exc:
                last_error = exc
                if attempt >= attempts:
                    break
                _sleep_backoff(attempt=attempt, response=None, retry=self._retry)

        if last_error is not None:
            raise OARetryExhaustedError(f"{context} failed after {attempts} attempts: {last_error}")
        raise OARetryExhaustedError(f"{context} failed after {attempts} attempts")


def ensure_success(result: TransportResult, *, context: str) -> None:
    if 200 <= result.status_code < 300:
        return

    detail: object | None = result.data
    message: str
    if isinstance(result.data, dict):
        message = (
            str(result.data.get("detail") or result.data.get("error") or result.data.get("message") or "")
            or f"HTTP {result.status_code}"
        )
    elif result.text:
        message = result.text
    else:
        message = f"HTTP {result.status_code}"

    raise OAHTTPError(result.status_code, f"{context} failed: {message}", detail=detail)


def _safe_parse_json(response: httpx.Response) -> Any:
    content_type = response.headers.get("content-type", "")
    text = response.text
    if not text:
        return None
    if "application/json" in content_type or text[:1] in "[{":
        try:
            return response.json()
        except ValueError:
            return None
    return None


def _sleep_backoff(*, attempt: int, response: httpx.Response | None, retry: RetryConfig) -> None:
    retry_after_seconds = _parse_retry_after(response.headers.get("Retry-After") if response else None)
    if retry_after_seconds is not None:
        delay = min(retry_after_seconds, retry.max_delay_seconds)
    else:
        exp = retry.base_delay_seconds * (2 ** (attempt - 1))
        jitter = random.random() * retry.base_delay_seconds
        delay = min(exp + jitter, retry.max_delay_seconds)

    if delay > 0:
        time.sleep(delay)


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None

    value = value.strip()
    if not value:
        return None

    try:
        seconds = float(value)
        return seconds if seconds > 0 else None
    except ValueError:
        pass

    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = (dt - datetime.now(timezone.utc)).total_seconds()
        return delta if delta > 0 else None
    except (TypeError, ValueError):
        return None
