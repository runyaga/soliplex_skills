# PLAN_SKILLS.md Review Feedback

## Iteration 1: Pre-Implementation Review (Gemini 3 Pro)

### Findings

| ID | Section | Issue | Severity |
|:---|:---|:---|:---|
| 1 | `tools.py` | **Tool Signature Pattern:** Gemini flagged potential conflict if tools need both `ctx` and `tool_config`. However, PLAN_SKILLS.md consistently uses `tool_config` pattern for ALL tools, which is valid. The upstream pydantic-ai-skills `ctx` parameter is optional. | **Clarified** |
| 2 | `config.py` | **Path Resolution Bug:** `from_yaml` does not resolve relative paths in `directories` against `config_path.parent`. If two rooms use `directories: "./skills"`, they'll have identical cache keys despite different physical locations. | **High** |
| 3 | `pyproject.toml` | **Import Dependency:** `soliplex.config.ToolConfig` is imported at module level, but `soliplex` is optional dependency. Package won't import without Soliplex installed. | **Medium** |
| 4 | `tools.py` | **Missing ToolReturn:** Soliplex tools often return `ToolReturn` for rich metadata. The plan returns simple strings. Acceptable for V1 but limits error handling. | **Low** |

### Key Clarifications

1. **Tool Config Pattern**: Soliplex supports TWO patterns:
   - Pattern A: `ctx: RunContext[AgentDependencies]` → access `ctx.deps.tool_configs[kind]`
   - Pattern B: `tool_config: ToolConfig` → Soliplex curries it via `functools.partial`

   PLAN_SKILLS.md uses Pattern B consistently for all 4 tools. This is valid because:
   - pydantic-ai-skills `ctx` parameter is optional in `load()` and `run()`
   - Avoids ToolRequirementConflict
   - Simpler implementation

2. **Repeated Config in YAML**: Each tool entry needs `directories` if overriding. This is standard Soliplex pattern (see haiku room_config.yaml where each tool has its own config).

### Required Changes Before Implementation

1. **Fix Path Resolution in `from_yaml()`**:
```python
@classmethod
def from_yaml(cls, installation_config, config_path, config):
    env_settings = _get_env_settings()

    # Resolve directories relative to config_path
    raw_dirs = config.get("directories", env_settings.directories)
    resolved_dirs = []
    for d in raw_dirs.split(","):
        d = d.strip()
        if not d:
            continue
        path = pathlib.Path(d)
        if not path.is_absolute() and config_path:
            path = (config_path.parent / path).resolve()
        resolved_dirs.append(str(path))

    return cls(
        tool_name=config.get("tool_name", ""),
        directories=",".join(resolved_dirs),  # Store resolved absolute paths
        # ... rest
    )
```

2. **Consider Conditional Import for Soliplex**:
```python
# In config.py
try:
    from soliplex.config import ToolConfig
except ImportError:
    # Provide stub for standalone testing
    @dataclasses.dataclass
    class ToolConfig:
        tool_name: str = ""
        _installation_config: Any = None
        _config_path: pathlib.Path = None
```

---

## Iteration 2: Critic Mode (Gemini 3 Pro)

### Findings

| ID | Category | Issue | Severity | Recommendation |
|:---|:---|:---|:---|:---|
| 1 | Functionality | **Context Propagation Blocked:** Soliplex's `ToolRequirementConflict` prevents tools from accepting both `tool_config` and `ctx`. Cannot pass `ctx` to upstream skills that need RunContext. | High | Document limitation: "Context-aware skill scripts not supported in V1." The upstream `ctx` is optional. |
| 2 | Error Handling | **Uncaught Exceptions:** `tools.py` functions do not catch exceptions from adapter. Propagates as generic failures rather than descriptive errors. | High | Wrap adapter calls with `try/except` for known exceptions, return user-friendly error strings. |
| 3 | Caching | **Stale Content:** `_toolset_cache` persists indefinitely. New skills added at runtime won't be visible until restart. | Medium | Document limitation or add cache invalidation mechanism. |
| 4 | Configuration | **Split-Brain Risk:** Typo in `directories` for one tool (e.g., `./skillz` vs `./skills`) creates disjoint toolsets. Agent sees skills it cannot load. | Medium | Consider logging warning if toolset configs diverge unexpectedly. |
| 5 | Thread Safety | **Unsafe Cleanup:** `close_all()` modifies `_toolset_cache` without acquiring `_cache_lock`. Race condition risk. | Low | Make `close_all()` async or acquire lock before clearing. |
| 6 | Testing | **Negative Testing Gap:** Test plan misses error conditions (non-existent skill, script failures). | Medium | Add test cases for `SkillNotFoundError`, `SkillResourceNotFoundError`, script exceptions. |

