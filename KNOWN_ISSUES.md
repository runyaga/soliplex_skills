# Soliplex Upstream Known Issues

Issues discovered during comprehensive code review that require fixes in `github.com/soliplex/soliplex`.

## Critical Issues

### 1. Data Loss on Client Disconnect (AG-UI Streaming)

**Location:** `views/agui.py` - `tee_events` function

**Problem:**
```python
async def tee_events(...):
    async for event in event_stream:
        yield event  # <--- If client disconnects, this raises/closes

    # This line is UNREACHABLE on disconnect/error
    await on_done(events=event_list)
```

**Impact:** If user closes browser during SSE stream, `RunEvents` are NEVER saved to database. Run record exists but history is lost.

**Fix Required:** Wrap loop in `try...finally` to ensure `on_done` is called even on disconnect.

---

### 2. Agent Caching Contradicts Documentation

**Location:** `agents.py` - `get_agent_from_configs`, `_agent_cache`

**Problem:**
- Documentation claims "Soliplex creates a NEW ToolConfig instance for every tool call"
- Reality: Agents are CACHED in `_agent_cache` with ToolConfigs frozen via `functools.partial`
- `get_agent_from_configs` ignores `tool_configs` argument if agent already cached

**Impact:**
- Dynamic/per-request configs (user-specific API keys) DON'T WORK with standard Adapter Pattern
- Config updates require cache clear or server restart

**Fix Required:** Either update documentation to match behavior, or implement proper config refresh mechanism.

---

### 3. Public-by-Default Rooms with Ephemeral Authorization

**Location:** `authz/schema.py`

**Problem:**
1. If NO RoomPolicy exists for a room → access ALLOWED (public by default)
2. Default `room_authz_dburi` uses IN-MEMORY SQLite
3. Server restart WIPES all policies → all rooms revert to PUBLIC

**Impact:** Security vulnerability - users think rooms are secured but restart exposes them.

**Fix Required:**
- Consider deny-by-default for rooms without policies
- Warn loudly when using in-memory authz DB
- Or require explicit `room_authz_dburi` configuration

---

### 4. JWT Audience Validation Disabled

**Location:** `authn.py` - `validate_access_token`

**Problem:**
```python
jwt.decode(..., options={"verify_aud": False})
```

**Impact:** Soliplex accepts ANY valid JWT signed by the OIDC provider, even tokens issued for different applications. Token substitution attack risk.

**Fix Required:** Enable audience validation or document the security implications.

---

### 5. Multi-Worker Session Breakage

**Location:** `authn.py` - `_get_session_secret_key`, `main.py` - `app_with_session`

**Problem:**
- If `SESSION_SECRET_KEY` not set, generates random key via `os.urandom(16)`
- `create_app` runs per worker process → each worker gets DIFFERENT secret
- Session cookie from Worker 1 invalid on Worker 2

**Impact:** Random logouts in multi-worker deployments.

**Fix Required:** Either require `SESSION_SECRET_KEY` in production or generate once and share across workers.

---

### 6. MCP Server Broken for Configurable Tools

**Location:** `mcp_server.py`

**Problem:**
- Tools using Pattern A (tool_config argument) exposed via `fmcp_tools.Tool.from_function(tool_config.tool)`
- If tool NOT registered in `MCP_TOOL_CONFIG_WRAPPERS_BY_TOOL_NAME`:
  - Raw function exposed asking for `tool_config`
  - External MCP client cannot provide it → TypeError on call

**Impact:** MCP Server silently broken for most configurable tools.

**Fix Required:** Auto-generate wrappers for Pattern A tools or fail loudly at startup.

---

### 7. Ollama Client Blocks Event Loop

**Location:** `ollama.py`

**Problem:**
- Uses synchronous `requests` and `urllib.request` libraries
- No `async` anywhere in the module
- 600s timeout on `pull_model`

**Impact:** Calling from async views blocks entire event loop, freezing server.

**Fix Required:** Rewrite with `httpx` or `aiohttp` for async operation.

