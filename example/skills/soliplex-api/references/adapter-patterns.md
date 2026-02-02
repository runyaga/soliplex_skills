# Adapter Patterns for Soliplex

This document describes patterns for building adapters that integrate external libraries with Soliplex.

## What is an Adapter?

An **adapter** bridges an external library's functionality into Soliplex's tool system. It translates between:

```text
External Library API  ←→  Adapter  ←→  Soliplex ToolConfig
```

## Critical Requirements

### tool_name Must Be a Dotted Import Path

**CRITICAL**: Soliplex's `ToolConfig.tool` property uses dynamic import:

```python
# soliplex/config.py line ~360
module_name, tool_id = self.tool_name.rsplit(".", 1)
module = importlib.import_module(module_name)
self._tool = getattr(module, tool_id)
```

This means `tool_name` **MUST** be a valid Python dotted path like:
- ✅ `my_adapter.tools.my_function`
- ✅ `soliplex_todo.tools.add_todo`
- ❌ `my-tool` (no dot - will crash!)
- ❌ `my_adapter` (no function name - will crash!)

### Tool Naming Strategy - Avoid Collisions

**WARNING: Soliplex identifies tools by function name only.**

When Soliplex loads tools, it uses only the *last part* of the dotted path (the function name) as the tool's key:

```python
# soliplex/config.py line ~316
_, kind = self.tool_name.rsplit(".", 1)
# tool_configs[kind] = tool_config  # Keys by function name only!
```

This means:
- `adapter_a.tools.search` → key: `search`
- `adapter_b.tools.search` → key: `search`

**If you load both tools in the same room, the second silently overwrites the first!**

**Solution: Always use unique, prefixed function names:**

```python
# BAD - Generic names will collide
async def search(tool_config: MyConfig, query: str): ...
async def query(tool_config: MyConfig, text: str): ...

# GOOD - Prefixed names are safe
async def todo_search(tool_config: TodoConfig, query: str): ...
async def weather_query(tool_config: WeatherConfig, text: str): ...
```

### Tool Function Signature Patterns

Soliplex supports two distinct patterns for tool configuration access:

**Pattern A: Frozen Configuration (Standard Adapter Pattern)**

```python
async def my_tool(
    tool_config: MyToolConfig,  # Injected via functools.partial at startup
    query: str,
) -> str:
    """Tool description shown to LLM."""
    return f"Connecting to {tool_config.endpoint}..."
```

- **Pros**: Simple signature, easy to test
- **Cons**: Config frozen at Agent creation time (see Agent Caching below)
- **Best for**: Static configurations that don't change per-request

**Pattern B: Runtime Context (Dynamic)**

```python
from pydantic_ai import RunContext
from soliplex.agents import AgentDependencies

async def my_tool(
    ctx: RunContext[AgentDependencies],
    query: str,
) -> str:
    """Tool description shown to LLM."""
    # Access config dynamically from run dependencies
    tool_config = ctx.deps.tool_configs["my_adapter.tools.my_tool"]
    user = ctx.deps.user
    return f"User {user.email} connecting to {tool_config.endpoint}..."
```

- **Pros**: Bypasses Agent Caching, access to per-request state (User, Installation)
- **Cons**: More complex signature, tool_name must match exactly
- **Best for**: User-specific configs, dynamic settings

⚠️ **Note**: Pattern B tools using `FASTAPI_CONTEXT` are **excluded from MCP Server exposure**.

## The Adapter Pattern

### 1. Create Tool Functions in tools.py

```python
# my_adapter/tools.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_adapter.config import MyToolConfig

async def query_service(
    tool_config: MyToolConfig,
    query: str,
) -> dict | str:
    """Query the external service.

    Args:
        query: The search query.

    Returns:
        Query results or error message string.
    """
    try:
        # Lazy import external library
        from external_lib import Client

        client = Client(tool_config.api_key, tool_config.endpoint)
        return client.query(query)
    except Exception as e:
        return f"Error: {e}"
```

### 2. Create ToolConfig in config.py