### Action Items from Iteration 2

1. **Exception Handling in tools.py**:
```python
from pydantic_ai_skills import SkillNotFoundError, SkillResourceNotFoundError

async def load_skill(tool_config: SkillsToolConfig, skill_name: str) -> str:
    try:
        adapter = await _get_adapter(tool_config)
        return await adapter.load_skill(skill_name)
    except SkillNotFoundError:
        available = ", ".join(sorted((await _get_adapter(tool_config)).skills.keys()))
        return f"Skill '{skill_name}' not found. Available skills: {available or 'none'}"
```

2. **Thread-safe close_all()**:
```python
async def close_all() -> None:
    async with _cache_lock:
        _toolset_cache.clear()
```

3. **Document Limitations** in README:
   - Skills using RunContext-aware scripts/resources not supported
   - Cache requires restart to pick up new skills
   - All tools in a room should use same `directories` value

---

## Iteration 3: Final Implementation Readiness (Gemini 3 Pro)

### Verdict: YELLOW - Implement with Fixes

The plan is ready for implementation IF the fixes from iterations 1-2 are applied during coding.

### Implementation Order

1. `exceptions.py` - Base dependency, no imports
2. `config.py` - Path resolution + optional soliplex import
3. `adapter.py` - Thread-safe close_all()
4. `tools.py` - Error handling wrappers
5. `__init__.py` - Exports

### Critical Fixes to Apply

**1. Path Resolution in config.py** (supports per-room skills directories):
```python
raw_dirs = config.get("directories", env_settings.directories)
resolved_dirs = []
for d in raw_dirs.split(","):
    d = d.strip()
    if not d:
        continue
    path = pathlib.Path(d)
    if not path.is_absolute() and config_path:
        path = (config_path.parent / path).resolve()
    resolved_dirs.append(str(path))
```

**2. Optional Soliplex Import in config.py**:
```python
try:
    from soliplex.config import ToolConfig
except ImportError:
    @dataclasses.dataclass
    class ToolConfig:
        tool_name: str = ""
        _installation_config: Any = None
        _config_path: pathlib.Path | None = None
```

**3. Async close_all() in adapter.py**:
```python
async def close_all() -> None:
    async with _cache_lock:
        _toolset_cache.clear()
```

**4. Error Handling in tools.py**:
```python
async def load_skill(tool_config: SkillsToolConfig, skill_name: str) -> str:
    try:
        adapter = await _get_adapter(tool_config)
        return await adapter.load_skill(skill_name)
    except SkillNotFoundError:
        adapter = await _get_adapter(tool_config)
        available = ", ".join(sorted(adapter.skills.keys())) or "none"
        return f"Error: Skill '{skill_name}' not found. Available: {available}"
```

### Test Strategy for Phase 1

1. **Config path resolution** - verify relative paths resolve against config location
2. **Error propagation** - mock adapter, verify tools return error strings not exceptions
3. **Optional dependency** - verify config.py loads without soliplex installed
4. **Negative cases** - SkillNotFoundError, SkillResourceNotFoundError

### Documented Limitations (for README)

- RunContext-aware skill scripts/resources not supported in V1
- Cache persists until restart (new skills require restart)
- All tools in a room should use consistent `directories` value
