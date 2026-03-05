from __future__ import annotations

from typing import Mapping

from ..config import OAConfig
from ..errors import OAHTTPError
from ..models import OAResponse
from ..retry_policy import endpoint_retry_allowed
from ..transport import HTTPTransport
from .backends import (
    BackendKind,
    GeminiProviderDirectBackend,
    InferenceBackend,
    OpenResponsesBackend,
    OpenRouterEphemeralBackend,
)
from .gemini_live import GeminiLiveClient
from .models import AccessCredential, ResponseRequest


class InferenceService:
    """
    Unified inference surface inspired by OpenResponses-style API:
    `responses.create(...)` against pluggable backend kinds.
    """

    def __init__(self, *, config: OAConfig, transport: HTTPTransport) -> None:
        self._config = config
        self._transport = transport

    def create_response(
        self,
        request: ResponseRequest,
        *,
        backend: InferenceBackend,
        credential: AccessCredential | None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> OAResponse:
        method, url, headers, payload = backend.build_request(
            request,
            credential=credential,
            extra_headers=extra_headers,
        )

        result = self._transport.request_json(
            method,
            url,
            headers=headers,
            json_body=payload,
            allow_retry=endpoint_retry_allowed("inference"),
            context=f"inference backend {backend.id}",
        )

        if not (200 <= result.status_code < 300):
            message = _extract_error_message(result.data, result.text, result.status_code)
            raise OAHTTPError(result.status_code, message, detail=result.data)

        return backend.parse_response(result.data)

    def openrouter_ephemeral_backend(self, *, base_url: str | None = None) -> OpenRouterEphemeralBackend:
        return OpenRouterEphemeralBackend(base_url=base_url or self._config.openrouter_api_base)

    def gemini_provider_direct_backend(
        self,
        *,
        base_url: str | None = None,
    ) -> GeminiProviderDirectBackend:
        return GeminiProviderDirectBackend(base_url=base_url or self._config.gemini_openai_api_base)

    def provider_direct_backend(
        self,
        *,
        base_url: str,
        endpoint: str = "/v1/responses",
    ) -> OpenResponsesBackend:
        return OpenResponsesBackend(
            base_url=base_url,
            kind=BackendKind.PROVIDER_DIRECT,
            id="provider-direct",
            endpoint=endpoint,
        )

    def openai_provider_direct_backend(
        self,
        *,
        base_url: str | None = None,
    ) -> OpenResponsesBackend:
        return OpenResponsesBackend(
            base_url=base_url or self._config.openai_api_base,
            kind=BackendKind.PROVIDER_DIRECT,
            id="openai-provider-direct",
            endpoint="/v1/responses",
        )

    def tee_gateway_backend(
        self,
        *,
        base_url: str,
        endpoint: str = "/v1/responses",
        extra_headers: Mapping[str, str] | None = None,
    ) -> OpenResponsesBackend:
        # Gateway request contract is still evolving; keep this as an explicit
        # backend target now so clients can adopt it once gateway is live.
        return OpenResponsesBackend(
            base_url=base_url,
            kind=BackendKind.TEE_GATEWAY,
            id="tee-gateway",
            endpoint=endpoint,
            extra_headers=extra_headers or {},
        )

    def gemini_live_client(
        self,
        *,
        api_key: str,
        api_version: str | None = None,
    ) -> GeminiLiveClient:
        return GeminiLiveClient(
            api_key=api_key,
            api_version=api_version or self._config.gemini_live_api_version,
        )


def _extract_error_message(data: object, text: str, status_code: int) -> str:
    if isinstance(data, Mapping):
        for key in ("detail", "error", "message"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value
    if text:
        return text
    return f"HTTP {status_code}"
