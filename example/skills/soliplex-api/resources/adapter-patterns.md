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

### Tool Functions Must Accept tool_config

Soliplex injects config via the `tool_config` parameter:

```python
# Your tool function MUST have this signature
async def my_tool(
    tool_config: MyToolConfig,  # Injected by Soliplex
    param1: str,                # User-provided parameters
    param2: int = 10,
) -> str:
    """Tool description shown to LLM."""
    # Use tool_config to access your configuration
    return f"Result using {tool_config.some_setting}"
```

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
        """Create from Soliplex YAML configuration."""
        return cls(
            tool_name=config.get("tool_name", cls.tool_name),  # Use class default
            api_key=config.get("api_key", ""),
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

### 2. Lazy Loading

Don't import external libraries until needed:

```python
async def my_tool(tool_config: MyConfig, query: str) -> str:
    # Import here, not at module level
    from heavy_library import Client
    ...
```

### 3. Error Handling - Return Strings, Don't Raise

Tool functions should return error strings for LLM-friendly handling:

```python
async def my_tool(tool_config: MyConfig, query: str) -> dict | str:
    try:
        result = do_something()
        return {"success": True, "data": result}
    except NotFoundException:
        return "Error: Item not found."  # LLM can understand this
    except Exception as e:
        return f"Error: {e}"
```

### 4. Validation at Config Time

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

### 5. Use TYPE_CHECKING for Circular Imports

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_adapter.config import MyToolConfig

async def my_tool(tool_config: "MyToolConfig", ...) -> str:
    ...
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
| Raising exceptions | LLM can't handle | Return error strings |
| Module-level imports | Slows config loading | Lazy import in functions |
| Missing `from_yaml` | YAML config fails | Implement classmethod |
| Hardcoded `tool_name` in `from_yaml` | Subclasses broken | Use `cls.tool_name` |

## Packaging Checklist

- [ ] `tool_name` is a valid dotted import path
- [ ] Tool functions accept `tool_config` as first parameter
- [ ] Tool functions return error strings (not raise)
- [ ] `from_yaml()` implemented correctly
- [ ] Per-tool config classes for each tool function
- [ ] Lazy imports for external libraries
- [ ] Unit tests with mocks
- [ ] Integration tests with real library
- [ ] Example installation.yaml showing registration
- [ ] Example room_config.yaml showing usage
