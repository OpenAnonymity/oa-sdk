# OA SDK Py

Python SDK for The Open Anonymity Project unlinkable inference workflow.

> **Work in progress:** This repository is under active development. APIs and documentation may change before the `0.1.0` release.

Public API is intentionally simple:
- list online stations (`oa.list_stations`)
- request OA key (`oa.request_unlinkable_key`)
- request confidential key (`oa.request_confidential_key`)
- run chat completion (`oa.chat_completion`)
- add tickets from a code (`oa.add_tickets`)
- display/manage tickets (`oa.show_tickets`, `oa.archive_tickets`)

## Install (editable local)

```bash
pip install -e .
```

Optional blind-signature support:

```bash
pip install -e '.[blind-signatures]'
```

Optional Gemini Live support:

```bash
pip install -e '.[gemini-live]'
```

Optional request-key signature verification helpers:

```bash
pip install -e '.[signatures]'
```

## Python API (simple)

```python
import oa

# 0) Inspect real stations currently online in oa-org (v2 by default).
stations = oa.list_stations()
print(stations["total"])

# 1) Redeem ticket(s) for an OA unlinkable key.
# Defaults to ./oa-chat-tickets.json
key = oa.request_unlinkable_key(ticket_count=1)

# 2) Run inference with that key.
response = oa.chat_completion(
    key=key["key"],
    model="openai/gpt-5.2-chat",
    prompt="hi",
    destination="openrouter",
)
print(response["output_text"])
```

Confidential key flow (via oa-org relay):

```python
import oa

key = oa.request_confidential_key(
    ticket_count=1,
)
```

Advanced signature verification (station + org):

```python
from oa_sdk.client import OAClient
from oa_sdk.tickets.store import TicketStore

store = TicketStore.from_file("oa-chat-tickets.json")
with OAClient() as client:
    lease = client.keys.request_key_from_store(store=store, count=1)
    org_pub = client.keys.fetch_org_public_key()
    verification = client.keys.verify_key_lease_signatures(
        lease=lease,
        org_public_key_hex=org_pub,
        # station_public_key_hex=...  # from trusted station directory/broadcast
    )
    print(verification.org_signature_valid)
```

Ticket management:

```python
import oa

oa.add_tickets("YOUR_TICKET_CODE")
print(oa.show_tickets(limit=5))
oa.archive_tickets(count=1)
```

## CLI (matching simple API)

```bash
oa-sdk model-tiers
oa-sdk list-stations --version 2
oa-sdk request-unlinkable-key oa-chat-tickets.json --count 1
oa-sdk request-confidential-key oa-chat-tickets.json --count 1
oa-sdk chat-completion --key <oa_key> --model openai/gpt-5.2-chat --prompt "hi" --destination openrouter
oa-sdk add-tickets <ticket_code> oa-chat-tickets.json
oa-sdk show-tickets oa-chat-tickets.json --limit 5
oa-sdk archive-tickets oa-chat-tickets.json --count 1
```

## Backend Internals

Class/service surfaces still exist under `oa_sdk.*` for advanced integrations, but they are no longer the primary public interface.

## Docs

See `docs/`.

Minimal copy-paste quickstart:
- `docs/MINIMAL_EXAMPLE.md`

Live E2E test instructions:
- `docs/E2E_TESTING.md`
