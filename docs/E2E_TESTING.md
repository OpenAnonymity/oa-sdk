# E2E Testing

This repository includes a real live E2E pytest:
- `tests/test_e2e_live.py`

It runs the true workflow:
1. Load tickets from a local ticket export JSON.
2. Request an ephemeral key via OA org `/api/request_key`.
3. Use the key for one inference call.
4. Persist ticket file updates (active -> archived).

## Important
This test consumes real tickets.
Each run with `OA_E2E_TICKET_COUNT=1` archives exactly one ticket.
That is acceptable for local developer and agent workflows in this repo, and it is fine to run this live test liberally when changing end-to-end behavior.

If `OA_E2E_MODEL` is unset, the test now:
1. Fetches OA model tiers from `/chat/model-tickets`.
2. Fetches the live OpenRouter catalog from `/models`.
3. Picks the newest free text model that appears in both sets.

This avoids hardcoding stale model IDs while still preferring a model OA currently supports.
Using a free OpenRouter model does not make the OA key request free; the OA ticket redemption still consumes real tickets.
The test prints ticket-usage lines to the terminal before and after the request so runners can see the requested and observed consumed counts clearly.

## Run

```bash
OA_E2E_LIVE=1 \
OA_E2E_TICKETS_FILE=oa-chat-tickets.json \
OA_E2E_PROMPT='ping' \
OA_E2E_TICKET_COUNT=1 \
PYTHONPATH=src pytest -m e2e_live tests/test_e2e_live.py -q
```

## Optional env vars
- `OA_E2E_MODEL` (override auto-selection)
- `OA_E2E_STATION_ID` (pin station)
- `OA_E2E_KEY_NAME` (default: `OA-SDK-E2E`)

## Inspect free-model candidates

```python
from oa_sdk.client import OAClient

with OAClient() as client:
    supported = client.keys.fetch_model_tickets().keys()
    model = client.inference.latest_openrouter_free_model(
        allowed_model_ids=supported,
    )
    print(model.id)
```

## CI guidance
Do not run this test in regular CI by default.
Keep it opt-in/manual because it needs:
- network access
- real tickets
- live OA/OpenRouter services
