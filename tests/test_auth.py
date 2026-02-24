from oa_sdk.auth import build_inference_ticket_header, parse_inference_ticket_header


def test_single_ticket_header_roundtrip() -> None:
    header = build_inference_ticket_header(["abc"])
    assert header == "InferenceTicket token=abc"
    assert parse_inference_ticket_header(header) == ["abc"]


def test_multi_ticket_header_roundtrip() -> None:
    header = build_inference_ticket_header(["a", "b", "c"])
    assert header == "InferenceTicket tokens=a,b,c"
    assert parse_inference_ticket_header(header) == ["a", "b", "c"]
