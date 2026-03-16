# Decisions

## 2026-02-23: Docs-first execution
Decision:
- Enforce docs updates before and after implementation milestones.

Why:
- User requirement: first-class documentation and resumable context.

## 2026-02-23: Workflow grounding
Decision:
- Use `request_key.py` and `oa-fastchat` as primary workflow references; use `oa-org` only for endpoint contract behavior.

Why:
- Keeps SDK aligned to real client flows while avoiding server internals.

## 2026-02-23: Inference abstraction model
Decision:
- Implement three backend kinds in SDK surface:
  - `ephemeral_key`
  - `provider_direct`
  - `tee_gateway`
- Keep one unified inference method (`create_response`) that maps backend-specific HTTP/auth details.

Why:
- Matches `oa-fastchat` backend taxonomy and keeps future language SDK parity straightforward.

## 2026-02-23: OpenResponses-style request shape
Decision:
- Model inference request API as OpenResponses-like request object (`model`, `input`, optional controls), then adapt to backend wire formats.

Why:
- Provides one stable SDK interface while supporting heterogeneous backend APIs.

## 2026-02-23: Package naming
Decision:
- Use project/package distribution name `oa-sdk-py` for Python-specific release identity.

Why:
- Leaves room for future SDKs in other languages under separate package namespaces.

## 2026-02-23: Concrete provider-direct target
Decision:
- Add OpenAI Responses (`/v1/responses`) as first concrete provider-direct backend target.

Why:
- Provides immediate production usability while preserving generic provider-direct abstraction.

## 2026-02-23: Request-key-first client API
Decision:
- Remove `FlowService` as a public concept and place request_key + inference workflow directly on `OAClient`.

Why:
- Keeps the SDK mentally aligned with `request_key.py` baseline and reduces API surface ambiguity.

## 2026-02-23: Gemini support priority
Decision:
- Add Gemini provider-direct target and Gemini Live API helper (official ephemeral token flow).

Why:
- Gemini is the requested immediate provider-direct target and official live flow supports ephemeral tokens.

## 2026-02-23: Universal core strategy
Decision:
- Maintain explicit deterministic core contract that can be migrated to Rust/Go and bound into multiple languages later.

Why:
- Reduces reimplementation risk and enables faster cross-language SDK rollout.
- Note: superseded by the decision below that selects separate per-language SDK implementations as the default.

## 2026-02-23: Cross-language implementation strategy (JS + Python)
Decision:
- Build JavaScript and Python SDKs as separate native implementations.
- Keep one shared protocol contract and conformance suite across SDKs.
- Do not introduce a mandatory shared Rust/Go/C++ core at this stage.
- If a shared native core is introduced later, limit it to deterministic crypto-critical components.

Why:
- Most current SDK behavior is transport orchestration, API mapping, and language-native ergonomics; these are better implemented directly in each language.
- A shared native core now would add FFI and packaging complexity (npm/pip native build matrix) without enough payoff.
- Shared protocol docs + fixtures + conformance tests provide cross-language consistency with lower delivery risk.

## 2026-02-24: Function-first public API
Decision:
- Make top-level Python public usage function-first via `import oa`.
- Keep service/class surfaces (`OAClient`, `TicketService`, `KeyService`, `InferenceService`) as backend/advanced interfaces.
- Align CLI commands to the same operation model as the function API.

Why:
- Primary user need is a brutally simple and obvious integration path for key request + inference + ticket management.
- The SDK still needs modular internal boundaries and typed implementation internals, but these do not need to be first contact for most users.

## 2026-02-24: Station discovery + no station pin in top-level key helpers
Decision:
- Expose live station discovery in top-level API and CLI:
  - `oa.list_stations(...)`
  - `oa-sdk list-stations`
- Keep top-level key helpers (`oa.request_unlinkable_key(...)`, `oa.request_confidential_key(...)`) as oa-org relay calls without caller-provided station pinning in the simple surface.

Why:
- The SDK should expose actual online stations from oa-org instead of relying on hardcoded IDs in examples.
- Key exchange ownership remains with oa-org as the intermediary station relay.

## 2026-02-25: Explicit endpoint retry policy matrix
Decision:
- Add one centralized retry policy matrix keyed by endpoint semantic intent.
- Wire every transport call site to a named policy instead of ad-hoc booleans.

Why:
- Retry behavior needs to be auditable against idempotency and ticket-consumption risk.
- Centralizing policy reduces accidental unsafe retries when new endpoints are added.

## 2026-02-25: Request-key signature verification helper
Decision:
- Add SDK helper support for verifying `/api/request_key` signatures:
  - station signature payload: `{station_id}|{key}|{expires_at_unix}`
  - org signature payload: `{station_id}|{key}|{expires_at_unix}|{station_signature}`
- Keep Ed25519 verification dependency optional (`pynacl` or `cryptography`).

Why:
- Signature checks are a core hardening step for confidential/verifier workflows.
- Optional dependency keeps base SDK minimal while still enabling strong verification paths.

## 2026-03-15: Live E2E should discover a current OA-supported free OpenRouter model
Decision:
- Treat real-ticket redemption as acceptable for explicit manual end-to-end validation in this repo.
- Add inference-layer OpenRouter catalog helpers and default the live E2E test to the newest free text model that also appears in OA's current model-tier map.
- Keep `OA_E2E_MODEL` as an explicit override for debugging or reproduction.

Why:
- Hardcoded example model IDs drift quickly and create avoidable contributor friction.
- Intersecting OpenRouter free models with OA's live allowlist is safer than assuming every free catalog entry is usable with OA-issued keys.

## 2026-03-15: README onboarding should mirror the two real user entry points
Decision:
- Keep README quickstart centered on the two concrete starting states users actually have:
  - an exported `tickets.json`
  - a redeemable 24-character ticket code
- Keep advanced service/class usage below that quickstart instead of making it first contact.

Why:
- The baseline comparison is the bare `request_key.py` script, which succeeds because it is task-shaped and obvious.
- The SDK already has the necessary simple surface (`oa.request_unlinkable_key`, `oa.add_tickets`), so the remaining usability risk is discovery, not missing functionality.
