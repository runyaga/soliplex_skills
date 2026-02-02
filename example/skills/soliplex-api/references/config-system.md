# Soliplex Configuration System

## Configuration Hierarchy

Soliplex uses a three-level configuration hierarchy:

```
InstallationConfig
    │
    ├── RoomConfig (room-a)
    │       ├── AgentConfig
    │       ├── ToolConfig[]
    │       └── MCP_Client_Toolsets{}
    │
    └── RoomConfig (room-b)
            └── ...
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

### Corrected installation.yaml Structure

```yaml
id: my-installation
name: My Soliplex

# CRITICAL: Custom ToolConfig classes must be registered here
meta:
  tool_configs:
    - my_adapter.config.QueryServiceConfig
    - my_adapter.config.UpdateServiceConfig
  agent_configs:
    - my_adapter.config.CustomAgentConfig  # Optional: for agent templates

# Environment variables (NOT at root level)
environment:
  OLLAMA_BASE_URL: http://bizon:11434  # Use this, NOT ollama_host

# Path references
room_paths:
  - ./rooms/room-a
  - ./rooms/room-b
completion_paths:
  - ./completions/endpoint-a
quizzes_paths:
  - ./quizzes/quiz-a
```

**Key attributes:**
- `id` - Unique installation identifier
- `name` - Installation display name
- `meta.tool_configs` - **CRITICAL**: Register custom ToolConfig classes here
- `meta.agent_configs` - Register custom agent templates
- `environment` - Environment variables (including `OLLAMA_BASE_URL`)
- `room_paths` - List of room directory paths
- `room_configs` - Dict of loaded RoomConfig (populated after `reload_configurations()`)

## RoomConfig

Room-level configuration loaded from `room_config.yaml`.

```python
room_config = config.room_configs["gpt-20b"]

print(room_config.id)              # "gpt-20b"
print(room_config.name)            # "GPT-OSS 20B"
print(room_config.agent.model)     # "gpt-oss:20b" - nested under agent!
print(room_config.agent.system_prompt)   # System prompt text
print(room_config.tools)           # List[ToolConfig]
```

### Corrected room_config.yaml Structure

```yaml
id: gpt-20b
name: GPT-OSS 20B
description: Math-capable room

# IMPORTANT: Agent settings are NESTED under 'agent:' key
agent:
  model: gpt-oss:20b
  system_prompt: |
    You are a math assistant. Use available tools.
  # Optional agent template inheritance
  # template_id: my-base-template

welcome_message: |
  Welcome! I can help with calculations.

suggestions:
  - "Calculate factorial of 23"
  - "What is 2^100?"

# Tools use 'tool_name' (dotted path), NOT 'type' discriminator
tools:
  - tool_name: my_adapter.tools.query_service
    api_key: secret:MY_API_KEY
    endpoint: https://api.example.com

  - tool_name: soliplex_skills.tools.run_skill
    path: ../../skills
    include:
      - math-solver

# MCP is in SEPARATE block, NOT in tools list
mcp_client_toolsets:
  git-server:
    kind: stdio
    command: uv
    args: ["run", "mcp-server-git"]
    env:
      GIT_USERNAME: bot
    allowed_tools:  # Optional whitelist
      - git_read_file

  remote-server:
    kind: http
    url: http://localhost:8080/mcp
    headers:
      X-API-Key: secret
```

**Key attributes:**
- `id` - Unique room identifier (used in API paths)
- `name` - Display name
- `description` - Room description
- `agent.model` - LLM model name (nested!)
- `agent.system_prompt` - Instructions for the LLM (nested!)
- `agent.template_id` - Optional inheritance from agent templates
- `welcome_message` - Shown on room entry
- `suggestions` - Example queries
- `tools` - List of ToolConfig objects (keyed by `tool_name`)
- `mcp_client_toolsets` - MCP server connections (separate from tools)

## ToolConfig

Base class for tool configurations. Specialized by tool type.

### Registration Rule

**CRITICAL:** A custom ToolConfig class must be registered in `meta.tool_configs` in `installation.yaml` BEFORE Soliplex can recognize it in any `room_config.yaml`.

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

Without registration, Soliplex will crash with a `TypeError` when parsing the `tools:` section in room configs.

### ToolConfig Base

```python
class ToolConfig(BaseModel):
    tool_name: str      # Dotted import path (e.g., "my_adapter.tools.query")
    enabled: bool = True
