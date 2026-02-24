from __future__ import annotations

from oa_sdk.config import OAConfig
from oa_sdk.inference.gemini_live import _extract_text_chunks, _is_turn_complete, _to_plain
from oa_sdk.inference.models import AccessCredential, ResponseRequest
from oa_sdk.inference.service import InferenceService
from oa_sdk.transport import TransportResult


class FakeTransport:
    def __init__(self, result: TransportResult):
        self.result = result
        self.last_url = None

    def request_json(self, method, url, **kwargs):  # noqa: ANN001, ANN003
        self.last_url = url
        return self.result


def test_gemini_provider_direct_backend_default_base() -> None:
    transport = FakeTransport(
        TransportResult(
            status_code=200,
            data={
                "id": "chatcmpl_1",
                "choices": [{"message": {"content": "gemini ok"}}],
            },
            text="",
            headers={},
        )
    )

    service = InferenceService(
        config=OAConfig(gemini_openai_api_base="https://generativelanguage.googleapis.com/v1beta/openai"),
        transport=transport,
    )
    backend = service.gemini_provider_direct_backend()

    response = service.create_response(
        ResponseRequest(model="gemini-2.5-flash", input="hi"),
        backend=backend,
        credential=AccessCredential(token="tok"),
    )

    assert response.output_text == "gemini ok"
    assert (
        transport.last_url
        == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    )


def test_gemini_live_helpers_extract_text_and_turn_complete() -> None:
    event = {
        "server_content": {
            "model_turn": {
                "parts": [
                    {"text": "hello "},
                    {"text": "world"},
                ]
            },
            "turn_complete": True,
        }
    }

    assert _extract_text_chunks(event) == ["hello ", "world"]
    assert _is_turn_complete(event) is True


def test_to_plain_handles_basic_object() -> None:
    class Obj:
        def __init__(self) -> None:
            self.a = "x"
            self.b = {"n": 1}

    plain = _to_plain(Obj())
    assert plain == {"a": "x", "b": {"n": 1}}
