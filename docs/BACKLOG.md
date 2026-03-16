# Backlog

## P0
- [x] Docs baseline (`AGENTS.md`, architecture/protocol/backlog/status/decisions).
- [x] Python package skeleton and typed models.
- [x] Ticket import/export + store semantics compatible with oa-chat exports.
- [x] Key request flow parity with `request_key.py` and oa-fastchat behavior.
- [x] Inference backend abstractions (`ephemeral_key`, `provider_direct`, `tee_gateway`).
- [x] CLI commands for tiers/tickets/keys/inference.
- [x] Tests for parser/header/errors/backends.
- [x] Simplify public interface to top-level function API (`import oa`) and match CLI operations.
- [x] Expose oa-org online station discovery in simple API/CLI and remove station pinning from top-level confidential helper.
- [x] Add request-key signature verification helper (org + station signatures).
- [x] Add retry policy matrix by endpoint idempotency and ticket-consumption risk.
- [ ] Add full async parity for end-to-end request_key + inference workflow.

## P1
- [x] Blind-signature ticket issuance via `privacypass-py`.
- [ ] Async API parity for all sync functions and services.
- [x] Improved retry policy by endpoint idempotency class.
- [x] Add concrete provider-direct target for at least one non-OpenAI provider (Gemini).
- [x] Add OpenRouter catalog helper for free-model discovery in live testing/docs.
- [ ] Finalize TEE gateway auth contract and replace stub assumptions.
- [ ] Expand Gemini live mode beyond single text-turn helper (streaming multimodal sessions).
- [ ] Add shared JS/Python conformance fixture suite (ticket/header/request-key/backend-mode parity).

## P2
- [ ] Optional verifier integration surface.
- [ ] Streaming inference response helpers.
- [ ] Metrics hooks / structured tracing callbacks.