```

**Note:** Soliplex uses `tool_name` for tool lookup, NOT a `type` discriminator. The `tool_name` must be a valid Python dotted import path to the tool function.

### Tool Requires Enum

Soliplex tools can require different runtime contexts. The `tool_requires` property determines what Soliplex injects:

```python
from soliplex.config import ToolRequires

class ToolRequires(enum.StrEnum):
    TOOL_CONFIG = "tool_config"      # Tool receives ToolConfig instance
    FASTAPI_CONTEXT = "fastapi_context"  # Tool receives FastAPI request context
    BARE = "bare"                    # Tool receives no injection
```

**TOOL_CONFIG (Pattern A - Frozen Configuration):**
```python
async def my_tool(tool_config: MyToolConfig, query: str) -> str:
    # tool_config is baked in via functools.partial at Agent creation time
    return await do_work(tool_config.api_key)
```

**FASTAPI_CONTEXT (Pattern B - Runtime Context):**
```python
from pydantic_ai import RunContext
from soliplex.agents import AgentDependencies

async def my_tool(ctx: RunContext[AgentDependencies], query: str) -> str:
    # ctx provides access to fresh configs, user info, installation at runtime
    tool_config = ctx.deps.tool_configs["my_adapter.tools.my_tool"]
    user = ctx.deps.user
    return await do_work(tool_config.api_key, user)
```

**BARE (simple tools with no injection):**
```python
async def my_tool(query: str) -> str:
    # No config or context injected
    return query.upper()
```

See `adapter-patterns.md` for detailed comparison of Pattern A vs Pattern B and agent caching implications.

### SkillsToolConfig

Configuration for pydantic-ai-skills integration:

```python
class SkillsToolConfig(ToolConfig):
    tool_name: str = "soliplex_skills.tools.run_skill"
    path: str           # Path to skills directory
    include: list[str] | None = None  # Whitelist
    exclude: list[str] | None = None  # Blacklist
```

**YAML representation:**

```yaml
tools:
  - tool_name: soliplex_skills.tools.run_skill
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
    print(f"  Model: {room.agent.model}")  # Note: nested under agent
    print(f"  Tools: {len(room.tools)}")
    for tool in room.tools:
        print(f"    - {tool.tool_name}")  # tool_name, not type
```

## Tool Resolution

Soliplex resolves tools by `tool_name`, NOT by type discriminators. The `tool_name` must be registered in `meta.tool_configs` at the installation level.

**Resolution process:**
1. Parse `tool_name` from room config (e.g., `my_adapter.tools.query`)
2. Look up corresponding ToolConfig class from `meta.tool_configs`
3. Dynamic import: `module_name, func = tool_name.rsplit(".", 1)`
4. Load function via `importlib.import_module(module_name)`

```yaml
# installation.yaml - Register ToolConfig classes
meta:
  tool_configs:
    - my_adapter.config.QueryServiceConfig
    - soliplex_skills.config.SkillsToolConfig

# room_config.yaml - Use by tool_name
tools:
  - tool_name: my_adapter.tools.query_service
    api_key: secret:MY_KEY
    endpoint: https://api.example.com

  - tool_name: soliplex_skills.tools.run_skill
    path: ./skills
```

**Note:** MCP servers are configured separately in `mcp_client_toolsets`, not in the `tools` list.

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
environment:
  OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-http://localhost:11434}

# Server binding via pydantic-settings
host: ${SOLIPLEX_HOST:-127.0.0.1}
port: ${SOLIPLEX_PORT:-8000}
```

**Key Environment Variables:**

| Variable | Purpose | Default |
|----------|---------|---------|
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `SESSION_SECRET_KEY` | Session signing key | Random (unsafe for multi-worker!) |
| `SOLIPLEX_INSTALLATION_PATH` | Installation path for reload | - |
| `SOLIPLEX_NO_AUTH_MODE` | Bypass authentication | `false` |
| `WEB_CONCURRENCY` | Uvicorn workers | 1 |
| `FORWARDED_ALLOW_IPS` | Trusted proxy IPs | `127.0.0.1` |

This uses pydantic-settings for environment binding.

## Agent Caching Warning

⚠️ **CRITICAL**: Soliplex caches Agents by Room ID. Config updates won't apply until server restarted.

**Summary:**
- **Pattern A** (`tool_config`): Config frozen at Agent creation
- **Pattern B** (`ctx`): Fresh config every `agent.run()`

See [adapter-patterns.md](adapter-patterns.md#2-agent-caching-and-config-lifecycle) for detailed patterns and when to use each.
