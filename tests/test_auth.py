import pytest

from oa_sdk.auth import build_inference_ticket_header, parse_inference_ticket_header
from oa_sdk.errors import TicketFormatError


def test_single_ticket_header_roundtrip() -> None:
    header = build_inference_ticket_header(["abc"])
    assert header == "InferenceTicket token=abc"
    assert parse_inference_ticket_header(header) == ["abc"]


def test_multi_ticket_header_roundtrip() -> None:
    header = build_inference_ticket_header(["a", "b", "c"])
    assert header == "InferenceTicket tokens=a,b,c"
    assert parse_inference_ticket_header(header) == ["a", "b", "c"]


def test_build_header_rejects_invalid_token_characters() -> None:
    with pytest.raises(TicketFormatError):
        build_inference_ticket_header(["abc,def"])

    with pytest.raises(TicketFormatError):
        build_inference_ticket_header(["abc\ndef"])


def test_parse_header_rejects_invalid_shape() -> None:
    with pytest.raises(TicketFormatError):
        parse_inference_ticket_header("Bearer abc")

    with pytest.raises(TicketFormatError):
        parse_inference_ticket_header("InferenceTicket token=")

    with pytest.raises(TicketFormatError):
        parse_inference_ticket_header("InferenceTicket token=abc extra")
