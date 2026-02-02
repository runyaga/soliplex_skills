# Soliplex Configuration System

## Configuration Hierarchy

Soliplex uses a three-level configuration hierarchy:

```
InstallationConfig
    │
    ├── RoomConfig (room-a)
    │       └── ToolConfig[]
    │
    └── RoomConfig (room-b)
            └── ToolConfig[]
```

## InstallationConfig

Top-level configuration loaded from `installation.yaml`.

```python
from soliplex.config import load_installation

# Load installation
config = load_installation("./installation.yaml")

# IMPORTANT: Must reload to populate room_configs
config.reload_configurations()

# Access rooms
for room_id, room_config in config.room_configs.items():
    print(f"{room_id}: {room_config.name}")
```

**Key attributes:**
- `name` - Installation name
- `host` / `port` - Server binding
- `ollama_host` - Ollama server URL
- `rooms` - List of room path references
- `room_configs` - Dict of loaded RoomConfig (after reload)

## RoomConfig

Room-level configuration loaded from `room_config.yaml`.

```python
room_config = config.room_configs["gpt-20b"]

print(room_config.id)              # "gpt-20b"
print(room_config.name)            # "GPT-OSS 20B"
print(room_config.model)           # "gpt-oss:20b"
print(room_config.system_prompt)   # System prompt text
print(room_config.tools)           # List[ToolConfig]
```

**Key attributes:**
- `id` - Unique room identifier
- `name` - Display name
- `description` - Room description
- `model` - Ollama model name
- `system_prompt` - Agent instructions
- `welcome_message` - Shown on room entry
- `suggestions` - Example queries
- `tools` - List of ToolConfig objects

## ToolConfig

Base class for tool configurations. Specialized by tool type.

### Registration Rule

**IMPORTANT:** A custom ToolConfig class must be registered in `meta.tool_configs` in `installation.yaml` BEFORE Soliplex can recognize it in any `room_config.yaml`.

```yaml
# installation.yaml
id: my-installation

meta:
  tool_configs:
    # Register your custom config classes here
    - my_adapter.config.MyToolConfig
    - my_adapter.config.QueryServiceConfig
    - my_adapter.config.UpdateServiceConfig
```

Without registration, Soliplex will fail to parse the `tools:` section in room configs.

### ToolConfig Base

```python
class ToolConfig(BaseModel):
    type: str           # Tool type discriminator
    enabled: bool = True
```

### Tool Requires Enum

Soliplex tools can require different runtime contexts. The `tool_requires` property determines what Soliplex injects:

```python
from soliplex.config import ToolRequires

class ToolRequires(enum.StrEnum):
    TOOL_CONFIG = "tool_config"      # Tool receives ToolConfig instance
    FASTAPI_CONTEXT = "fastapi_context"  # Tool receives FastAPI request context
    BARE = "bare"                    # Tool receives no injection
```

**TOOL_CONFIG (most common for adapters):**
```python
async def my_tool(tool_config: MyToolConfig, query: str) -> str:
    # tool_config is injected by Soliplex
    return await do_work(tool_config.api_key)
```

**FASTAPI_CONTEXT (for tools needing request info):**
```python
async def my_tool(ctx: RunContext[AgentDeps], query: str) -> str:
    # ctx provides access to FastAPI request, user info, etc.
    return await do_work(ctx.deps.request)
```

**BARE (simple tools with no injection):**
```python
async def my_tool(query: str) -> str:
    # No config or context injected
    return query.upper()
```

**Note:** A tool can use `tool_config` OR `ctx`, but NOT both. Soliplex inspects the function signature to determine which mode to use.

### SkillsToolConfig

Configuration for pydantic-ai-skills integration:

```python
class SkillsToolConfig(ToolConfig):
    type: Literal["skills"] = "skills"
    path: str           # Path to skills directory
    include: list[str] | None = None  # Whitelist
    exclude: list[str] | None = None  # Blacklist
```

**YAML representation:**

```yaml
tools:
  - type: skills
    path: ../../skills
    include:
      - math-solver
      - text-utils
```

### Creating a Toolset

SkillsToolConfig provides a method to create the runtime toolset:

```python
from soliplex_skills import SkillsToolConfig

config = SkillsToolConfig(path="./skills")
toolset = config.create_toolset()

# toolset is a list of pydantic-ai Tool objects
for tool in toolset:
    print(f"{tool.name}: {tool.description}")
```

## Configuration Loading Pattern

```python
from pathlib import Path
from soliplex.config import load_installation

def load_soliplex_config(installation_path: str | Path):
    """Load and return fully populated Soliplex config."""
    config = load_installation(installation_path)
    config.reload_configurations()  # Critical!
    return config

# Usage
config = load_soliplex_config("./installation.yaml")

# Enumerate rooms
for room_id, room in config.room_configs.items():
    print(f"Room: {room.name}")
    print(f"  Model: {room.model}")
    print(f"  Tools: {len(room.tools)}")
    for tool in room.tools:
        print(f"    - {tool.type}")
```

## Discriminated Unions

Soliplex uses Pydantic's discriminated unions for tool configs:

```python
from typing import Annotated, Union
from pydantic import Discriminator

ToolConfigUnion = Annotated[
    Union[SkillsToolConfig, MCPToolConfig, FunctionToolConfig],
    Discriminator("type"),
]
```

This allows YAML like:

```yaml
tools:
  - type: skills
    path: ./skills
  - type: mcp
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem"]
  - type: function
    module: mymodule
    function: my_tool
```

## Validation

All configs use Pydantic for validation:

```python
from pydantic import ValidationError

try:
    config = SkillsToolConfig(path="/nonexistent", type="skills")
except ValidationError as e:
    print(e.errors())
```

Common validation:
- Required fields (path, type)
- Path existence checks
- Type discriminator matching
- Include/exclude mutual exclusivity

## Environment Variable Support

Configs support environment variable interpolation:

```yaml
# installation.yaml
ollama_host: ${OLLAMA_HOST:-localhost:11434}
port: ${SOLIPLEX_PORT:-8002}
```

This uses pydantic-settings for environment binding.
