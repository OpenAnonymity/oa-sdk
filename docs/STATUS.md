# Status Log

## 2026-02-23 - Milestone 0 (Before)
Planned:
1. Create docs baseline and AGENTS policy.
2. Scaffold Python package layout.
3. Implement first working SDK path:
   - ticket import + request key
   - inference abstractions with backend kinds
4. Add tests and run pytest.

Notes:
- OA website/blog were not resolvable from this shell environment.
- Workflow contracts are grounded in local `oa-fastchat`, `oa-org`, and `request_key.py`.

## 2026-02-23 - Milestone 0 (After)
Completed:
- [x] Docs baseline created.
- [x] Python package scaffolded (`oa_sdk`).
- [x] Transport, config, and typed error foundations implemented.
- [x] Ticket parsing/store implemented (compatible export shapes).
- [x] Key request flow implemented from ticket store (with spent-ticket mapping).
- [x] Inference abstraction implemented for 3 backend kinds:
  - `ephemeral_key` (OpenRouter chat-completions path),
  - `provider_direct` (OpenResponses-style path),
  - `tee_gateway` (OpenResponses-style path with configurable headers).
- [x] CLI commands added: `tiers`, `key-request`, `ticket-redeem`, `infer`.
- [x] Basic examples added under `/examples`.

Tests:
- `pytest` -> `10 passed`.

Open Questions:
1. Default package name preference.
2. Whether v0.1 should include backend stubs only or concrete provider-direct + TEE implementations.
3. Preferred sync/async API priority for first release.

## 2026-02-23 - Milestone 1 (Before)
Planned:
1. Rename package metadata to `oa-sdk-py`.
2. Add first-class end-to-end request-key + inference flow.
3. Add concrete provider-direct production backend target.
4. Keep TEE gateway as explicit stub target plus continuation plan docs.
5. Add universal multi-language core/binding plan documentation.

## 2026-02-23 - Milestone 1 (After)
Completed:
- [x] Renamed package distribution metadata to `oa-sdk-py`.
- [x] Added end-to-end client method (`OAClient.request_key_and_infer_openrouter`).
- [x] Added CLI workflow command: `infer-with-tickets`.
- [x] Added concrete provider-direct backend target: OpenAI Responses.
- [x] Kept tee-gateway backend as explicit (experimental/stub-target) abstraction.
- [x] Added universal core + bindings plan doc.

Tests:
- `pytest` -> `12 passed`.

Open Questions:
1. Which non-OpenAI provider-direct target should be next (Anthropic/Gemini/other)?
2. Should CLI default backend be switched from `openrouter` to `openai-provider-direct` for provider-direct demos?

## 2026-02-23 - Milestone 2 (Before)
Planned:
1. Add concrete Gemini provider-direct backend target.
2. Add Gemini Live API support (official ephemeral token flow).
3. Remove `FlowService` public surface and keep request_key-first workflow directly on `OAClient`.
4. Update CLI/docs/tests accordingly.

## 2026-02-23 - Milestone 2 (After)
Completed:
- [x] Added `gemini-provider-direct` backend target.
- [x] Added Gemini Live API client with:
  - ephemeral token creation
  - one live text-turn inference helper
- [x] Removed public `FlowService` concept from SDK surface.
- [x] Added direct client workflow method:
  - `OAClient.request_key_and_infer_openrouter(...)`
- [x] Updated CLI commands:
  - `infer --backend gemini-provider-direct`
  - `gemini-live-token`
  - `infer-gemini-live`
- [x] Added Gemini Live example script (`examples/gemini_live_text.py`).

Tests:
- `pytest` -> `15 passed`.
- `oa-chat-tickets.json` compatibility check:
  - parsed active tickets: `1000`
  - archived tickets: `0`
- Live E2E run (`infer-with-tickets`, ticket_count=1):
  - request_key: success
  - inference: success
  - output text: `pong 🏓`
  - station_id: `v2-station-stanford-2`
  - ticket file state after run: `999 active`, `1 archived`

Open Questions:
1. Should Gemini provider-direct be default for provider-direct docs/examples over OpenAI?
2. For Gemini Live, do you want streaming callback support as next increment or keep batch text-turn for now?

## 2026-02-23 - Milestone 3 (After)
Completed:
- [x] Added reusable live E2E pytest:
  - `tests/test_e2e_live.py`
  - marker: `@pytest.mark.e2e_live`
  - env-guarded and opt-in only
