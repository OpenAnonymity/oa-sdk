from oa_sdk.config import OAConfig
from oa_sdk.inference.backends import BackendKind, OpenResponsesBackend
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


def test_openresponses_backend_response_parsing() -> None:
    backend = OpenResponsesBackend(
        base_url="https://provider.test",
        kind=BackendKind.PROVIDER_DIRECT,
        id="provider-direct",
    )
    parsed = backend.parse_response(
        {
            "id": "resp_1",
            "output": [
                {
                    "content": [
                        {"text": "hello"},
                        {"text": "world"},
                    ]
                }
            ],
        }
    )
    assert parsed.response_id == "resp_1"
    assert parsed.output_text == "hello\nworld"


def test_inference_service_calls_backend() -> None:
    transport = FakeTransport(
        TransportResult(
            status_code=200,
            data={"id": "resp_123", "output_text": "ok"},
            text="",
            headers={},
        )
    )
    service = InferenceService(config=OAConfig(), transport=transport)
    backend = service.provider_direct_backend(base_url="https://provider.example")

    response = service.create_response(
        ResponseRequest(model="model-a", input="hi"),
        backend=backend,
        credential=AccessCredential(token="tok"),
    )

    assert response.response_id == "resp_123"
    assert response.output_text == "ok"
    assert transport.last_url == "https://provider.example/v1/responses"


def test_openai_provider_direct_backend_default_base() -> None:
    transport = FakeTransport(
        TransportResult(
            status_code=200,
            data={"id": "resp_456", "output_text": "ok"},
            text="",
            headers={},
        )
    )
    service = InferenceService(
        config=OAConfig(openai_api_base="https://api.openai.example"),
        transport=transport,
    )
    backend = service.openai_provider_direct_backend()

    response = service.create_response(
        ResponseRequest(model="gpt-5", input="hi"),
        backend=backend,
        credential=AccessCredential(token="tok"),
    )

    assert response.response_id == "resp_456"
    assert transport.last_url == "https://api.openai.example/v1/responses"
