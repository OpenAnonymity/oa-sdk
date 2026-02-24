# OA SDK Docs Index

This folder is the working memory for SDK development.

## Files
- `docs/IMPLEMENTATION_PLAN.md`: phased roadmap and acceptance criteria.
- `docs/ARCHITECTURE.md`: module boundaries and public API shape.
- `docs/PROTOCOL.md`: client-server contracts used by the SDK.
- `docs/BACKLOG.md`: prioritized work items.
- `docs/STATUS.md`: before/after implementation logs.
- `docs/DECISIONS.md`: architecture decision records.
- `docs/UNIVERSAL_CORE_PLAN.md`: cross-SDK consistency plan (separate SDKs + shared conformance).
- `docs/E2E_TESTING.md`: instructions for live end-to-end testing.
- `docs/MINIMAL_EXAMPLE.md`: shortest `import oa` + CLI usage path.

## Grounding
SDK workflow is explicitly grounded in:
- `request_key.py`
- `oa-fastchat/chat/services/ticketClient.js`
- `oa-fastchat/chat/services/inference/backends/openRouterBackend.js`
- `oa-org/marketplace/api/request_key.py`
- `oa-org/marketplace/api/code_redeem.py`
- `oa-org/auth/ticket_auth.py`