- [x] Added E2E runbook:
  - `docs/E2E_TESTING.md`

Tests:
- default suite: `15 passed, 1 skipped`
- live E2E suite:
  - `OA_E2E_LIVE=1 ... pytest -m e2e_live tests/test_e2e_live.py -q`
  - result: `1 passed`

Ticket file state after latest live E2E run:
- `oa-chat-tickets.json`: `998 active`, `2 archived`

## 2026-02-23 - Milestone 4 (Before)
Planned:
1. Document cross-language SDK strategy decision for JS + Python.
2. Resolve ambiguity between universal-core-first and separate-SDK development guidance.
3. Add backlog/status traceability for future contributors.

## 2026-02-23 - Milestone 4 (After)
Completed:
- [x] Added explicit ADR selecting separate JS/Python SDK implementations with shared conformance contracts.
- [x] Marked prior universal-core-first guidance as superseded.
- [x] Updated architecture/protocol/docs index to reflect new default strategy.
- [x] Added backlog item for shared JS/Python conformance fixture suite.

Tests:
- Not run (docs-only updates).

Open Questions:
1. When JS SDK work starts, should conformance fixtures live in this repo or a dedicated cross-SDK test artifact repo?

## 2026-02-24 - Milestone 5 (Before)
Planned:
1. Introduce a brutally simple public Python interface with top-level function calls via `import oa`.
2. Keep class/service objects as backend implementation details rather than primary public entrypoint.
3. Align CLI command surface with the same simple operations:
   - request unlinkable key
   - request confidential key
   - run chat completion
   - add tickets by code
   - display/manage tickets
4. Preserve existing workflow semantics (`request_key.py` parity and ticket safety rules) under the simplified interface.

## 2026-02-24 - Milestone 5 (After)
Completed:
- [x] Added function-first public API under `import oa`:
  - `request_unlinkable_key`
  - `request_confidential_key`
  - `chat_completion`
  - `add_tickets`
  - `show_tickets`
  - `archive_tickets`
- [x] Added `oa_sdk.simple` as composition layer while keeping existing service/class internals.
- [x] Updated `oa_sdk.__init__` exports to emphasize function-first surface.
- [x] Simplified CLI to match same operation model with direct commands:
  - `request-unlinkable-key`
  - `request-confidential-key`
  - `chat-completion`
  - `add-tickets`
  - `show-tickets`
  - `archive-tickets`
  - plus `model-tiers`
- [x] Added compatibility aliases for key legacy CLI names (`key-request`, `infer`, `ticket-redeem`, `tiers`).
- [x] Updated README and examples to the simplified public API.
- [x] Added tests for new simple API module (`tests/test_simple_api.py`).

Tests:
- `pytest -ra` -> `20 passed, 1 skipped`.
- skipped test: live E2E requires `OA_E2E_LIVE=1`.

Remaining Risks:
1. Existing users importing top-level `oa_sdk` classes (`from oa_sdk import OAClient`) now need `from oa_sdk.client import OAClient` or the new `import oa` surface.
2. Confidential key flow currently maps to `request_key` semantics with optional attestation enforcement; server-side confidential contract may evolve.

## 2026-02-24 - Milestone 6 (Before)
Planned:
1. Run a real live E2E key request + inference test consuming one ticket.
2. Add minimal SDK usage documentation focused on the simple public interface.
3. Prepare and push the current SDK snapshot to remote.

## 2026-02-24 - Milestone 6 (After)
Completed:
- [x] Ran live E2E test that performs real ticket redemption + inference:
  - `OA_E2E_LIVE=1 OA_E2E_TICKETS_FILE=oa-chat-tickets.json OA_E2E_TICKET_COUNT=1 PYTHONPATH=src pytest -m e2e_live tests/test_e2e_live.py -q`
  - result: `1 passed`
- [x] Added minimal quickstart usage doc:
  - `docs/MINIMAL_EXAMPLE.md`
- [x] Linked minimal quickstart from:
  - `README.md`
  - `docs/README.md`

Tests:
- live E2E: `1 passed` (real key request + inference)
- default suite: `pytest -ra` -> `20 passed, 1 skipped`

Ticket file state after latest live E2E run:
- `oa-chat-tickets.json`: `997 active`, `3 archived`

## 2026-02-24 - Milestone 7 (Before)
Planned:
1. Remove repository PII leakage by replacing local absolute paths in docs with repository-relative paths.
2. Align confidential key flow with `oa-org` relay semantics by avoiding caller-pinned station IDs in the top-level simple API and CLI.
3. Expose real online station discovery from `oa-org` in the public SDK so callers can inspect actual available stations.

