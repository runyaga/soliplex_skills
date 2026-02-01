"""Soliplex ToolConfig integration for Skills tools.

Bridges pydantic-ai-skills with Soliplex's configuration system.
Uses native Pydantic types - no string parsing in config objects.
"""

from __future__ import annotations

import dataclasses
import pathlib
from typing import TYPE_CHECKING
from typing import Any

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

# Handle optional soliplex dependency
try:
    from soliplex.config import ToolConfig
except ImportError:

    @dataclasses.dataclass
    class ToolConfig:  # type: ignore[no-redef]
        """Stub ToolConfig for standalone testing without Soliplex."""

        tool_name: str = ""
        agui_feature_names: tuple[str, ...] = ()
        allow_mcp: bool = False
        _tool: Any = None
        _installation_config: Any = None
        _config_path: pathlib.Path | None = None

        @classmethod
        def from_yaml(
            cls,
            installation_config: Any,
            config_path: pathlib.Path,
            config: dict[str, Any],
        ) -> ToolConfig:
            """Create from YAML configuration."""
            config["_installation_config"] = installation_config
            config["_config_path"] = config_path
            return cls(**config)


if TYPE_CHECKING:
    from pydantic_ai_skills import SkillsToolset


class SkillsToolSettings(BaseSettings):
    """Environment-based configuration for Skills tools.

    Environment variables use simple string formats for shell compatibility.
    These are converted to proper types when creating SkillsToolConfig.

    Environment variables:
        SOLIPLEX_SKILLS_DIRECTORIES: Comma-separated skill directories
        SOLIPLEX_SKILLS_VALIDATE: Validate skill structure (default: True)
        SOLIPLEX_SKILLS_MAX_DEPTH: Max discovery depth (default: 3)
        SOLIPLEX_SKILLS_EXCLUDE_TOOLS: Comma-separated tools to exclude
    """

    model_config = SettingsConfigDict(env_prefix="SOLIPLEX_SKILLS_")

    directories: str = "./skills"
    validate: bool = True
    max_depth: int = 3
    exclude_tools: str = ""

    def parse_directories(self) -> list[pathlib.Path]:
        """Convert comma-separated directories to list of Paths."""
        if not self.directories:
            return []
        return [
            pathlib.Path(d.strip())
            for d in self.directories.split(",")
            if d.strip()
        ]

    def parse_exclude_tools(self) -> set[str]:
        """Convert comma-separated exclude_tools to set."""
        if not self.exclude_tools:
            return set()
        return {t.strip() for t in self.exclude_tools.split(",") if t.strip()}


def _get_env_settings() -> SkillsToolSettings:
    """Lazy-load environment settings."""
    return SkillsToolSettings()


def _parse_directories_input(
    value: str | list[str] | list[pathlib.Path] | None,
    config_path: pathlib.Path | None,
) -> tuple[pathlib.Path, ...]:
    """Parse directories from YAML (list or string) to tuple of resolved Paths.

    Args:
        value: Raw value from YAML config or env settings
        config_path: Path to room_config.yaml for relative path resolution

    Returns:
        Tuple of resolved absolute Paths (hashable for cache keys)
    """
    if value is None:
        return ()

    # Normalize to list
    if isinstance(value, str):
        raw_list = [d.strip() for d in value.split(",") if d.strip()]
    else:
        raw_list = list(value)

    # Resolve paths
    resolved: list[pathlib.Path] = []
    for item in raw_list:
        path = pathlib.Path(item) if isinstance(item, str) else item
        if not path.is_absolute() and config_path:
            path = (config_path.parent / path).resolve()
        else:
            path = path.resolve()
        resolved.append(path)

    return tuple(resolved)


def _parse_exclude_tools_input(
    value: str | list[str] | set[str] | None,
) -> frozenset[str]:
    """Parse exclude_tools from YAML (list, set, or string) to frozenset.

    Args:
        value: Raw value from YAML config or env settings

    Returns:
        Frozenset of tool names (hashable for cache keys)
    """
    if value is None:
        return frozenset()

    if isinstance(value, str):
        return frozenset(t.strip() for t in value.split(",") if t.strip())
    elif isinstance(value, set):
        return frozenset(value)
    else:
        return frozenset(value)


@dataclasses.dataclass
class SkillsToolConfig(ToolConfig):
    """Configuration for Skills tools.

    Uses native Pydantic types - no string parsing after construction.
    Inherits from soliplex.config.ToolConfig for full Soliplex integration.

    Attributes:
        directories: Tuple of resolved absolute paths to skill directories
        exclude_tools: Frozenset of tool names to exclude
        validate_skills: Whether to validate skill structure on load
        max_depth: Maximum directory depth for skill discovery
    """

    # Native Pydantic types - tuple/frozenset for hashability (cache keys)
    directories: tuple[pathlib.Path, ...] = dataclasses.field(
        default_factory=lambda: _parse_directories_input(
            _get_env_settings().directories, None
        )
    )
    exclude_tools: frozenset[str] = dataclasses.field(
        default_factory=lambda: _parse_exclude_tools_input(
            _get_env_settings().exclude_tools
        )
    )
    validate_skills: bool = dataclasses.field(
        default_factory=lambda: _get_env_settings().validate
    )
    max_depth: int = dataclasses.field(
        default_factory=lambda: _get_env_settings().max_depth
    )

    @classmethod
    def from_yaml(
        cls,
        installation_config: Any,
        config_path: pathlib.Path,
        config: dict[str, Any],
    ) -> SkillsToolConfig:
        """Create from Soliplex YAML configuration.

        Handles both YAML lists and comma-separated strings for directories
        and exclude_tools. Resolves relative paths against config_path.parent.

        Example YAML formats supported:
            # List format (preferred)
            directories:
              - ./skills
              - ../shared/skills

            # String format (legacy/env var compatible)
            directories: ./skills,../shared/skills
        """
        env_settings = _get_env_settings()

        # Parse directories - supports list or string
        raw_dirs = config.get("directories", env_settings.directories)
        directories = _parse_directories_input(raw_dirs, config_path)

        # Parse exclude_tools - supports list, set, or string
        raw_exclude = config.get("exclude_tools", env_settings.exclude_tools)
        exclude_tools = _parse_exclude_tools_input(raw_exclude)

        # Accept both "validate" and "validate_skills" YAML keys
        validate_value = config.get(
            "validate_skills",
            config.get("validate", env_settings.validate),
        )

        return cls(
            tool_name=config.get("tool_name", ""),
            directories=directories,
            exclude_tools=exclude_tools,
            validate_skills=validate_value,
            max_depth=config.get("max_depth", env_settings.max_depth),
            _installation_config=installation_config,
            _config_path=config_path,
        )

    def create_toolset(self) -> SkillsToolset:
        """Create SkillsToolset from this configuration."""
        from pydantic_ai_skills import SkillsToolset

        return SkillsToolset(
            directories=[str(p) for p in self.directories],
            validate=self.validate_skills,
            max_depth=self.max_depth,
            exclude_tools=set(self.exclude_tools),
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
