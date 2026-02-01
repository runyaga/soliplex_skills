# Case Study: Building soliplex_skills

This document walks through how `soliplex_skills` was built as a Soliplex adapter for pydantic-ai-skills. Use this as a reference when building your own adapters.

## Goal

Integrate the `pydantic-ai-skills` library into Soliplex, allowing rooms to use skills as tools.

## Architecture

```
pydantic-ai-skills (upstream)
        │
        ▼
┌─────────────────────────────────────┐
│        soliplex_skills              │
│  ┌───────────────┐                  │
│  │ SkillsToolConfig │  ← YAML config │
│  └───────┬───────┘                  │
│          │                          │
│          ▼                          │
│  ┌───────────────────┐              │
│  │ SoliplexSkillsAdapter │          │
│  └───────┬───────────┘              │
│          │                          │
│          ▼                          │
│  ┌─────────────────────────┐        │
│  │ Tool Functions           │        │
│  │ - list_skills           │        │
│  │ - load_skill            │        │
│  │ - run_skill_script      │        │
│  └─────────────────────────┘        │
└─────────────────────────────────────┘
        │
        ▼
    Soliplex Room
```

## Implementation

### 1. Configuration Class (config.py)

First, create a `ToolConfig` subclass:

```python
@dataclasses.dataclass
class SkillsToolConfig(ToolConfig):
    """Configuration for Skills tools."""

    directories: tuple[pathlib.Path, ...] = ...
    exclude_tools: frozenset[str] = ...
    validate_skills: bool = True
    max_depth: int = 3

    @classmethod
    def from_yaml(cls, installation_config, config_path, config):
        """Parse YAML to native types."""
        ...

    def create_toolset(self) -> SkillsToolset:
        """Create the upstream toolset."""
        from pydantic_ai_skills import SkillsToolset
        return SkillsToolset(
            directories=[str(p) for p in self.directories],
            validate=self.validate_skills,
            max_depth=self.max_depth,
            exclude_tools=set(self.exclude_tools),
        )
```

**Key decisions:**
- Inherit from `soliplex.config.ToolConfig` for Soliplex integration
- Use `@dataclasses.dataclass` (Soliplex convention)
- Implement `from_yaml()` for YAML config parsing
- Implement `create_toolset()` to create upstream objects
- Use hashable types (tuple, frozenset) for cache keys

### 2. Adapter Class (adapter.py)

Wrap the upstream library with Soliplex-friendly methods:

```python
class SoliplexSkillsAdapter:
    """Adapter wrapping pydantic-ai-skills for Soliplex."""

    def __init__(self, toolset: SkillsToolset):
        self._toolset = toolset

    async def list_skills(self) -> dict[str, str]:
        return {
            name: skill.description
            for name, skill in self._toolset.skills.items()
        }

    async def load_skill(self, skill_name: str) -> str:
        # Return formatted skill content
        ...

    async def run_skill_script(self, skill_name, script_name, args):
        # Execute script and return output
        ...
```

**Key decisions:**
- Async methods (Soliplex tools are async)
- Convert upstream objects to strings/dicts
- Handle errors gracefully

### 3. Caching (adapter.py)

Cache toolsets to avoid repeated loading:

```python
_toolset_cache: dict[CacheKey, SkillsToolset] = {}
_cache_lock = asyncio.Lock()

async def _get_toolset(config: SkillsToolConfig) -> SkillsToolset:
    key = (config.directories, config.validate_skills,
           config.max_depth, config.exclude_tools)

    if key in _toolset_cache:
        return _toolset_cache[key]

    async with _cache_lock:
        if key in _toolset_cache:
            return _toolset_cache[key]
        toolset = config.create_toolset()
        _toolset_cache[key] = toolset
        return toolset
```

**Key decisions:**
- Use tuple/frozenset for hashable cache keys
- Double-check pattern for thread safety
- Async lock for concurrent access

### 4. Tool Functions (tools.py)

Create Soliplex-compatible tool functions:

```python
async def list_skills(
    tool_config: SkillsToolConfig,
) -> dict[str, str] | str:
    """List all available skills."""
    try:
        adapter = await _get_adapter(tool_config)
        return await adapter.list_skills()
    except Exception as e:
        return f"Error: Failed to list skills: {e}"
```

**Soliplex tool conventions:**
- First parameter: `tool_config: YourToolConfig` (injected by Soliplex)
- Async functions
- Return strings on error (don't raise exceptions to LLM)
- Use descriptive docstrings (shown to LLM)

### 5. Per-Tool Configs (config.py)

Soliplex requires separate config classes per tool:

```python
@dataclasses.dataclass
class ListSkillsConfig(SkillsToolConfig):
    tool_name: str = "soliplex_skills.tools.list_skills"

@dataclasses.dataclass
class LoadSkillConfig(SkillsToolConfig):
    tool_name: str = "soliplex_skills.tools.load_skill"

@dataclasses.dataclass
class RunSkillScriptConfig(SkillsToolConfig):
    tool_name: str = "soliplex_skills.tools.run_skill_script"
```

These map to `TOOL_CONFIG_CLASSES_BY_TOOL_NAME` in Soliplex.

### 6. Public API (__init__.py)

Export everything users need:

```python
from soliplex_skills.config import SkillsToolConfig
from soliplex_skills.tools import list_skills, load_skill
from soliplex_skills.exceptions import SoliplexSkillsError

__all__ = [
    "SkillsToolConfig",
    "list_skills",
    "load_skill",
    ...
]
```

## YAML Usage

After building the adapter, users configure it in room_config.yaml:

```yaml
tools:
  - type: skills
    directories:
      - ../../skills
    exclude_tools:
      - dangerous-tool
    validate_skills: true
    max_depth: 3
```

## Environment Variables

Support environment-based configuration:

```python
class SkillsToolSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SOLIPLEX_SKILLS_")

    directories: str = "./skills"
    validate: bool = True
    max_depth: int = 3
```

This allows:
```bash
export SOLIPLEX_SKILLS_DIRECTORIES=./skills,./more-skills
export SOLIPLEX_SKILLS_VALIDATE=false
```

## Testing Strategy

### Unit Tests

```python
def test_config_from_yaml():
    config = SkillsToolConfig.from_yaml(
        installation_config=None,
        config_path=Path("./room_config.yaml"),
        config={"directories": ["./skills"]}
    )
    assert len(config.directories) == 1
```

### Integration Tests

```python
@pytest.mark.integration
async def test_list_skills_integration():
    config = SkillsToolConfig(directories=(Path("./test-skills"),))
    result = await list_skills(config)
    assert "test-skill" in result
```

## Lessons Learned

1. **Lazy imports**: Don't import pydantic-ai-skills at module level. Import in `create_toolset()` to allow config validation without the full dependency.

2. **Hashable config**: Use tuple/frozenset for config values that become cache keys.

3. **Error strings**: Return human-readable error strings instead of raising exceptions. The LLM needs to understand what went wrong.

4. **Async everywhere**: Soliplex tools are async. Even if the underlying library is sync, wrap it properly.

5. **Path resolution**: Resolve relative paths against `config_path.parent` (the room_config.yaml location), not current directory.

## Package Structure

```
soliplex_skills/
├── __init__.py        # Public API exports
├── config.py          # SkillsToolConfig + per-tool configs
├── adapter.py         # SoliplexSkillsAdapter + caching
├── tools.py           # Tool functions
└── exceptions.py      # Custom exceptions
```
