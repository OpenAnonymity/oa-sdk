# SDK Architecture

## Package Layout
- `oa`: top-level simple public API (`list_stations`, `request_unlinkable_key`, `request_confidential_key`, `chat_completion`, ticket helpers).
- `oa_sdk.simple`: implementation of the simple function API.
- `oa_sdk.client`: internal orchestration client used by simple API and advanced integrations.
- `oa_sdk.config`: SDK/client configuration models.
- `oa_sdk.errors`: typed error classes.
- `oa_sdk.transport`: HTTP and retry logic.
- `oa_sdk.models`: shared dataclasses/types.
- `oa_sdk.tickets`: ticket parsing/store/issuance helpers.
- `oa_sdk.keys`: model tiers and ephemeral key request flows.
- `oa_sdk.inference`: backend abstractions + OpenResponses-style API.
  - includes Gemini provider-direct target and Gemini Live API client.
- `oa_sdk.cli`: command-line entrypoint.

## Responsibility Boundaries
- `oa`/`oa_sdk.simple` handles ergonomic public API composition and file persistence defaults.
- Tickets module handles local token lifecycle (including blind-signature issuance).
- Keys module handles OA org key exchange only.
- Inference module handles provider/backend calls using obtained credentials.
- Transport module owns retries/timeouts and never encodes OA-specific logic.

## Workflow Mapping

### A) Ticket issuance
1. Fetch issuer public key (`/api/ticket/issue/public-key`).
2. Blind N token requests locally.
3. Send `blinded_requests` to `/api/alpha-register`.
4. Finalize signed responses into tickets.
5. Persist active tickets.

### B) Key request (from tickets)
1. Select N active tickets.
2. Build `Authorization: InferenceTicket token=...` or `tokens=...`.
3. POST `/api/request_key`.
4. On success, archive consumed tickets and return `KeyLease`.
5. On failure, keep tickets active unless error proves they are spent.

### B.1) Station discovery
1. Call OA org station discovery endpoint (`/api/v2/online` by default).
2. Return currently online stations so callers can inspect real station IDs/metadata.

### C) Inference
1. Choose backend kind (`ephemeral_key`, `provider_direct`, `tee_gateway`).
2. Build OpenResponses-like request payload.
3. Apply backend auth strategy.
4. POST to backend endpoint.

Gemini note:
- Provider-direct Gemini uses the Gemini OpenAI-compatible endpoint (`/chat/completions`).
- Gemini Live (ephemeral token capable) is exposed via dedicated live client methods.

### D) End-to-End flow
1. Resolve ticket count from model tiers (unless explicitly overridden).
2. Request ephemeral key via `/api/request_key`.
3. Run inference call with returned key.
4. Return both key lease and response.

Exposed publicly via:
- `oa.list_stations(...)`
- `oa.request_unlinkable_key(...)`
- `oa.chat_completion(...)`

`OAClient.request_key_and_infer_openrouter(...)` remains available as an internal/advanced helper.

## Cross-Language Strategy
- Implement Python and JavaScript SDKs separately using native language/runtime patterns.
- Enforce parity via shared protocol contracts and conformance fixtures/tests.
- Keep any future shared native core optional and limited to deterministic crypto-critical operations only.
