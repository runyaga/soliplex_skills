"""Configuration for introspection tools.

These tools enable cross-room discovery and delegation.
"""

from __future__ import annotations

import dataclasses
import pathlib
from typing import Any

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


@dataclasses.dataclass
class IntrospectionToolConfig(ToolConfig):
    """Configuration for introspection tools.

    Attributes:
        include_tools: Whether to include tool lists in room discovery
        include_model: Whether to include model info in room discovery
        exclude_rooms: Room IDs to exclude from discovery
        max_delegation_depth: Maximum recursion depth for delegation
        use_auth_filter: Whether to filter rooms by user authorization
            (requires soliplex.authz to be available)
    """

    include_tools: bool = True
    include_model: bool = True
    exclude_rooms: frozenset[str] = dataclasses.field(
        default_factory=frozenset
    )
    max_delegation_depth: int = 2
    use_auth_filter: bool = False  # Off by default for backward compat

    @classmethod
    def from_yaml(
        cls,
        installation_config: Any,
        config_path: pathlib.Path,
        config: dict[str, Any],
    ) -> IntrospectionToolConfig:
        """Create from Soliplex YAML configuration."""
        # Parse exclude_rooms - supports list or set
        raw_exclude = config.get("exclude_rooms", [])
        if isinstance(raw_exclude, (list, set)):
            exclude_rooms = frozenset(raw_exclude)
        else:
            exclude_rooms = frozenset()

        return cls(
            tool_name=config.get("tool_name", ""),
            include_tools=config.get("include_tools", True),
            include_model=config.get("include_model", True),
            exclude_rooms=exclude_rooms,
            max_delegation_depth=config.get("max_delegation_depth", 2),
            use_auth_filter=config.get("use_auth_filter", False),
            _installation_config=installation_config,
            _config_path=config_path,
        )


@dataclasses.dataclass
class DiscoverRoomsConfig(IntrospectionToolConfig):
    """Config for discover_rooms tool."""

    tool_name: str = "soliplex_skills.introspection.tools.discover_rooms"


@dataclasses.dataclass
class DelegateToRoomConfig(IntrospectionToolConfig):
    """Config for delegate_to_room tool."""

    tool_name: str = "soliplex_skills.introspection.tools.delegate_to_room"
