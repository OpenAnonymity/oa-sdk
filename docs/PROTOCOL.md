# Protocol Contracts

## Ticket Header Format
The OA org accepts either header shape:
- `InferenceTicket token=<token>`
- `InferenceTicket tokens=<token1>,<token2>,...`

Derived from:
- `oa-org/auth/ticket_auth.py`
- `request_key.py`

## Org Endpoints Used by SDK

### `GET /chat/model-tickets`
- Returns map: `{ "model_id": <ticket_cost_int>, ... }`.

### `GET /models` (OpenRouter)
- Returns model catalog object: `{ "data": [ ... ] }`.
- SDK currently reads these fields when present:
  - `id`
  - `name`
  - `created`
  - `canonical_slug`
  - `context_length`
  - `description`
  - `pricing`
- Free-model heuristic used by live testing helpers:
  - `pricing.prompt == "0"`
  - `pricing.completion == "0"`
  - `pricing.request` absent or `"0"`

### `GET /api/v2/online`
- Returns current online v2 stations keyed by station ID.
- Example station shape includes:
  - `url`
  - `providers`
  - `models`
  - `name`
  - `last_seen_seconds_ago`
  - `version`

### `GET /api/ticket/issue/public-key`
- Returns issuer public key used for blinding.

### `POST /api/alpha-register` (or `/api/code-redeem`)
- Request:
  - `credential: str`
  - `blinded_requests: [[index:int, blinded_request:str], ...]`
- Response:
  - `signed_responses: [[index:int, signed_response:str], ...]`
  - `expires_at: int`
  - `public_key: str`

### `POST /api/request_key`
- Authorization uses `InferenceTicket` format.
- Optional body: `{ "name": str, "station_id": str? }`
- Expected response includes:
  - `key: str`
  - `tickets_consumed: int`
  - `expires_at` / `expires_at_unix`
  - `station_id`
  - optionally `station_signature`, `org_signature`, `station_url`, `station_recently_attested`

Public simple API mapping:
- `oa.request_unlinkable_key(...)` -> uses this endpoint with selected local tickets through oa-org relay (no station pin in simple API).
- `oa.request_confidential_key(...)` -> same endpoint through oa-org relay (no station pin in simple API); optional attestation requirement is client-side enforced.
- `oa.list_stations(...)` -> calls `GET /api/v2/online` (or `/api/online` for v1).

### `GET /api/public_key`
- Returns org Ed25519 public key used to verify `org_signature` from `/api/request_key`.
- Expected response: `{ "public_key": "<hex>", "algorithm": "Ed25519" }`

## Error Handling Rules
- `401` with spent/double-use hints => map to spent-ticket error.
- Network/5xx/429 are retryable by transport policy.
- Non-idempotent operations must avoid blind retries unless safe.

## Request-Key Signature Verification
`/api/request_key` signatures are verified against these exact UTF-8 payloads:
- Station signature payload: `"{station_id}|{key}|{expires_at_unix}"`
- Org signature payload: `"{station_id}|{key}|{expires_at_unix}|{station_signature}"`

SDK helper surface:
- `KeyService.fetch_org_public_key()`
- `KeyService.verify_key_lease_signatures(...)`

Note:
- Station signature verification requires a trusted station public key source (for example a verifier broadcast/directory).

## Cross-SDK Contract Policy
- Python and JavaScript SDKs are separate implementations and both must conform to this protocol document.
- Behavior changes require updating protocol notes plus shared fixtures/conformance cases used by both SDKs.
- A shared native core is optional and should not be assumed by protocol or API design.

## OpenResponses Alignment
SDK inference surface mirrors OpenResponses-style normalized API (`responses.create`) while allowing backend-specific auth and URLs.
Reference:
- https://openresponses.org/
- https://openresponses.org/spec/openapi.openapi.yml

Backend mapping:
- `ephemeral_key`: OpenRouter-style `/chat/completions` with OA-issued ephemeral bearer key.
- `provider_direct`: OpenResponses-compatible `/v1/responses` with provider credential.
  - concrete current target: OpenAI Responses (`https://api.openai.com/v1/responses`).
  - concrete Gemini target: Gemini OpenAI-compatible endpoint (`https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`).
- `tee_gateway`: OpenResponses-compatible `/v1/responses` through TEE gateway endpoint with configurable headers.
  - currently modeled as explicit backend target; gateway-specific auth/attestation contract TBD.

## Retry Policy Matrix
The SDK maintains explicit per-endpoint retry policy:
- `model_tickets` (`GET /chat/model-tickets`): retry allowed (`idempotent`).
- `openrouter_model_catalog` (`GET /models` on OpenRouter): retry allowed (`idempotent`).
- `online_stations` (`GET /api/v2/online` or `/api/online`): retry allowed (`idempotent`).
- `org_public_key` (`GET /api/public_key`): retry allowed (`idempotent`).
- `request_key` (`POST /api/request_key`): retry allowed (`safe_with_rollback` semantics on org relay path).
- `ticket_issue_public_key` (`GET /api/ticket/issue/public-key`): retry allowed (`idempotent`).
- `alpha_register` (`POST /api/alpha-register`): retry disabled (`non_idempotent`).
- `inference` (backend calls): retry allowed for transient transport/5xx/429 failures.

## Gemini Live API (Official Ephemeral Token Flow)
Reference docs:
- https://ai.google.dev/gemini-api/docs/ephemeral-tokens
- https://ai.google.dev/gemini-api/docs/live-guide

Supported SDK operations:
1. Create ephemeral token using long-lived Gemini API key.
2. Use ephemeral token to run a live text turn.

Implementation keeps this path separate from HTTP OpenResponses backends because Gemini Live uses dedicated live session semantics.

## Simple Public Interface Contract
The Python SDK exposes a function-first public surface via `import oa`:
- `list_stations`
- `request_unlinkable_key`
- `request_confidential_key`
- `chat_completion`
- `add_tickets`
- `show_tickets`
- `archive_tickets`

`show_tickets(...)` returns:
- overall counts (`active_tickets`, `archived_tickets`)
- preview metadata (`preview_limit`, `active_shown`, `archived_shown`)
- preview lists (`active`, `archived`) that include:
  - `ticket_preview`: short view of the finalized ticket string
  - other non-null ticket metadata
  - full `finalized_ticket` only when `include_tokens=True`
- default preview limit is `5`

CLI commands mirror these operations:
- `list-stations`
- `request-unlinkable-key`
- `request-confidential-key`
- `chat-completion`
- `add-tickets`
- `show-tickets`
- `archive-tickets`

Advanced inference helper surface also includes:
- `InferenceService.list_openrouter_models()`
- `InferenceService.list_openrouter_free_models(...)`
- `InferenceService.latest_openrouter_free_model(...)`
