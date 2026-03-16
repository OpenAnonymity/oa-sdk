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

## 2026-03-15 - Milestone 10 (Before)
Planned:
1. Review the current simple SDK surface against the standalone `request_key.py` baseline and the `oa-fastchat` ticket-code redemption flow.
2. Confirm whether the SDK is already at least as simple to use for:
   - existing `tickets.json` -> request key
   - ticket code -> redeem tickets locally -> request key
3. If README onboarding is still too diffuse, add one compact quickstart section centered on those two entry points.

## 2026-03-15 - Milestone 10 (After)
Completed:
- [x] Reviewed the current public SDK surface against:
  - local `request_key.py`
  - `oa-fastchat/chat/services/ticketClient.js`
  - `oa-fastchat/chat/services/privacyPass.js`
- [x] Confirmed the simple surface already covers the required minimal workflows:
  - `oa.request_unlinkable_key(...)` for existing local tickets
  - `oa.add_tickets(...)` for ticket-code redemption into local store
  - `oa-sdk request-unlinkable-key ...` / `oa-sdk add-tickets ...` for the same flows from CLI
- [x] Confirmed ticket-file compatibility and request-key behavior remain aligned with the bare script:
  - exported oa-chat ticket shapes are parsed by `oa_sdk.tickets.parser`
  - `InferenceTicket token=...` / `tokens=...` formatting is covered by tests
  - spent-ticket mapping is covered by `tests/test_key_service.py`
- [x] Added a README quickstart section that starts from the two real user entry points:
  - already have `tickets.json`
  - only have a redeemable ticket code

Tests:
- `pytest -ra` -> `36 passed, 1 skipped`.
- skipped test: live E2E requires `OA_E2E_LIVE=1`.
- `python -m compileall -q src` -> success.

Remaining Risks / Follow-ups:
1. README onboarding is now clearer, but live E2E for the ticket-code redemption path was not re-run in this pass.
2. Ticket-code redemption still requires the optional blind-signature dependency (`pip install -e '.[blind-signatures]'`), which is documented but not part of the base install.

## 2026-03-15 - Milestone 11 (Before)
Planned:
1. Add contributor-facing guidance that redeeming real tickets for manual/live testing is acceptable, with preference for free OpenRouter models.
2. Add a small OpenRouter catalog helper so tests/docs can discover the newest free model dynamically instead of pinning a brittle example model ID.
3. Update the live E2E path and runbook to use catalog-discovered free models by default while still allowing `OA_E2E_MODEL` override.

## 2026-03-15 - Milestone 11 (After)
Completed:
- [x] Added OpenRouter catalog helper in the inference layer:
  - `InferenceService.list_openrouter_models()`
  - `InferenceService.list_openrouter_free_models(...)`
  - `InferenceService.latest_openrouter_free_model(...)`
- [x] Added typed OpenRouter catalog parsing/model metadata module:
  - `src/oa_sdk/inference/openrouter_catalog.py`
- [x] Updated live E2E pytest default model resolution:
  - if `OA_E2E_MODEL` is unset, it now selects the newest free OpenRouter text model that also appears in OA's current `/chat/model-tickets` map
- [x] Updated contributor/testing docs:
  - `AGENTS.md`
  - `docs/E2E_TESTING.md`
  - `docs/DECISIONS.md`
  - `docs/PROTOCOL.md`
  - `README.md`
  - `docs/BACKLOG.md`
- [x] Added unit coverage for OpenRouter catalog parsing/filtering/selection:
  - `tests/test_inference.py`

Tests:
- `pytest tests/test_inference.py -q` -> `6 passed`.
- `pytest -ra` -> `39 passed, 1 skipped`.
- skipped test: `tests/test_e2e_live.py` requires `OA_E2E_LIVE=1`.
- `python -m compileall -q src` -> success.

Remaining Risks / Follow-ups:
1. The new free-model auto-selection path was not live-exercised in this turn because doing so would redeem a real ticket.
2. OpenRouter catalog semantics are external and may evolve; the SDK currently treats zero `prompt` + zero `completion` + absent/zero `request` pricing as the free-text-model signal.

## 2026-03-15 - Milestone 12 (Before)
Planned:
1. Make the live E2E test print ticket-usage information clearly for humans/agents running it.
2. Include both the requested ticket count and the observed consumed count in the terminal output.
3. Update the E2E runbook/status notes to reflect the clearer reporting behavior.

