# Cross-SDK Consistency Plan

This document supersedes the previous "universal core first" direction.

## Decision Summary
- JavaScript SDK and Python SDK should be implemented separately in their native ecosystems.
- Cross-language consistency should be enforced through shared protocol contracts and conformance tests.
- A shared native core (Rust/Go/C++) is optional and deferred.

## Shared Source of Truth
Both SDKs must share:
1. `docs/PROTOCOL.md` behavior contracts.
2. Golden fixtures/test vectors for:
   - ticket import/export compatibility,
   - `InferenceTicket` header formatting,
   - request-key response/error mapping,
   - backend-mode request normalization.
3. Conformance tests that run per SDK and validate equivalent behavior.

## What Stays Language-Native
- HTTP transport adapters.
- Retry and timeout behavior wrappers.
- CLI and developer ergonomics.
- Provider-specific integration surfaces.

## Optional Future Native Core (Strict Scope)
Only consider a shared native core if one or more conditions are true:
- repeated parity bugs in deterministic crypto-critical logic across SDKs,
- measurable performance bottlenecks in deterministic local operations,
- security review requires single implementation for high-risk primitives.

If introduced, scope it to deterministic crypto-critical code only (for example ticket parsing/serialization and blinded-token math), not transport or public API orchestration.

## Migration Guardrails
If a shared core is added later:
1. Keep public SDK APIs stable in both languages.
2. Preserve existing fixture/conformance suites as acceptance gates.
3. Avoid introducing hard native build requirements for users unless clearly justified.
