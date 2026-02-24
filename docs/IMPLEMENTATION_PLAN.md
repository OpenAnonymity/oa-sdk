# Implementation Plan

## Principles
- Docs-first development and change tracking.
- Strong module boundaries: tickets, keys, inference, transport.
- Ergonomic API with explicit behavior and predictable errors.
- Language-portable architecture (Python first, cross-language ready).

## Phases

### Phase 0: Repository + Docs Bootstrap
- Create `AGENTS.md` and docs baseline.
- Record protocol assumptions and open questions.
- Define initial package and test layout.

Acceptance:
- Docs can onboard a new engineer without external context.

### Phase 1: SDK Skeleton
- Create Python package with typed public API.
- Add transport layer + retry semantics + error taxonomy.
- Add tests for baseline behaviors.

Acceptance:
- `pytest` runs and validates core parsing/utilities.

### Phase 2: Ticket Handling (Import/Store/Header)
- Support oa-chat export formats for active/archived tickets.
- Build `InferenceTicket` authorization header exactly as OA expects.
- Add ticket reservation/consume semantics.

Acceptance:
- Compatible with `request_key.py` + `oa-fastchat` ticket JSON shapes.

### Phase 3: Key Request Flow
- Implement model tier fetch (`/chat/model-tickets`).
- Implement key request (`/api/request_key`) with robust errors.
- Map spent-ticket cases to explicit SDK error.

Acceptance:
- End-to-end: load tickets -> request key -> structured `KeyLease` response.

### Phase 4: Ticket Issuance (Blind Signature)
- Integrate `privacypass-py` as optional dependency.
- Implement public-key fetch + blinding + `/api/alpha-register` + finalize.
- Output finalized tickets compatible with store.

Acceptance:
- End-to-end: code redeem -> finalized tickets stored locally.

### Phase 5: Inference Abstractions
- Implement backend abstraction family aligned with `oa-fastchat` and OpenResponses pattern:
  - Ephemeral key backend.
  - Provider-direct backend.
  - TEE gateway backend.
- Provide OpenResponses-like `responses.create(...)` API.
- Provide at least one concrete provider-direct production target.

Acceptance:
- One call path can target different backend kinds by configuration.

### Phase 6: CLI + Examples + Hardening
- Add CLI commands for tiers/tickets/key/inference.
- Add usage examples.
- Improve tests and docs for release.

Acceptance:
- `0.1.0` candidate with docs + examples + test baseline.

## Risks
- API response fields may evolve; parser must be tolerant.
- Blind-signature challenge structure can be implementation-sensitive.
- Inference backends vary by auth semantics; abstraction must remain explicit.
