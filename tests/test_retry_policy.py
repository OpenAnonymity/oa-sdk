from __future__ import annotations

import pytest

from oa_sdk.retry_policy import RETRY_POLICY_MATRIX, endpoint_retry_allowed


def test_retry_policy_matrix_expected_defaults() -> None:
    assert endpoint_retry_allowed("model_tickets") is True
    assert endpoint_retry_allowed("online_stations") is True
    assert endpoint_retry_allowed("request_key") is True
    assert endpoint_retry_allowed("alpha_register") is False
    assert endpoint_retry_allowed("inference") is True
    assert "safe_with_rollback" == RETRY_POLICY_MATRIX["request_key"].idempotency.value


def test_retry_policy_unknown_endpoint_raises() -> None:
    with pytest.raises(ValueError):
        endpoint_retry_allowed("does-not-exist")
