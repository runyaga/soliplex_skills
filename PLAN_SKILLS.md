# Soliplex Skills Adapter - Implementation Plan

## Executive Summary

This document outlines the phased implementation plan for `soliplex_skills`, an adapter that integrates [pydantic-ai-skills](https://github.com/DougTrajano/pydantic-ai-skills) into the Soliplex framework. The adapter wraps the upstream Skills toolset to work with Soliplex's agent architecture and configuration system.

**Key Capability:** Agent Skills provide progressive disclosure of specialized capabilities - agents can discover, load, and execute domain-specific knowledge on-demand without saturating their context.

---

## LLM Review Process

**IMPORTANT**: When running LLM reviews at phase gates, you MUST:

1. **Use `mcp__gemini__read_files`** (NOT `ask_gemini`)
2. **Use model `gemini-3-pro-preview`**
3. **Include `PLAN_SKILLS.md`** so Gemini sees the phase objectives
4. **Include ALL source files touched in the phase**

### Required Tool Call Format

```python
mcp__gemini__read_files(
    file_paths=[
        "/Users/runyaga/dev/soliplex_skills/PLAN_SKILLS.md",  # ALWAYS include
        # ... all source files modified in this phase
        # ... all test files modified in this phase
    ],
    prompt="<phase context and review instructions>",
    model="gemini-3-pro-preview"  # ALWAYS use pro3 for reviews
)
```

### Review Prompt Template

```
This is Phase X.Y of soliplex_skills development: [Phase Title]

Refer to PLAN_SKILLS.md for phase objectives (included in file_paths).

Completed tasks this phase:
- [List what was done]

Please review for:
1. Any issues related to the phase objectives
2. Code quality issues
3. Security concerns
4. Thread-safety issues
5. Missing functionality or regressions

Report findings in this format:
| ID | File:Line | Issue | Severity |
```

---

## Progress Tracking

### Phase 1: Foundation ✅ COMPLETE
- [x] Create project directory structure
- [x] Create pyproject.toml with dependencies
- [x] Implement exceptions.py with custom hierarchy
- [x] Implement config.py (SkillsToolSettings + SkillsToolConfig)
- [x] Implement adapter.py (SoliplexSkillsAdapter)
- [x] Implement tools.py (wrapped functions)
- [x] Create __init__.py with exports
- [x] Write unit tests for config
- [x] Write unit tests for adapter
- [x] Write unit tests for tools
- [x] Write unit tests for exceptions
- [x] Run ruff and fix all issues
- [x] Verify ≥80% code coverage (achieved 86%)
- [x] **LLM Review: Source** - 3 iterations with Gemini pro3 (see FEEDBACK.md)
- [ ] Initial commit

**Phase 1 Results:**
- 46 tests passing
- 86% code coverage
- Ruff clean
- All issues from Gemini review addressed

### Phase 2: Functional Tests + Pydantic Refactor ⏳

**2.1 Pydantic-First Refactor (REQUIRED)**
- [ ] Refactor `config.py`: `directories: str` → `directories: list[pathlib.Path]`
- [ ] Refactor `config.py`: `exclude_tools: str` → `exclude_tools: set[str]`
- [ ] Remove `get_directories_list()` and `get_exclude_tools_set()` helper methods
- [ ] Update `from_yaml()` to handle YAML lists natively
- [ ] Update `adapter.py` cache key to use tuple of resolved paths
- [ ] Add `ctx: RunContext` parameter to tools that need it
- [ ] Standardize error returns (structured type or consistent string format)

**2.2 Functional Tests**
- [ ] Create functional tests with real skill directories
- [ ] Test all 4 tools (list_skills, load_skill, read_skill_resource, run_skill_script)
- [ ] Test skill discovery from multiple directories
- [ ] Test programmatic skills creation
- [ ] Test skill resource loading (static and callable)
- [ ] Test skill script execution
- [ ] Update `pyproject.toml` testpaths to include functional tests
- [ ] Add concurrency test for `_get_toolset` double-checked locking
- [ ] Create actual skill fixtures with resources/scripts in `example/skills/`
- [ ] Increase coverage to ≥90%
- [ ] **LLM Review: Source** - Gemini pro3 `read_files`
- [ ] **LLM Review: Tests** - Gemini pro3 `read_files`
- [ ] Commit Phase 2

### Phase 3: Room Configuration Integration ✅ COMPLETE
- [x] Create example room_config.yaml
- [x] Document installation.yaml registration
- [x] Create `example/installation.yaml` with tool config registration
- [x] Test per-room skills configuration (6 functional tests added)
- [x] Create example/ directory with working room and sample skills
- [x] Test with actual Soliplex installation (via `pytest.importorskip` - tests run when available)
- [x] Add integration test: verify SkillsToolConfig loads via Soliplex module import
- [x] Use `pytest.importorskip("soliplex")` for CI compatibility
- [x] Decide on `allow_mcp` support → Deferred to Phase 5 (MCP Tool Exposure). SkillsToolConfig inherits `allow_mcp=False` from ToolConfig.
- [x] Create example/ README with room usage examples and scenarios
- [x] **LLM Review: Source** - Gemini pro3 `read_files` (2 rounds)
- [x] Commit Phase 3

**Example Scenarios Created:**
- Research Assistant room with citation skill
- Code Reviewer room with style guide skill

### Phase 4: Polish & Release ⏳
- [ ] Complete README.md documentation
- [ ] Add CONTRIBUTING.md
- [ ] Verify LICENSE file
- [ ] Add GitHub CI actions (.github/workflows/ci.yml)
- [ ] All ruff checks pass
- [ ] Package builds successfully
- [ ] 100% type hint coverage
- [ ] All public APIs have docstrings
- [ ] Final coverage ≥95%
- [ ] **LLM Review: Docs** - Gemini pro3 `read_files`
- [ ] Commit Phase 4
- [ ] Tag release version

### Phase 5: MCP Tool Exposure (Future) ⏳
- [ ] Design MCP server exposing skills as dynamic tools
- [ ] Implement `src/soliplex_skills/mcp_server.py`
- [ ] Each skill becomes a discoverable MCP tool
- [ ] Support tool schemas from skill metadata
- [ ] Add `soliplex-skills-mcp` CLI entry point
- [ ] Document MCP integration patterns
- [ ] Test with Claude Code, Cursor, other MCP clients

**MCP Exposure Concept:**
Skills become MCP tools that any MCP-compatible client can discover and invoke:

```
┌─────────────────┐     MCP Protocol      ┌──────────────────┐
│  Claude Code    │◄────────────────────►│ soliplex-skills  │
│  Cursor         │   tools/list          │   MCP Server     │
│  Any MCP Client │   tools/call          │                  │
└─────────────────┘                       └────────┬─────────┘
                                                   │
                                          ┌────────▼─────────┐
                                          │  Skills Directory │
                                          │  - research-asst  │
                                          │  - code-reviewer  │
                                          └──────────────────┘
```

**Benefits:**
- Skills usable outside Soliplex (Claude Code, Cursor, etc.)
- Dynamic tool registration (no code changes to add skills)
- Unified skill management across all AI agents

---

## Upstream Library Overview

The `pydantic-ai-skills` library provides:

| Component | Description |
|-----------|-------------|
| `SkillsToolset` | Main toolset integrating skills with pydantic-ai agents |
| `Skill` | Dataclass representing a skill with resources and scripts |
| `SkillsDirectory` | Filesystem-based skill discovery and management |
| `SkillResource` | Static or callable resource within a skill |
| `SkillScript` | Executable script (file or function) within a skill |

**Key Tools Provided:**
| Tool | Description |
|------|-------------|
| `list_skills` | List all available skills with descriptions |
| `load_skill` | Load complete instructions for a specific skill |
| `read_skill_resource` | Read skill resource files or invoke callable resources |
| `run_skill_script` | Execute skill scripts |

**Key Concepts:**
- **Progressive Disclosure**: Load skill metadata on-demand rather than comprehensively
- **Multi-source Loading**: Import skills from multiple directories
- **Programmatic Skills**: Create skills via Python decorators or dataclasses
- **Security Hardening**: Path traversal prevention and safe script execution

---

## Architecture Principles

### Pydantic-First Design

**MANDATORY**: All configuration uses native Pydantic types. No string parsing.

| Anti-Pattern | Correct Pattern |
|--------------|-----------------|
| `directories: str = "a,b"` then `.split(",")` | `directories: list[Path]` |
| `exclude_tools: str` then parse | `exclude_tools: set[str]` |
| String validation in methods | Pydantic validators |
| Manual type coercion | `Field()` with proper types |

**Rationale:**
- YAML lists map directly to `list[T]`
- Soliplex config system expects Pydantic models
- pydantic-ai tools use typed schemas
- Eliminates parsing bugs (whitespace, edge cases)

### Soliplex Config Integration

Configuration must inherit from `soliplex.config.ToolConfig` and:
- Use `@dataclasses.dataclass` (Soliplex pattern)
- Implement `from_yaml(cls, installation_config, config_path, config)` classmethod
- Resolve relative paths against `config_path.parent`
- Support environment variable fallbacks via `pydantic-settings`

### pydantic-ai Idioms

Tools should:
- Accept typed `ToolConfig` objects (not dicts)
- Use `RunContext` for dependency injection when needed
- Return structured types or well-defined error models
- Leverage pydantic-ai's schema generation for MCP exposure

---

## Architecture Decisions

### Path Resolution Strategy

**Source**: `src/soliplex_skills/config.py:343-356`

Relative paths in `directories` configuration are resolved relative to the room's `config_path`:

```python
# In SkillsToolConfig.from_yaml()
# config_path is the room_config.yaml location
# directories like "../../skills" resolve from there
```

**Resolution Order:**
1. Absolute paths → used as-is
2. Relative paths → resolved from `config_path.parent`
3. Environment variable `SOLIPLEX_SKILLS_DIRECTORIES` → fallback default

### Error Handling Strategy

**Source**: `src/soliplex_skills/tools.py:67-95`

All tool functions return **user-friendly error strings** rather than raising exceptions:

```python
# Pattern used in all tools:
try:
    adapter = await _get_adapter(tool_config)
    return await adapter.method(...)
except SkillNotFoundError as e:
    return f"Error: {e}"
except Exception as e:
    return f"Unexpected error: {e}"
```

**Rationale:** LLM agents handle string responses better than exceptions. Errors become actionable context.

### ToolConfig Import Shim

**Source**: `src/soliplex_skills/config.py:12-20`

Allows standalone operation without full Soliplex installation:

```python
try:
    from soliplex.config import ToolConfig
except ImportError:
    @dataclasses.dataclass
    class ToolConfig:  # Minimal shim
        tool_name: str = ""
        _installation_config: Any = None
        _config_path: pathlib.Path | None = None
```

### Known Issues (from Codex gpt-5.2 review)

| Issue | Location | Violation | Status |
|-------|----------|-----------|--------|
| `ctx` parameter not passed to tools | `tools.py:74,107` | pydantic-ai idiom | Phase 2 |
| **String parsing for directories** | `config.py:112` | **Pydantic-First** | Phase 2 |
| **String parsing for exclude_tools** | `config.py:153` | **Pydantic-First** | Phase 2 |
| Inconsistent error returns | `tools.py:27` vs `tools.py:42` | Type consistency | Phase 2 |
| Cache key uses raw strings | `adapter.py:35` | Resolved by Pydantic types | Phase 2 |
| Old `PLAN.md` conflicts | `PLAN.md.archived` | Stale docs | ✅ Done |

**Phase 2 MUST refactor config to use native Pydantic types:**
```python
# BEFORE (anti-pattern)
directories: str = "./skills"
exclude_tools: str = ""

# AFTER (Pydantic-first)
directories: list[pathlib.Path] = Field(default_factory=list)
exclude_tools: set[str] = Field(default_factory=set)
```

### Security Considerations

**Source**: `src/soliplex_skills/adapter.py:241`

| Risk | Mitigation | Status |
|------|------------|--------|
| Scripts execute arbitrary code | Add explicit `allow_scripts: bool` config gate | Phase 3 |
| No path allowlist enforcement | Enforce "installation-root relative" paths | Phase 3 |
| No execution limits | Add timeouts, output caps, sandbox options | Phase 4 |

**Recommendation:** Treat skills directories as **trusted code paths**. Document security model clearly.

---

## Phase 1: Project Foundation & Upstream Integration

### Objectives
- Establish project structure following soliplex patterns
- Integrate pydantic-ai-skills as dependency
- Create Soliplex-compatible configuration wrapper
- Set up development tooling (ruff, pytest, coverage)

### 1.1 Project Structure

```
soliplex_skills/
├── src/
│   └── soliplex_skills/
│       ├── __init__.py           # Public exports
│       ├── config.py             # Soliplex ToolConfig integration
│       ├── adapter.py            # Core adapter wrapping upstream toolset
│       ├── tools.py              # Soliplex-compatible tool functions
│       └── exceptions.py         # Soliplex-specific exceptions
├── tests/
│   ├── unit/
│   │   ├── conftest.py
│   │   ├── test_config.py
│   │   ├── test_adapter.py
│   │   └── test_tools.py
│   └── functional/
│       ├── conftest.py
│       ├── test_skill_discovery.py
│       └── test_soliplex_integration.py
├── example/
│   ├── installation.yaml
│   ├── skills/
│   │   └── research-assistant/
│   │       └── SKILL.md
│   └── rooms/
│       └── skills-demo/
│           └── room_config.yaml
├── pyproject.toml
├── README.md
├── LICENSE
├── PLAN_SKILLS.md
└── CONTRIBUTING.md
```

### 1.2 pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "soliplex-skills"
version = "0.1.0dev0"
description = "Soliplex adapter for pydantic-ai-skills"
authors = [{ name = "runyaga", email = "runyaga@gmail.com" }]
readme = "README.md"
requires-python = ">=3.12"
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "License :: OSI Approved :: MIT License",
]
dependencies = [
    # Upstream library
    "pydantic-ai-skills >= 0.4.0",
    # Soliplex core (for types/protocols)
    "pydantic >= 2.0.0",
    "pydantic-settings >= 2.0.0",
    "pydantic-ai >= 0.5.0",
]