---

### 8. Ollama Streaming Implementation Broken

**Location:** `ollama.py` - `_post_endpoint`

**Problem:**
```python
response = requests.post(...)
return response.json()  # Reads full body, expects single JSON
```
But Ollama streams multiple JSON objects when `stream=True`.

**Impact:** `pull_model` with `stream=True` hangs or crashes.

**Fix Required:** Implement proper streaming JSON parsing or remove stream support.

---

## Medium Issues

### 9. Thinking Events Not Persisted (Live vs Replay Discrepancy)

**Location:** `agui/persistence.py` - `SKIP_EVENT_TYPES`, `agui/__init__.py` - `compact_event_stream`

**Problem:**
- `THINKING_TEXT_MESSAGE_CONTENT` streamed live to client
- But filtered out in `Run.list_events` persistence

**Impact:** Users see "Thinking" live, refresh page → "Thinking" disappears. Inconsistent UX.

**Fix Required:** Document behavior or provide option to persist thinking events.

---

### 10. JSON Patch Crashes Parser

**Location:** `agui/parser.py` - `EventStreamParser`

**Problem:**
- `STATE_DELTA` applies `jsonpatch.apply_patch`
- No try/except around patch application
- Patching non-existent path → exception crashes parser

**Impact:** Malformed state delta events crash the request.

**Fix Required:** Add error handling around jsonpatch operations.

---

### 11. Blocking Chunk Visualization

**Location:** `views/rooms.py` - `get_chunk_visualization`

**Problem:**
- Heavy blocking I/O (PIL images, Base64 encoding) in `async def` handler
- No `run_in_executor` or async image library

**Impact:** Blocks event loop during visualization generation.

**Fix Required:** Offload to thread pool or use async image processing.

---

### 12. MCP Client No Tool Caching

**Location:** `mcp_client.py`

**Problem:**
- `list_tools()` fetches from upstream MCP server on EVERY call
- Explicitly decided not to cache

**Impact:** Network latency added to every agent run using MCP tools.

**Fix Required:** Consider optional tool caching with TTL.

---

### 13. MCP Token No Revocation

**Location:** `mcp_auth.py`

**Problem:**
- Symmetric tokens valid until expiry (default 3600s)
- No revocation mechanism

**Impact:** Cannot invalidate compromised MCP tokens except by rotating `URL_SAFE_TOKEN_SECRET` (invalidates ALL tokens).

**Fix Required:** Consider token blacklist or shorter expiry with refresh.

---

### 14. Inconsistent Admin Auth

**Location:** `views/installation.py`

**Problem:**
- `get_installation_git_metadata` SKIPS `check_admin_access`
- All other installation endpoints require admin

**Impact:** Security inconsistency.

**Fix Required:** Add admin check to `get_installation_git_metadata` or document why it's public.

---

### 15. Unauthenticated Debug Endpoints

**Location:** `views/streaming.py`

**Problem:**
- `/ssetest` and `/wstest` have NO authentication
- Appear to be development debug endpoints

**Impact:** Potential information leakage or abuse in production.

**Fix Required:** Remove from production builds or add authentication.

---

## Documentation Gaps (Not Code Bugs)

These don't require code fixes but need documentation:

1. **25+ AG-UI event types** - docs show only 4
2. **Tool signature patterns** - Pattern A (frozen) vs Pattern B (runtime ctx)
3. **Authorization schema** - AdminUser, RoomPolicy, ACLEntry tables
4. **MCP client configuration** - `mcp_client_toolsets` structure
5. **CLI command reference** - maintenance and authz commands
6. **Production deployment** - SESSION_SECRET_KEY, multi-worker, reload behavior

---

## Review Metadata

- **Review Date:** 2026-02-01
- **Source Version:** Upstream at `~/dev/soliplex-upstream/src/soliplex/`
- **Methodology:** 7-group iterative review (Analysis → Critic → Synthesis)
- **Full Findings:** See `PLAN_COMPREHENSIVE_REVIEW.md`
