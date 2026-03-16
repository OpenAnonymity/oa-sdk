# OA SDK Repository Guidelines

## Scope
This repository contains a Python SDK for The Open Anonymity Project (OA), focused on unlinkable inference workflows from `oa-fastchat` and `request_key.py`:
1. Acquire inference tickets (blind signatures / Privacy Pass flow).
2. Redeem tickets for ephemeral access keys (`/api/request_key`).
3. Make inference calls via backend abstractions.

This SDK must remain minimal, modular, and language-portable.

## Documentation First Policy
Before substantial implementation work:
1. Update `docs/STATUS.md` with planned changes.
2. Update `docs/BACKLOG.md` if priorities change.

After implementation work:
1. Update `docs/STATUS.md` with what shipped, tests run, and remaining risks.
2. Update `docs/DECISIONS.md` for architecture decisions.
3. Update protocol notes in `docs/PROTOCOL.md` if interface behavior changed.

## Agent Continuity Requirements
All future agents must leave clear written continuity for the next contributor.

Required behavior:
1. Document progress in `docs/STATUS.md` before and after meaningful implementation work.
2. Document learnings:
   - Put architecture/product learnings in `docs/DECISIONS.md`.
   - Put protocol/contract learnings in `docs/PROTOCOL.md` when relevant.
3. Keep development TODOs current in `docs/BACKLOG.md`:
   - Add newly discovered work items.
   - Mark completed items as done.
   - Re-prioritize items when priorities change.
4. Include concrete test evidence in `docs/STATUS.md` (commands + outcomes), not just claims.
5. If work is partial, explicitly record remaining risks/blockers and next steps in `docs/STATUS.md`.

## Source of Truth for Workflow
- Primary client workflow references:
  - `request_key.py` in this repo.
  - `oa-fastchat/chat/services/ticketClient.js`.
  - `oa-fastchat/chat/services/privacyPass.js`.
  - `oa-fastchat/chat/services/inference/backends/*.js`.
- Primary server contract references:
  - `oa-org/marketplace/api/request_key.py`
  - `oa-org/marketplace/api/code_redeem.py`
  - `oa-org/auth/ticket_auth.py`
  - `oa-org/chat/api/model_tiering.py`

## Engineering Rules
- Keep public SDK APIs typed and stable.
- Separate concerns by module: transport, tickets, keys, inference.
- Do not bake server internals into SDK behavior.
- Avoid hidden retries for non-idempotent operations.
- Preserve ticket safety: never consume tickets locally unless key redemption succeeds.

## Testing
- Use `pytest`.
- Cover:
  - Ticket import/export compatibility with oa-chat formats.
  - InferenceTicket auth header formatting.
  - Request-key error mapping (especially spent tickets).
  - Backend abstraction behavior for ephemeral/provider-direct/TEE gateway modes.
- Manual/live verification is allowed to redeem real tickets when that is the most direct way to validate the end-to-end flow.
- In this repo, local developers and agents can be liberal about running live E2E tests when changing ticket/key/inference behavior.
- When doing live OA + OpenRouter testing, prefer free OpenRouter models instead of pinning brittle paid examples.
  - Leave `OA_E2E_MODEL` unset in `tests/test_e2e_live.py` to auto-select the newest OA-supported free model from the live OpenRouter catalog.
  - If you need to inspect candidates directly, use `InferenceService.latest_openrouter_free_model(...)` with the OA model-tier allowlist.

## Release Target
Initial release is `0.1.0` once these are complete:
1. ticket import + key request + inference call path works end-to-end.
2. documentation and examples are complete.
3. tests pass in CI-equivalent local run.

## API Priority
- Keep `request_key.py` semantics as the primary workflow baseline.
- Public end-to-end helper should stay explicit as request-key + inference (`OAClient.request_key_and_infer_openrouter`).