[project.optional-dependencies]
soliplex = [
    "soliplex",
]

[dependency-groups]
dev = [
    "pytest >= 8.0.0",
    "pytest-cov >= 4.0.0",
    "pytest-asyncio >= 0.23.0",
    "coverage >= 7.0.0",
    "ruff >= 0.4.0",
    "soliplex",
]

[tool.pytest.ini_options]
pythonpath = "src"
python_files = "test_*.py"
testpaths = ["tests/unit"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
addopts = "--cov=soliplex_skills --cov-branch --cov-fail-under=80"

[tool.coverage.run]
source = ["src/soliplex_skills"]

[tool.coverage.report]
show_missing = true

[tool.ruff]
line-length = 79
target-version = "py312"

[tool.ruff.lint]
select = ["F", "E", "B", "UP", "I", "TRY", "PT", "SIM", "RUF"]

[tool.ruff.lint.isort]
force-single-line = true
```

### 1.3 Configuration Module (`src/soliplex_skills/config.py`)

```python
"""Soliplex ToolConfig integration for Skills tools.

Bridges pydantic-ai-skills with Soliplex's configuration system.
"""

from __future__ import annotations

import dataclasses
import pathlib
from typing import TYPE_CHECKING
from typing import Any

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from soliplex.config import ToolConfig

if TYPE_CHECKING:
    from pydantic_ai_skills import SkillsToolset


class SkillsToolSettings(BaseSettings):
    """Environment-based configuration for Skills tools.

    Environment variables:
        SOLIPLEX_SKILLS_DIRECTORIES: Comma-separated skill directories
        SOLIPLEX_SKILLS_VALIDATE: Validate skill structure (default: True)
        SOLIPLEX_SKILLS_MAX_DEPTH: Max discovery depth (default: 3)
        SOLIPLEX_SKILLS_EXCLUDE_TOOLS: Comma-separated tools to exclude
    """

    model_config = SettingsConfigDict(env_prefix="SOLIPLEX_SKILLS_")

    directories: str = "./skills"  # Comma-separated paths
    validate: bool = True
    max_depth: int = 3
    exclude_tools: str = ""  # Comma-separated: "run_skill_script"


def _get_env_settings() -> SkillsToolSettings:
    """Lazy-load environment settings."""
    return SkillsToolSettings()


@dataclasses.dataclass
class SkillsToolConfig(ToolConfig):
    """Configuration for Skills tools.

    Inherits from soliplex.config.ToolConfig for full Soliplex integration.
    Single config class for all Skills tools - tool_name from room config.

    Defaults come from environment variables via SkillsToolSettings.
    Room configs can override any setting.
    """

    # Skills-specific fields with lazy env var defaults
    directories: str = dataclasses.field(
        default_factory=lambda: _get_env_settings().directories
    )
    validate: bool = dataclasses.field(
        default_factory=lambda: _get_env_settings().validate
    )
    max_depth: int = dataclasses.field(
        default_factory=lambda: _get_env_settings().max_depth
    )
    exclude_tools: str = dataclasses.field(
        default_factory=lambda: _get_env_settings().exclude_tools
    )

    @classmethod
    def from_yaml(
        cls,
        installation_config: Any,
        config_path: pathlib.Path,
        config: dict[str, Any],
    ) -> SkillsToolConfig:
        """Create from Soliplex YAML configuration."""
        env_settings = _get_env_settings()
        return cls(
            tool_name=config.get("tool_name", ""),
            directories=config.get("directories", env_settings.directories),
            validate=config.get("validate", env_settings.validate),
            max_depth=config.get("max_depth", env_settings.max_depth),
            exclude_tools=config.get(
                "exclude_tools", env_settings.exclude_tools
            ),
            _installation_config=installation_config,
            _config_path=config_path,
        )

    def get_directories_list(self) -> list[str]:
        """Parse directories string into list."""
        if not self.directories:
            return []
        return [d.strip() for d in self.directories.split(",") if d.strip()]

    def get_exclude_tools_set(self) -> set[str]:
        """Parse exclude_tools string into set."""
        if not self.exclude_tools:
            return set()
        return {t.strip() for t in self.exclude_tools.split(",") if t.strip()}

    def create_toolset(self) -> SkillsToolset:
        """Create SkillsToolset from this configuration."""
        from pydantic_ai_skills import SkillsToolset

        return SkillsToolset(
            directories=self.get_directories_list(),
            validate=self.validate,
            max_depth=self.max_depth,
            exclude_tools=self.get_exclude_tools_set(),
        )


# Per-tool config classes for Soliplex registration.
# Soliplex requires class-level tool_name for TOOL_CONFIG_CLASSES_BY_TOOL_NAME


@dataclasses.dataclass
class ListSkillsConfig(SkillsToolConfig):
    """Config for list_skills tool."""

    tool_name: str = "soliplex_skills.tools.list_skills"


@dataclasses.dataclass
class LoadSkillConfig(SkillsToolConfig):
    """Config for load_skill tool."""

    tool_name: str = "soliplex_skills.tools.load_skill"


@dataclasses.dataclass
class ReadSkillResourceConfig(SkillsToolConfig):
    """Config for read_skill_resource tool."""

    tool_name: str = "soliplex_skills.tools.read_skill_resource"


@dataclasses.dataclass
class RunSkillScriptConfig(SkillsToolConfig):
    """Config for run_skill_script tool."""

    tool_name: str = "soliplex_skills.tools.run_skill_script"
```

### 1.4 Adapter Module (`src/soliplex_skills/adapter.py`)

```python
"""Core adapter bridging pydantic-ai-skills with Soliplex.

Wraps SkillsToolset to provide Soliplex-compatible tool functions.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from pydantic_ai_skills import SkillsToolset

    from soliplex_skills.config import SkillsToolConfig

# Module-level cache: config key -> toolset (supports concurrent rooms)
_toolset_cache: dict[tuple, SkillsToolset] = {}
_cache_lock = asyncio.Lock()


async def _get_toolset(config: SkillsToolConfig) -> SkillsToolset:
    """Get or create SkillsToolset from config.

    Uses async-safe caching to support multiple concurrent configurations
    (e.g., Room A -> skills-dir-1, Room B -> skills-dir-2).

    Args:
        config: Skills configuration

    Returns:
        SkillsToolset instance
    """
    # Cache key based on config parameters
    key = (
        config.directories,
        config.validate,
        config.max_depth,
        config.exclude_tools,
    )

    if key in _toolset_cache:
        return _toolset_cache[key]

    async with _cache_lock:
        # Double-check after acquiring lock
        if key in _toolset_cache:
            return _toolset_cache[key]

        # Create new toolset and cache it
        toolset = config.create_toolset()
        _toolset_cache[key] = toolset
        return toolset


def close_all() -> None:
    """Clear all cached toolsets.

    Thread-safe cleanup for testing and shutdown.
    """
    _toolset_cache.clear()


class SoliplexSkillsAdapter:
    """Adapter wrapping pydantic-ai-skills for Soliplex.

    Provides Soliplex-compatible interface to skills functionality.
    """

    def __init__(self, toolset: SkillsToolset):
        self._toolset = toolset

    @property
    def skills(self) -> dict[str, Any]:
        """Get available skills."""
        return self._toolset.skills

    async def list_skills(self) -> dict[str, str]:
        """List all available skills.

        Returns:
            Dictionary mapping skill names to descriptions.
        """
        return {
            name: skill.description
            for name, skill in self._toolset.skills.items()
        }

    async def load_skill(self, skill_name: str) -> str:
        """Load complete instructions for a skill.

        Args:
            skill_name: Name of the skill to load

        Returns:
            Formatted skill instructions with resources and scripts
        """
        from pydantic_ai_skills import SkillNotFoundError

        if skill_name not in self._toolset.skills:
            available = ", ".join(sorted(self._toolset.skills.keys())) or "none"
            raise SkillNotFoundError(
                f"Skill '{skill_name}' not found. Available: {available}"
            )

        skill = self._toolset.skills[skill_name]

        # Build formatted output matching upstream template
        resources_list = []
        if skill.resources:
            for res in skill.resources:
                resources_list.append(f'<resource name="{res.name}" />')

        scripts_list = []
        if skill.scripts:
            for scr in skill.scripts:
                scripts_list.append(f'<script name="{scr.name}" />')

        return f"""<skill>
<name>{skill.name}</name>
<description>{skill.description}</description>
<uri>{skill.uri or 'N/A'}</uri>

<resources>
{chr(10).join(resources_list) if resources_list else '<!-- No resources -->'}
</resources>

<scripts>
{chr(10).join(scripts_list) if scripts_list else '<!-- No scripts -->'}
</scripts>

<instructions>
{skill.content}
</instructions>
</skill>
"""

    async def read_skill_resource(
        self,
        skill_name: str,
        resource_name: str,
        args: dict[str, Any] | None = None,
        ctx: Any = None,
    ) -> str:
        """Read a skill resource.

        Args:
            skill_name: Name of the skill
            resource_name: Name of the resource
            args: Arguments for callable resources
            ctx: RunContext for callable resources

        Returns:
            Resource content
        """
        from pydantic_ai_skills import SkillNotFoundError
        from pydantic_ai_skills import SkillResourceNotFoundError

        if skill_name not in self._toolset.skills:
            raise SkillNotFoundError(f"Skill '{skill_name}' not found.")

        skill = self._toolset.skills[skill_name]

        # Find the resource
        resource = None
        if skill.resources:
            for r in skill.resources:
                if r.name == resource_name:
                    resource = r
                    break

        if resource is None:
            available = [r.name for r in skill.resources] if skill.resources else []
            raise SkillResourceNotFoundError(
                f"Resource '{resource_name}' not found in skill "
                f"'{skill_name}'. Available: {available}"
            )

        return await resource.load(ctx=ctx, args=args)

    async def run_skill_script(
        self,
        skill_name: str,
        script_name: str,
        args: dict[str, Any] | None = None,
        ctx: Any = None,
    ) -> str:
        """Execute a skill script.

        Args:
            skill_name: Name of the skill
            script_name: Name of the script
            args: Arguments for the script
            ctx: RunContext for the script

        Returns:
            Script output
        """
        from pydantic_ai_skills import SkillNotFoundError
        from pydantic_ai_skills import SkillResourceNotFoundError

        if skill_name not in self._toolset.skills:
            raise SkillNotFoundError(f"Skill '{skill_name}' not found.")

        skill = self._toolset.skills[skill_name]

        # Find the script
        script = None
        if skill.scripts:
            for s in skill.scripts:
                if s.name == script_name:
                    script = s
                    break

        if script is None:
            available = [s.name for s in skill.scripts] if skill.scripts else []
            raise SkillResourceNotFoundError(
                f"Script '{script_name}' not found in skill "
                f"'{skill_name}'. Available: {available}"
            )

        return await script.run(ctx=ctx, args=args)
```

### 1.5 Tools Module (`src/soliplex_skills/tools.py`)

```python
"""Soliplex-compatible tool functions.

These tools follow Soliplex conventions:
- Accept tool_config: SkillsToolConfig (injected by Soliplex)
- Async tool functions
- Type-safe return values
"""

from __future__ import annotations

from typing import Any

from soliplex_skills.adapter import SoliplexSkillsAdapter
from soliplex_skills.adapter import _get_toolset
from soliplex_skills.config import SkillsToolConfig


async def _get_adapter(config: SkillsToolConfig) -> SoliplexSkillsAdapter:
    """Get adapter from config."""
    toolset = await _get_toolset(config)
    return SoliplexSkillsAdapter(toolset)


async def list_skills(tool_config: SkillsToolConfig) -> dict[str, str]:
    """List all available skills.

    Returns:
        Dictionary mapping skill names to their descriptions.
        Empty dictionary if no skills are available.
    """
    adapter = await _get_adapter(tool_config)
    return await adapter.list_skills()


async def load_skill(
    tool_config: SkillsToolConfig,
    skill_name: str,
) -> str:
    """Load complete instructions for a specific skill.

    Args:
        skill_name: Exact name from your available skills list.
            Must match exactly (e.g., "data-analysis" not "data analysis").

    Returns:
        Structured documentation containing skill instructions,
        available resources, and scripts.
    """
    adapter = await _get_adapter(tool_config)
    return await adapter.load_skill(skill_name)


async def read_skill_resource(
    tool_config: SkillsToolConfig,
    skill_name: str,
    resource_name: str,
    args: dict[str, Any] | None = None,
) -> str:
    """Read a skill resource file or invoke callable resource.

    Args:
        skill_name: Name of the skill containing the resource.
        resource_name: Exact name of the resource as listed in the skill.
        args: Arguments for callable resources (optional for static files).

    Returns:
        The resource content as a string.
    """
    adapter = await _get_adapter(tool_config)
    return await adapter.read_skill_resource(
        skill_name, resource_name, args=args
    )


async def run_skill_script(
    tool_config: SkillsToolConfig,
    skill_name: str,
    script_name: str,
    args: dict[str, Any] | None = None,
) -> str:
    """Execute a skill script.

    Args:
        skill_name: Name of the skill containing the script.
        script_name: Exact name of the script as listed in the skill.
        args: Arguments required by the script.

    Returns:
        Script execution output.
    """
    adapter = await _get_adapter(tool_config)
    return await adapter.run_skill_script(
        skill_name, script_name, args=args
    )
```

### 1.6 Exceptions Module (`src/soliplex_skills/exceptions.py`)

```python
"""Soliplex-specific exceptions for Skills adapter."""

from __future__ import annotations


class SoliplexSkillsError(Exception):
    """Base exception for soliplex_skills errors."""


class SkillsConfigurationError(SoliplexSkillsError):
    """Configuration-related errors."""
```

### 1.7 Init Module (`src/soliplex_skills/__init__.py`)

```python
"""Soliplex Skills Adapter.

Integrates pydantic-ai-skills into the Soliplex framework.
"""

from __future__ import annotations

from importlib.metadata import version

# Configuration
from soliplex_skills.config import ListSkillsConfig
from soliplex_skills.config import LoadSkillConfig
from soliplex_skills.config import ReadSkillResourceConfig
from soliplex_skills.config import RunSkillScriptConfig
from soliplex_skills.config import SkillsToolConfig
from soliplex_skills.config import SkillsToolSettings

# Exceptions
from soliplex_skills.exceptions import SkillsConfigurationError
from soliplex_skills.exceptions import SoliplexSkillsError

# Tools (for direct import in room configs)
from soliplex_skills.tools import list_skills
from soliplex_skills.tools import load_skill
from soliplex_skills.tools import read_skill_resource
from soliplex_skills.tools import run_skill_script

__all__ = [
    # Configuration
    "SkillsToolConfig",
    "SkillsToolSettings",
    "ListSkillsConfig",
    "LoadSkillConfig",
    "ReadSkillResourceConfig",
    "RunSkillScriptConfig",
    # Exceptions
    "SoliplexSkillsError",
    "SkillsConfigurationError",
    # Tools
    "list_skills",
    "load_skill",
    "read_skill_resource",
    "run_skill_script",
]

__version__ = version("soliplex-skills")
```

### 1.8 Gate Criteria - Phase 1

| Criterion | Target | Status |
|-----------|--------|--------|
| Project structure | Complete | ⏳ |
| pyproject.toml | Valid | ⏳ |
| Upstream integration | Working | ⏳ |
| Ruff lint | 0 errors | ⏳ |
| Unit tests | Pass | ⏳ |
| Coverage | ≥80% | ⏳ |

**Gate Checklist:**
- [ ] Directory layout matches spec
- [ ] `pip install -e .` succeeds
- [ ] `from pydantic_ai_skills import *` works
- [ ] `ruff check src tests` passes (zero warnings)
- [ ] `pytest tests/unit` passes
- [ ] Coverage ≥80% achieved

---

## Phase 2: Functional Tests + Pydantic Refactor

### Objectives
- **Refactor config to Pydantic-first design** (REQUIRED before testing)
- Test all 4 skill tools against real skill directories
- Verify skill discovery and loading
- Test programmatic skill creation
- Test resource and script execution
- Increase coverage to ≥90%

### 2.1 Pydantic-First Refactor

**Source files to modify:**
- `src/soliplex_skills/config.py` - Convert string fields to native types
- `src/soliplex_skills/adapter.py` - Update cache key logic
- `src/soliplex_skills/tools.py` - Add RunContext support, standardize errors

```python
# config.py refactor target
@dataclasses.dataclass
class SkillsToolConfig(ToolConfig):
    directories: list[pathlib.Path] = Field(default_factory=list)
    exclude_tools: set[str] = Field(default_factory=set)
    validate_skills: bool = True
    max_depth: int = 3
```

### 2.2 Test Skill Directory Structure

```
tests/
└── functional/
    └── test_skills/
        └── research-assistant/
            ├── SKILL.md
            ├── resources/
            │   └── REFERENCES.md
            └── scripts/
                └── search.py
```

### 2.2 Sample SKILL.md

```markdown
---
name: research-assistant
description: Helps with research tasks and finding information
---

# Research Assistant Skill

Use this skill for research tasks including:
- Finding relevant papers and articles
- Summarizing information
- Organizing research notes

## Workflow

1. Use the `REFERENCES.md` resource for citation formatting
2. Run the `search.py` script to find relevant papers
```

### 2.4 Gate Criteria - Phase 2

| Criterion | Target | Status |
|-----------|--------|--------|
| **Pydantic refactor** | No string parsing | ⏳ |
| `directories` type | `list[pathlib.Path]` | ⏳ |
| `exclude_tools` type | `set[str]` | ⏳ |
| Functional tests | Pass | ⏳ |
| Skill discovery | Working | ⏳ |
| Programmatic skills | Working | ⏳ |
| Resource loading | Working | ⏳ |
| Script execution | Working | ⏳ |
| Coverage | ≥90% | ⏳ |

**Gate Checklist:**
- [ ] All 4 tools tested with real skill directories
- [ ] Skill discovery from multiple directories works
- [ ] Programmatic skill creation works
- [ ] Static and callable resources work
- [ ] Script execution works
- [ ] Coverage ≥90% achieved

---

## Phase 3: Room Configuration Integration

### Objectives
- Register SkillsToolConfig with Soliplex config system
- Create example room configuration
- Test with actual Soliplex installation
- Document usage patterns

### 3.1 Installation Registration

```yaml
# installation.yaml
meta:
  tool_configs:
    - soliplex_skills.config.ListSkillsConfig
    - soliplex_skills.config.LoadSkillConfig
    - soliplex_skills.config.ReadSkillResourceConfig
    - soliplex_skills.config.RunSkillScriptConfig
```

### 3.2 Example Room Configuration

```yaml
# example/rooms/skills-demo/room_config.yaml
id: skills-demo
name: Skills Demo Assistant
description: Demonstrates skills integration with Soliplex

agent:
  model_name: qwen3-coder-tools:30b
  system_prompt: |
    You are a helpful assistant with access to specialized skills.
    Use list_skills to discover available capabilities.
    Load skills as needed for domain-specific tasks.

tools:
  - tool_name: soliplex_skills.tools.list_skills
    directories: ./skills
  - tool_name: soliplex_skills.tools.load_skill
    directories: ./skills
  - tool_name: soliplex_skills.tools.read_skill_resource
    directories: ./skills
  - tool_name: soliplex_skills.tools.run_skill_script
    directories: ./skills
    exclude_tools: ""  # Enable all tools

suggestions:
  - "What skills are available?"
  - "Load the research-assistant skill"
  - "Help me find papers on machine learning"
```

### 3.3 Per-Room Skills Configuration

Rooms can override skills settings:

```yaml
# Room with custom skills directory
tools:
  - tool_name: soliplex_skills.tools.list_skills
    directories: /path/to/custom/skills

# Room with script execution disabled
tools:
  - tool_name: soliplex_skills.tools.list_skills
    exclude_tools: run_skill_script
```

### 3.4 Gate Criteria - Phase 3

| Criterion | Target | Status |
|-----------|--------|--------|
| Config registration | Working | ⏳ |
| Example room | Complete | ⏳ |
| Tools callable | Working | ⏳ |
| Integration tests | Pass | ⏳ |
| Documentation | Updated | ⏳ |

**Gate Checklist:**
- [ ] SkillsToolConfig classes load from YAML
- [ ] example/ directory with working room provided
- [ ] All tools work from room configuration
- [ ] End-to-end test with Soliplex passes
- [ ] README reflects room usage patterns

---

## Phase 4: Polish & Release

### Objectives
- Complete documentation
- Add comprehensive error handling
- CI/CD setup
- Release preparation

### 4.1 Final Checklist

| Item | Status | Notes |
|------|--------|-------|
| README.md | ⏳ | Complete documentation |
| CONTRIBUTING.md | ⏳ | Development guide |
| LICENSE | ⏳ | MIT license |
| pyproject.toml | ⏳ | All metadata |
| Type hints | ⏳ | 100% coverage |
| Docstrings | ⏳ | All public APIs |
| Unit tests | ⏳ | ≥95% coverage |
| Functional tests | ⏳ | Integration verified |
| Ruff lint | ⏳ | 0 errors |
| Example room | ⏳ | Working configuration |

### 4.2 Gate Criteria - Phase 4 (Final)

| Criterion | Target | Status |
|-----------|--------|--------|
| All tests pass | Yes | ⏳ |
| Coverage ≥95% | Yes | ⏳ |
| Ruff clean | Yes | ⏳ |
| Documentation | Complete | ⏳ |
| Example works | Yes | ⏳ |
| Package builds | Yes | ⏳ |

**Gate Checklist:**
- [ ] `pytest` succeeds (all tests pass)
- [ ] Coverage ≥95% achieved
- [ ] `ruff check` passes (zero errors)
- [ ] README.md covers all features
- [ ] Example room config functional
- [ ] `pip install .` succeeds
- [ ] Release tagged

---

## Summary

| Phase | Key Deliverables | Status |
|-------|-----------------|--------|
| 1. Foundation | Project setup, upstream integration, config | ✅ |
| 2. Functional Tests | Integration tests, skill discovery | ⏳ |
| 3. Room Integration | Full Soliplex configuration support | ⏳ |
| 4. Polish | Documentation, CI, release prep | ⏳ |
| 5. MCP Exposure | Skills as MCP tools for external clients | Future |

### Dependencies

**Runtime:**
- pydantic-ai-skills >= 0.4.0
- pydantic >= 2.0.0
- pydantic-ai >= 0.5.0
- soliplex (optional, for full integration)

**Development:**
- pytest, pytest-asyncio, pytest-cov
- ruff
- coverage

### Risk Mitigation

1. **Upstream changes**: Pin to specific version if needed
2. **API compatibility**: Adapter pattern isolates changes
3. **Testing**: High coverage ensures regressions caught early
4. **Security**: Honor exclude_tools for script execution control