## 2026-02-24 - Milestone 7 (After)
Completed:
- [x] Removed local absolute path references from public docs (`README.md`, `docs/README.md`, `docs/PROTOCOL.md`) to avoid PII leakage in OSS.
- [x] Added public station discovery surface:
  - Python: `oa.list_stations(version=...)`
  - CLI: `oa-sdk list-stations --version {1|2}`
  - service layer: `KeyService.fetch_online_stations(...)`
- [x] Updated top-level confidential flow to rely on oa-org relay selection (no station pin argument in simple API/CLI).
- [x] Updated docs and architecture/protocol notes for station discovery and relay-first confidential flow.
- [x] Added/updated tests for station discovery and confidential-key API shape.

Tests:
- `pytest -ra` -> `23 passed, 1 skipped`.
- skipped test: live E2E requires `OA_E2E_LIVE=1`.

Remaining Risks:
1. This change is intentionally breaking for callers using top-level station pinning (`oa.request_unlinkable_key(..., station_id=...)`, `oa.request_confidential_key(..., station_id=...)`, or CLI `--station-id` on key-request commands).
2. Low-level station pinning still exists in advanced/internal service methods for compatibility with raw oa-org request contract; public docs now prefer relay-selected station flow.

## 2026-02-24 - Milestone 8 (Before)
Planned:
1. Run live E2E key-request + inference roundtrip using real tickets.
2. Rewrite git history to remove commit snapshots that contain local absolute-path PII.

## 2026-02-24 - Milestone 8 (After)
Completed:
- [x] Ran live E2E pytest using real OA ticket flow and inference call.
- [x] Rewrote git history to replace earlier commit snapshots containing local path PII.

Tests:
- `OA_E2E_LIVE=1 OA_E2E_TICKETS_FILE=oa-chat-tickets.json OA_E2E_MODEL=openai/gpt-5.2-chat OA_E2E_PROMPT='ping' OA_E2E_TICKET_COUNT=1 PYTHONPATH=src pytest -m e2e_live tests/test_e2e_live.py -q` -> `1 passed`.

## 2026-02-25 - Milestone 9 (Before)
Planned:
1. Run a full SDK hardening scan across transport, auth/header parsing, key request flow, ticket store semantics, and retry behavior.
2. Implement remaining P0 hardening work:
   - request-key signature verification helper (station + org signatures),
   - explicit endpoint retry policy matrix tied to idempotency and ticket-consumption risk.
3. Fix async transport retry backoff to avoid blocking sleeps in async code paths.
4. Add targeted tests for all new/changed behavior and run full `pytest -ra`.

## 2026-02-25 - Milestone 9 (After)
Completed:
- [x] Added centralized retry policy matrix (`src/oa_sdk/retry_policy.py`) and wired service calls to named endpoint policy entries.
- [x] Added request-key signature verification helpers (`src/oa_sdk/signatures.py`) including:
  - station payload format: `{station_id}|{key}|{expires_at_unix}`
  - org payload format: `{station_id}|{key}|{expires_at_unix}|{station_signature}`
  - optional Ed25519 verification backends (`pynacl` or `cryptography`)
- [x] Added `KeyService` hardening helpers:
  - `fetch_org_public_key()`
  - `verify_key_lease_signatures(...)`
- [x] Fixed async transport retry backoff to use non-blocking async sleep in `AsyncHTTPTransport`.
- [x] Hardened ticket auth header handling by rejecting malformed tokens (delimiter/newline/whitespace injection cases).
- [x] Hardened ticket store merge semantics to avoid re-adding already archived tokens.
- [x] Added/updated tests for all hardening changes:
  - `tests/test_auth.py`
  - `tests/test_key_service.py`
  - `tests/test_retry_policy.py`
  - `tests/test_signatures.py`
  - `tests/test_ticket_store.py`
  - `tests/test_transport.py`
- [x] Updated README/docs for signature verification and retry policy behavior.

Tests:
- `pytest -ra` -> `36 passed, 1 skipped`.
- `python -m compileall -q src` -> success.
- `ruff check src tests` -> not run (`ruff` not installed in shell).
- `mypy src` -> not run (`mypy` not installed in shell).

Remaining Risks / Follow-ups:
1. Full async parity is still incomplete at public API/service level (backlog item remains open).
2. Station signature verification still requires callers to supply a trusted station public key source.
