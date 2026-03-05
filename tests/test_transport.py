from __future__ import annotations

import asyncio
import httpx

from oa_sdk.config import RetryConfig
from oa_sdk.transport import AsyncHTTPTransport


class _FlakyAsyncClient:
    def __init__(self) -> None:
        self.calls = 0

    async def request(self, method: str, url: str, headers=None, json=None):  # noqa: ANN001, ANN202
        self.calls += 1
        request = httpx.Request(method, url, headers=headers, json=json)
        if self.calls == 1:
            raise httpx.ReadTimeout("timeout", request=request)
        return httpx.Response(200, request=request, json={"ok": True})


def test_async_transport_retries_with_async_sleep(monkeypatch) -> None:  # noqa: ANN001
    delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    async def run() -> None:
        monkeypatch.setattr("oa_sdk.transport.asyncio.sleep", fake_sleep)
        transport = AsyncHTTPTransport(
            timeout_seconds=1.0,
            retry=RetryConfig(max_attempts=2, base_delay_seconds=0.1, max_delay_seconds=0.1),
        )
        await transport._client.aclose()
        transport._client = _FlakyAsyncClient()  # type: ignore[assignment]

        result = await transport.request_json("GET", "https://example.test", context="async retry test")

        assert result.status_code == 200
        assert result.data == {"ok": True}
        assert delays == [0.1]

    asyncio.run(run())
