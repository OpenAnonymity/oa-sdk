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

## Run

```bash
OA_E2E_LIVE=1 \
OA_E2E_TICKETS_FILE=oa-chat-tickets.json \
OA_E2E_MODEL=openai/gpt-5.2-chat \
OA_E2E_PROMPT='ping' \
OA_E2E_TICKET_COUNT=1 \
PYTHONPATH=src pytest -m e2e_live tests/test_e2e_live.py -q
```

## Optional env vars
- `OA_E2E_STATION_ID` (pin station)
- `OA_E2E_KEY_NAME` (default: `OA-SDK-E2E`)

## CI guidance
Do not run this test in regular CI by default.
Keep it opt-in/manual because it needs:
- network access
- real tickets
- live OA/OpenRouter services
