from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from ..errors import OAProtocolError, OptionalDependencyError
from ..models import OAResponse


@dataclass(frozen=True)
class GeminiEphemeralToken:
    name: str
    expire_time: str | None
    raw: Mapping[str, Any]


class GeminiLiveClient:
    """Gemini Live API client using the official `google-genai` SDK."""

    def __init__(self, *, api_key: str, api_version: str = "v1alpha") -> None:
        try:
            from google import genai  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise OptionalDependencyError(
                "Gemini Live requires optional dependency 'google-genai'. "
                "Install with: pip install 'oa-sdk-py[gemini-live]'"
            ) from exc

        self._genai = genai
        self._api_version = api_version
        self._client = genai.Client(
            api_key=api_key,
            http_options={"api_version": api_version},
        )

    def create_ephemeral_token(
        self,
        *,
        uses: int = 1,
        expire_seconds: int = 30 * 60,
        new_session_expire_seconds: int = 60,
        live_model: str | None = None,
        response_modalities: Sequence[str] | None = ("TEXT",),
    ) -> GeminiEphemeralToken:
        if uses <= 0:
            raise ValueError("uses must be > 0")
        if expire_seconds <= 0:
            raise ValueError("expire_seconds must be > 0")
        if new_session_expire_seconds <= 0:
            raise ValueError("new_session_expire_seconds must be > 0")

        config: dict[str, Any] = {
            "uses": uses,
            "expire_time": f"{expire_seconds}s",
            "new_session_expire_time": f"{new_session_expire_seconds}s",
        }

        if live_model or response_modalities:
            live_constraints: dict[str, Any] = {}
            if live_model:
                live_constraints["model"] = live_model
            if response_modalities:
                live_constraints["config"] = {
                    "response_modalities": list(response_modalities),
                }
            config["live_constrained_parameters"] = live_constraints

        token = self._client.auth_tokens.create(config=config)
        token_data = _to_plain(token)
        if not isinstance(token_data, Mapping):
            raise OAProtocolError("Gemini auth_tokens.create returned unexpected payload")

        name = token_data.get("name")
        if not isinstance(name, str) or not name:
            raise OAProtocolError("Gemini auth token response missing token name")

        expire_time = token_data.get("expire_time")
        if not isinstance(expire_time, str):
            expire_time = None

        return GeminiEphemeralToken(name=name, expire_time=expire_time, raw=token_data)

    async def generate_text(
        self,
        *,
        token_name: str,
        model: str,
        prompt: str,
        response_modalities: Sequence[str] = ("TEXT",),
        max_events: int = 128,
    ) -> OAResponse:
        if max_events <= 0:
            raise ValueError("max_events must be > 0")

        token_client = self._genai.Client(
            api_key=token_name,
            http_options={"api_version": self._api_version},
        )

        events: list[Mapping[str, Any]] = []
        parts: list[str] = []

        config = {"response_modalities": list(response_modalities)}

        async with token_client.aio.live.connect(model=model, config=config) as session:
            await session.send_client_content(
                turns={"role": "user", "parts": [{"text": prompt}]},
                turn_complete=True,
            )

            async for event in session.receive():
                event_data = _to_plain(event)
                if isinstance(event_data, Mapping):
                    events.append(event_data)
                    parts.extend(_extract_text_chunks(event_data))
                    if _is_turn_complete(event_data):
                        break
                if len(events) >= max_events:
                    break

        output_text = "".join(parts) if parts else None
        return OAResponse(response_id=None, output_text=output_text, raw={"events": events})


def _extract_text_chunks(event_data: Mapping[str, Any]) -> list[str]:
    chunks: list[str] = []

    top_text = event_data.get("text")
    if isinstance(top_text, str) and top_text:
        chunks.append(top_text)

    server_content = event_data.get("server_content")
    if isinstance(server_content, Mapping):
        model_turn = server_content.get("model_turn")
        if isinstance(model_turn, Mapping):
            parts = model_turn.get("parts")
            if isinstance(parts, list):
                for part in parts:
                    if isinstance(part, Mapping):
                        text = part.get("text")
                        if isinstance(text, str) and text:
                            chunks.append(text)

    return chunks


def _is_turn_complete(event_data: Mapping[str, Any]) -> bool:
    top = event_data.get("turn_complete")
    if isinstance(top, bool):
        return top

    server_content = event_data.get("server_content")
    if isinstance(server_content, Mapping):
        value = server_content.get("turn_complete")
        if isinstance(value, bool):
            return value

    return False


def _to_plain(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, Mapping):
        return {str(k): _to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_plain(v) for v in value]

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        try:
            dumped = model_dump(exclude_none=True)
            return _to_plain(dumped)
        except TypeError:
            dumped = model_dump()
            return _to_plain(dumped)

    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _to_plain(to_dict())

    if hasattr(value, "__dict__"):
        data = {
            key: _to_plain(val)
            for key, val in vars(value).items()
            if not key.startswith("_")
        }
        return data

    return str(value)
