# MCP Multi-Document / Page Support Spec

## Status
Draft for implementation planning.

## A) Current-State Confirmation
Yes, the current MCP server is effectively hard-coded to one Grist document.

Evidence:
- [mcp-server/grist_client.py](/home/elmunoz42/innovative/grist/grist-sqlite-ec2/mcp-server/grist_client.py#L59) loads a single `GRIST_DOC_ID` from env.
- [mcp-server/grist_client.py](/home/elmunoz42/innovative/grist/grist-sqlite-ec2/mcp-server/grist_client.py#L67) builds all API URLs as `/api/docs/{GRIST_DOC_ID}...`.
- [mcp-server/server.py](/home/elmunoz42/innovative/grist/grist-sqlite-ec2/mcp-server/server.py#L37) requires `GRIST_DOC_ID` at startup and exits if missing.
- Existing tools accept `table_id` only (no `doc_id`), e.g. [mcp-server/tools.py](/home/elmunoz42/innovative/grist/grist-sqlite-ec2/mcp-server/tools.py#L46).

## Goal
Allow MCP clients/agents to work across multiple Grist documents and target different pages/tables without redeploying with a new `GRIST_DOC_ID`.

## Scope
- In scope:
  - Per-request document selection.
  - Optional default document context.
  - Page/table targeting ergonomics.
  - Backward compatibility for existing clients.
- Out of scope:
  - End-user UI changes in Grist web app.
  - Full RBAC beyond existing API key permissions.

## Design Principles
- Keep current tools working with no client changes.
- Require explicit allowlist of documents for safety.
- Prefer additive schema changes (optional new args).

## Proposed API Changes

### 1) Add Optional `doc_id` Argument to All Existing Tools
Affected tools:
- `grist_list_tables`
- `grist_list_records`
- `grist_create_records`
- `grist_update_records`
- `grist_delete_records`

Rules:
- If `doc_id` provided: use it.
- Else fallback to active context doc (if set).
- Else fallback to `GRIST_DOC_ID` (legacy default).

### 2) Add Document Context Tools
- `grist_set_context`
  - Args: `doc_id` (required)
  - Behavior: set active document for this server process.
- `grist_get_context`
  - Returns active `doc_id` and fallback/default doc.

Note:
- For single-tenant demo use, process-wide context is acceptable.
- If multi-tenant clients are expected later, context must move to per-auth-token or per-session storage.

### 3) Add Document Discovery Tool (Allowlist-Backed)
- `grist_list_docs`
  - Returns list of allowed docs with labels.
  - Reads from env config (proposed):
    - `GRIST_ALLOWED_DOCS_JSON`
    - Example:
      `[{"id":"docA123","name":"Demo Sales"},{"id":"docB456","name":"Demo Ops"}]`

Rationale:
- Avoid relying on uncertain org/workspace listing endpoints.
- Enforces explicit document boundary for MCP operations.

### 4) Add Page-Friendly Access
MVP interpretation:
- In Grist API operations here, "page" is table-oriented for CRUD.
- Add optional `page_id` alias on record tools.

Rules:
- If `table_id` provided, use it.
- Else if `page_id` provided, treat as `table_id`.
- Else error.

Add helper tool:
- `grist_list_pages`
  - Args: optional `doc_id`
  - Returns table list as page candidates (`id`, `name`).

## Internal Refactor
- Update `make_grist_request(...)` signature:
  - Add optional `doc_id: Optional[str] = None`.
  - Resolve effective doc via resolver function.
- Add resolver utilities:
  - `get_allowed_doc_ids()`
  - `resolve_doc_id(request_doc_id)`
  - `get_active_context_doc_id()` / setter.
- Centralize validation:
  - Reject doc IDs not in allowlist (if allowlist configured).

## Backward Compatibility
- Keep `GRIST_DOC_ID` required for initial rollout, used as default.
- Existing tool calls without `doc_id` remain unchanged.
- New args are optional and additive.

## Security Requirements
- Enforce document allowlist if `GRIST_ALLOWED_DOCS_JSON` is set.
- Never accept arbitrary doc IDs when allowlist exists.
- Keep MCP auth unchanged (`MCP_AUTH_TOKEN`).
- Avoid exposing sensitive metadata beyond configured doc labels/IDs.

## Error Handling
- Missing/invalid `doc_id`:
  - `ValueError("doc_id is not allowed")` or `ValueError("doc_id is required")` when no fallback.
- Both `table_id` and `page_id` missing:
  - `ValueError("table_id or page_id is required")`.
- Unknown page/table:
  - keep existing 404 translation behavior.

## Test Plan
- Unit tests:
  - Resolver precedence: `doc_id arg` > context > env default.
  - Allowlist acceptance/rejection.
  - `page_id` alias behavior.
- Tool tests:
  - All CRUD tools run against two docs by passing different `doc_id`.
  - Existing calls without `doc_id` still work.
- Integration:
  - Smoke test with two real docs and one blocked doc.

## Rollout Plan
1. Add resolver + allowlist parsing utilities.
2. Update Grist client request function for dynamic doc routing.
3. Extend tool schemas/handlers with optional `doc_id` and `page_id` alias logic.
4. Add new context/discovery/page helper tools.
5. Update MCP docs and examples.
6. Run tests and deploy.

## Example Usage (Target)
```json
{
  "name": "grist_list_records",
  "arguments": {
    "doc_id": "docB456",
    "table_id": "Customers",
    "limit": 20
  }
}
```

```json
{
  "name": "grist_set_context",
  "arguments": {
    "doc_id": "docA123"
  }
}
```