```python
# my_adapter/config.py
import dataclasses
import pathlib
from typing import Any

# Handle optional soliplex dependency
try:
    from soliplex.config import ToolConfig
except ImportError:
    @dataclasses.dataclass
    class ToolConfig:
        """Stub for standalone testing."""
        tool_name: str = ""
        _installation_config: Any = None
        _config_path: pathlib.Path | None = None

        @classmethod
        def from_yaml(cls, installation_config, config_path, config):
            config["_installation_config"] = installation_config
            config["_config_path"] = config_path
            return cls(**config)


@dataclasses.dataclass
class MyToolConfig(ToolConfig):
    """Configuration for my external service integration."""

    # CRITICAL: Must be a dotted path to the tool function
    tool_name: str = "my_adapter.tools.query_service"

    # Your configuration fields
    api_key: str = ""
    endpoint: str = "https://api.example.com"

    @classmethod
    def from_yaml(
        cls,
        installation_config: Any,
        config_path: pathlib.Path,
        config: dict[str, Any],
    ) -> "MyToolConfig":
        """Create from Soliplex YAML configuration.

        IMPORTANT: Secrets and relative paths are NOT automatically resolved.
        You must handle them explicitly in this method.
        """
        # 1. Resolve secrets - YAML `secret:MY_KEY` stays literal without this!
        api_key = config.get("api_key", "")
        if api_key.startswith("secret:"):
            secret_name = api_key.replace("secret:", "")
            api_key = installation_config.get_secret(secret_name)

        # 2. Resolve relative file paths (if your config needs file references)
        cert_path = config.get("cert_path")
        if cert_path:
            cert_path = str((config_path.parent / cert_path).resolve())

        return cls(
            tool_name=config.get("tool_name", cls.tool_name),  # Use class default
            api_key=api_key,
            endpoint=config.get("endpoint", "https://api.example.com"),
            _installation_config=installation_config,
            _config_path=config_path,
        )
```

### 3. Create Per-Tool Config Classes

If your adapter provides multiple tools, create a config class for each:

```python
# my_adapter/config.py (continued)

@dataclasses.dataclass
class QueryServiceConfig(MyToolConfig):
    """Config for query_service tool."""
    tool_name: str = "my_adapter.tools.query_service"


@dataclasses.dataclass
class UpdateServiceConfig(MyToolConfig):
    """Config for update_service tool."""
    tool_name: str = "my_adapter.tools.update_service"


@dataclasses.dataclass
class DeleteServiceConfig(MyToolConfig):
    """Config for delete_service tool."""
    tool_name: str = "my_adapter.tools.delete_service"
```

### 4. Register with Soliplex Installation

In your Soliplex `installation.yaml`:

```yaml
id: my-installation

meta:
  tool_configs:
    - my_adapter.QueryServiceConfig
    - my_adapter.UpdateServiceConfig
    - my_adapter.DeleteServiceConfig
```

### 5. Configure in Room YAML

```yaml
# room_config.yaml
id: my-room
name: My Room

tools:
  - tool_name: my_adapter.tools.query_service
    api_key: ${MY_API_KEY}
    endpoint: https://api.example.com

  - tool_name: my_adapter.tools.update_service
    api_key: ${MY_API_KEY}
    endpoint: https://api.example.com
```

## Complete Example: soliplex-todo

