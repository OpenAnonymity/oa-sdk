from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, Protocol, runtime_checkable

from ..errors import BackendError, OAProtocolError
from ..models import OAResponse
from .models import AccessCredential, ResponseRequest


class BackendKind(str, Enum):
    EPHEMERAL_KEY = "ephemeral_key"
    PROVIDER_DIRECT = "provider_direct"
    TEE_GATEWAY = "tee_gateway"


@runtime_checkable
class InferenceBackend(Protocol):
    id: str
    kind: BackendKind

    def build_request(
        self,
        request: ResponseRequest,
        *,
        credential: AccessCredential | None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> tuple[str, str, Dict[str, str], Dict[str, Any]]:
        ...

    def parse_response(self, data: object) -> OAResponse:
        ...


@dataclass(frozen=True)
class OpenRouterEphemeralBackend:
    base_url: str
    id: str = "openrouter"
    kind: BackendKind = BackendKind.EPHEMERAL_KEY

    def build_request(
        self,
        request: ResponseRequest,
        *,
        credential: AccessCredential | None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> tuple[str, str, Dict[str, str], Dict[str, Any]]:
        if credential is None:
            raise BackendError("Ephemeral backend requires access credential")

        headers: Dict[str, str] = {"Content-Type": "application/json"}
        credential.apply(headers)
        if extra_headers:
            headers.update(extra_headers)

        payload: Dict[str, Any] = {
            "model": request.model,
            "messages": request.as_messages(),
            "stream": request.stream,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_output_tokens is not None:
            payload["max_output_tokens"] = request.max_output_tokens
        payload.update(request.extra)

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        return "POST", url, headers, payload

    def parse_response(self, data: object) -> OAResponse:
        if not isinstance(data, Mapping):
            raise OAProtocolError("OpenRouter response is not an object")

        response_id = data.get("id") if isinstance(data.get("id"), str) else None
        output_text: str | None = None
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, Mapping):
                message = first.get("message")
                if isinstance(message, Mapping):
                    content = message.get("content")
                    if isinstance(content, str):
                        output_text = content

        return OAResponse(response_id=response_id, output_text=output_text, raw=data)


@dataclass(frozen=True)
class GeminiProviderDirectBackend:
    base_url: str
    id: str = "gemini-provider-direct"
    kind: BackendKind = BackendKind.PROVIDER_DIRECT

    def build_request(
        self,
        request: ResponseRequest,
        *,
        credential: AccessCredential | None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> tuple[str, str, Dict[str, str], Dict[str, Any]]:
        if credential is None:
            raise BackendError("Gemini provider-direct backend requires access credential")

        headers: Dict[str, str] = {"Content-Type": "application/json"}
        credential.apply(headers)
        if extra_headers:
            headers.update(extra_headers)

        payload: Dict[str, Any] = {
            "model": request.model,
            "messages": request.as_messages(),
            "stream": request.stream,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_output_tokens is not None:
            payload["max_output_tokens"] = request.max_output_tokens
        payload.update(request.extra)

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        return "POST", url, headers, payload

    def parse_response(self, data: object) -> OAResponse:
        if not isinstance(data, Mapping):
            raise OAProtocolError("Gemini provider-direct response is not an object")

        response_id = data.get("id") if isinstance(data.get("id"), str) else None
        output_text: str | None = None
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, Mapping):
                message = first.get("message")
                if isinstance(message, Mapping):
                    content = message.get("content")
                    if isinstance(content, str):
                        output_text = content

        return OAResponse(response_id=response_id, output_text=output_text, raw=data)


@dataclass(frozen=True)
class OpenResponsesBackend:
    base_url: str
    kind: BackendKind
    id: str
    endpoint: str = "/v1/responses"
    default_auth_header: str = "Authorization"
    default_auth_prefix: str = "Bearer "
    extra_headers: Mapping[str, str] = field(default_factory=dict)

    def build_request(
        self,
        request: ResponseRequest,
        *,
        credential: AccessCredential | None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> tuple[str, str, Dict[str, str], Dict[str, Any]]:
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            **dict(self.extra_headers),
        }

        if credential is not None:
            credential.apply(headers)
        elif self.default_auth_header:
            raise BackendError(f"Backend '{self.id}' requires access credential")

        if extra_headers:
            headers.update(extra_headers)

        payload: Dict[str, Any] = {
            "model": request.model,
            "input": request.as_messages(),
            "stream": request.stream,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_output_tokens is not None:
            payload["max_output_tokens"] = request.max_output_tokens
        payload.update(request.extra)

        url = f"{self.base_url.rstrip('/')}{self.endpoint}"
        return "POST", url, headers, payload

    def parse_response(self, data: object) -> OAResponse:
        if not isinstance(data, Mapping):
            raise OAProtocolError("OpenResponses backend response is not an object")

        response_id = data.get("id") if isinstance(data.get("id"), str) else None
        output_text = _extract_openresponses_output_text(data)
        return OAResponse(response_id=response_id, output_text=output_text, raw=data)


def _extract_openresponses_output_text(data: Mapping[str, object]) -> str | None:
    output_text = data.get("output_text")
    if isinstance(output_text, str):
        return output_text

    output = data.get("output")
    if not isinstance(output, list):
        return None

    parts: list[str] = []
    for item in output:
        if not isinstance(item, Mapping):
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for piece in content:
            if not isinstance(piece, Mapping):
                continue
            text = piece.get("text")
            if isinstance(text, str):
                parts.append(text)

    if not parts:
        return None
    return "\n".join(parts)