## 2026-03-15 - Milestone 12 (After)
Completed:
- [x] Updated `tests/test_e2e_live.py` to emit terminal-visible ticket usage lines:
  - pre-request `planned-spend` line with requested ticket count and starting ticket-file counts
  - post-request `result` line with requested/consumed counts and before/after ticket-file counts
- [x] Updated contributor guidance to reflect that local developers and agents can run live E2E tests liberally in this repo:
  - `AGENTS.md`
  - `docs/E2E_TESTING.md`
- [x] Live-validated the new reporting against the local ticket file.

Tests:
- `OA_E2E_LIVE=1 OA_E2E_TICKETS_FILE=oa-chat-tickets.json PYTHONPATH=src pytest -m e2e_live tests/test_e2e_live.py -q -s` -> `1 passed`
- live terminal output:
  - `[oa-sdk live e2e] phase=planned-spend requested_tickets=1 active_before=995 archived_before=5 model=stepfun/step-3.5-flash:free`
  - `[oa-sdk live e2e] phase=result requested_tickets=1 active_before=995 archived_before=5 model=stepfun/step-3.5-flash:free consumed_tickets=1 active_after=994 archived_after=6`
- `pytest -ra` -> `39 passed, 1 skipped`
- skipped test: `tests/test_e2e_live.py` requires `OA_E2E_LIVE=1`
- `python -m compileall -q src` -> success

Ticket file state after latest live E2E run:
- `oa-chat-tickets.json`: `994 active`, `6 archived`

Remaining Risks / Follow-ups:
1. Ticket-usage reporting is terminal-oriented; if a future runner suppresses terminal output entirely, they should use `-s` for the clearest live-test visibility.

## 2026-03-15 - Milestone 13 (Before)
Planned:
1. Simplify `oa.show_tickets(...)` preview payload so active tickets do not emit null-heavy fields by default.
2. Add explicit preview metadata (`preview_limit`, shown counts) so the output reads more like a summary than a raw export fragment.
3. Update tests and protocol notes for the cleaner shape.

## 2026-03-15 - Milestone 13 (After)
Completed:
- [x] Simplified `oa.show_tickets(...)` preview payload:
  - active tickets no longer emit `status=None` / `consumed_at=None`
  - preview entries now include only non-null metadata unless `include_tokens=True`
- [x] Added preview summary metadata:
  - `preview_limit`
  - `active_shown`
  - `archived_shown`
- [x] Reduced default preview limit from `20` to `5` for both Python and CLI surfaces so the default output is more summary-oriented.
- [x] Updated tests and protocol notes for the cleaner shape.

Tests:
- `pytest tests/test_simple_api.py -q` -> `7 passed`
- `pytest -ra` -> `39 passed, 1 skipped`
- skipped test: `tests/test_e2e_live.py` requires `OA_E2E_LIVE=1`
- `python -m compileall -q src` -> success
- local shape check:
  - `PYTHONPATH=src python - <<'PY' ... oa.show_tickets('oa-chat-tickets.json') ... PY` -> active previews show only `created_at`; default `preview_limit=5`

Remaining Risks / Follow-ups:
1. `show_tickets(..., include_tokens=False)` can still yield sparse preview items if a ticket export lacks timestamps/status metadata entirely, though current OA-issued tickets include `created_at`.

## 2026-03-15 - Milestone 14 (Before)
Planned:
1. Make `oa.show_tickets(...)` previews include a short view of the actual finalized ticket string by default.
2. Keep the full finalized ticket behind `include_tokens=True` to avoid dumping long secrets into normal output.
3. Update tests and protocol notes for the new preview field.

## 2026-03-15 - Milestone 14 (After)
Completed:
- [x] Updated `oa.show_tickets(...)` previews to include `ticket_preview` derived from the actual finalized ticket string by default.
- [x] Kept full `finalized_ticket` output behind `include_tokens=True`.
- [x] Preserved timestamp/status metadata when present, but no longer rely on timestamps alone to distinguish tickets.
- [x] Updated tests and protocol notes for the new preview field.

Tests:
- `pytest tests/test_simple_api.py -q` -> `8 passed`
- `pytest -ra` -> `40 passed, 1 skipped`
- skipped test: `tests/test_e2e_live.py` requires `OA_E2E_LIVE=1`
- local shape check:
  - `PYTHONPATH=src python - <<'PY' ... oa.show_tickets('oa-chat-tickets.json') ... PY` -> active/archived previews now include shortened finalized ticket strings such as `AAIASnrvH-8_koVE...5PPgfdLs`

Remaining Risks / Follow-ups:
1. `ticket_preview` is intentionally lossy; callers that need the full finalized ticket should still use `include_tokens=True`.