The [soliplex-todo](https://github.com/runyaga/soliplex-todo) adapter demonstrates this pattern:

### Package Structure

```
soliplex-todo/
├── src/soliplex_todo/
│   ├── __init__.py      # Export configs and tools
│   ├── config.py        # TodoToolConfig + per-tool configs
│   └── tools.py         # add_todo, read_todos, etc.
├── tests/
│   ├── test_config.py   # Config unit tests
│   ├── test_tools.py    # Tool unit tests (mocked)
│   └── test_integration.py  # Full integration tests
└── example/
    ├── installation.yaml
    └── rooms/
```

### tools.py Pattern

```python
async def add_todo(
    tool_config: TodoToolConfig,
    content: str,
    parent_id: str | None = None,
) -> dict[str, Any] | str:
    """Add a new todo item."""
    try:
        storage = await _get_storage(tool_config)
        # ... implementation
        return {"id": todo.id, "content": todo.content}
    except Exception as e:
        return f"Error: Failed to add todo: {e}"
```

### config.py Pattern

```python
@dataclasses.dataclass
class TodoToolConfig(ToolConfig):
    tool_name: str = "soliplex_todo.tools.add_todo"
    storage: Literal["memory", "postgres"] = "memory"
    # ... other fields

@dataclasses.dataclass
class AddTodoConfig(TodoToolConfig):
    tool_name: str = "soliplex_todo.tools.add_todo"

@dataclasses.dataclass
class ReadTodosConfig(TodoToolConfig):
    tool_name: str = "soliplex_todo.tools.read_todos"
```

## Adapter Design Principles

### 1. Configuration Over Code

Put integration details in YAML, not hardcoded:

```yaml
# Good: Configurable
tools:
  - tool_name: my_adapter.tools.query
    connection_string: ${DATABASE_URL}
    max_connections: 10
```

### 2. Agent Caching and Config Lifecycle

⚠️ **CRITICAL WARNING**: Soliplex caches Agents by Room ID in `_agent_cache`.

**How it works:**
1. **Agent Creation**: First request to a room creates Agent via `get_agent_from_configs`
2. **Tool Freezing**: Pattern A tools have `tool_config` baked via `functools.partial`
3. **Caching**: Agent stored in cache, subsequent requests reuse it

**Implications:**
- **Pattern A**: Config updates won't apply until cache cleared/server restarted
- **Pattern B**: `ctx.deps.tool_configs` passed fresh every `agent.run()` - always sees latest

**When to use each pattern:**
- Pattern A: Static configs (API endpoints, credentials that don't change)
- Pattern B: Dynamic configs (user-specific API keys, per-request settings)

### 3. Resource Caching - Critical for Connections

Even though Agents are cached, you should still cache expensive resources:

**Correct approach (cache by connection parameters with thread safety):**
```python
import asyncio
from typing import Any

_resource_cache: dict[tuple, Any] = {}
_init_lock = asyncio.Lock()

async def _get_client(config: MyToolConfig) -> DatabaseClient:
    """Get or create cached client for this config."""
    # Build cache key from actual connection values
    cache_key = (
        config.dsn,
        config.database,
    )

    async with _init_lock:  # Thread-safe initialization
        if cache_key not in _resource_cache:
            client = DatabaseClient(config.dsn, config.database)
            await client.connect()  # Initialize once
            _resource_cache[cache_key] = client

    return _resource_cache[cache_key]

async def my_tool(tool_config: MyConfig, query: str) -> str:
    client = await _get_client(tool_config)  # Reuses cached connection
    return await client.query(query)
```

**Why cache by values, not `id(config)`**: Multiple ToolConfig classes (e.g., `AddTodoConfig`, `ReadTodosConfig`) may share the same connection settings. Caching by values ensures connection reuse across tools.

### 5. Lazy Loading

Don't import external libraries until needed:

```python
async def my_tool(tool_config: MyConfig, query: str) -> str:
    # Import here, not at module level
    from heavy_library import Client
    ...
```

### 4. Error Handling - Wiring vs Runtime

Distinguish between wiring errors (missing config) and runtime errors (transient failures):

```python
async def my_tool(tool_config: MyConfig, query: str) -> dict | str:
    # 1. Wiring Check (RAISE for missing config - this is a setup error)
    if tool_config is None:
        raise ValueError("Tool configuration missing - check room config")

    try:
        result = await client.search(query)
        return {"success": True, "data": result}
    except TimeoutError:
        # 2. Runtime Error (RETURN string for LLM recovery)
        return "Error: The search service timed out. Please try again later."
    except NotFoundException:
        return "Error: Item not found."  # LLM can understand this
    except Exception as e:
        return f"Error: Unexpected failure: {e}"
```

**Key distinction:**
- **Wiring errors** (missing config, bad setup): RAISE - crashes the run, operator must fix
- **Runtime errors** (timeouts, not found): RETURN string - LLM can recover or inform user

### 6. Validation at Config Time

Validate in `__post_init__`:

```python
@dataclasses.dataclass
class MyConfig(ToolConfig):
    storage: str = "memory"
    postgres_dsn: str | None = None

    def __post_init__(self):
        if self.storage == "postgres" and not self.postgres_dsn:
            raise ValueError("postgres_dsn required when storage='postgres'")
```

### 7. Use TYPE_CHECKING for Circular Imports

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_adapter.config import MyToolConfig

async def my_tool(tool_config: "MyToolConfig", ...) -> str:
    ...
```

**Why this works:** Soliplex uses `functools.partial` and rewrites `__signature__` to hide the `tool_config` parameter from pydantic-ai. The LLM never sees `tool_config` - it's injected before the tool reaches the AI. This means pydantic-ai doesn't need to inspect the type hint at runtime.

```python
# What Soliplex does internally (config.py):
def tool_with_config(self):
    """Wrap tool function with config pre-injected."""
    tool_w_config = functools.partial(self.tool, tool_config=self)

    # Rewrite signature to hide tool_config from pydantic-ai
    orig_sig = inspect.signature(self.tool)
    new_params = [p for p in orig_sig.parameters.values() if p.name != "tool_config"]
    tool_w_config.__signature__ = orig_sig.replace(parameters=new_params)

    return tool_w_config
```

### 8. Understand create_toolset() vs Soliplex Loading

The `create_toolset()` method in your config class is **NOT called by Soliplex**. Soliplex loads tools individually via the `tool_name` path and `tool_with_config()`.

**When create_toolset() IS useful:**
- Unit testing your adapter outside of Soliplex
- Standalone scripts using raw pydantic-ai
- Integration tests without a full Soliplex server

```python
# Standalone usage (outside Soliplex)
from my_adapter.config import MyToolConfig

config = MyToolConfig(api_key="test-key")
tools = config.create_toolset()  # Returns list of pydantic-ai Tool objects

# Use with pydantic-ai directly
from pydantic_ai import Agent
agent = Agent("openai:gpt-4", tools=tools)
```

## Testing Adapters

### Unit Tests (Mocked)

```python
@pytest.mark.asyncio
async def test_add_todo_success(mock_storage):
    config = MyToolConfig(storage="memory")

    with patch("my_adapter.tools._get_storage") as mock:
        mock.return_value = mock_storage
        result = await my_tool(config, query="test")

    assert result["success"] is True
```

### Integration Tests (Real Library)

```python
@pytest.mark.asyncio
async def test_full_workflow():
    config = MyToolConfig(storage="memory")

    # Add
    result = await add_item(config, content="Test")
    item_id = result["id"]

    # Read
    items = await read_items(config)
    assert len(items) == 1

    # Delete
    await remove_item(config, item_id=item_id)
```

### Test tool_name Format

```python
def test_tool_name_has_dot():
    """tool_name must have a dot for Soliplex import."""
    config = MyToolConfig()
    assert "." in config.tool_name

    # Verify it can be parsed
    module_name, tool_id = config.tool_name.rsplit(".", 1)
    assert module_name == "my_adapter.tools"
    assert tool_id  # Not empty
```

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| `tool_name = "my-tool"` | No dot, crashes `rsplit` | Use `my_adapter.tools.my_tool` |
| Raising runtime exceptions | LLM can't recover | Return error strings for runtime errors |
| Module-level imports | Slows config loading | Lazy import in functions |
| Missing `from_yaml` | YAML config fails | Implement classmethod |
| Hardcoded `tool_name` in `from_yaml` | Subclasses broken | Use `cls.tool_name` |
| Dynamic configs with Pattern A | Configs frozen at startup | Use Pattern B for per-request configs |
| Missing `meta.tool_configs` | TypeError on YAML parse | Register all ToolConfig classes |

## MCP Server Compatibility

If exposing rooms via MCP:

| Tool Type | MCP Compatible | Notes |
|-----------|----------------|-------|
| Pattern A (tool_config) | ⚠️ Partial | Must have wrapper in `MCP_TOOL_CONFIG_WRAPPERS_BY_TOOL_NAME` |
| Pattern B (ctx) | ❌ No | `FASTAPI_CONTEXT` tools auto-excluded |
| BARE (no injection) | ✅ Yes | Works directly |

## Packaging Checklist

- [ ] `tool_name` is a valid dotted import path
- [ ] Tool functions use appropriate pattern (A for static, B for dynamic)
- [ ] Tool functions return error strings for runtime errors
- [ ] Tool functions raise for wiring errors (missing config)
- [ ] `from_yaml()` implemented correctly
- [ ] Per-tool config classes for each tool function
- [ ] Config classes registered in `meta.tool_configs`
- [ ] Lazy imports for external libraries
- [ ] Unit tests with mocks
- [ ] Integration tests with real library
- [ ] Example installation.yaml showing registration
- [ ] Example room_config.yaml showing usage
- [ ] Consider MCP compatibility if needed
