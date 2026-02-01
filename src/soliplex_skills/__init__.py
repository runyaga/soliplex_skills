"""Soliplex Skills Adapter.

Integrates pydantic-ai-skills into the Soliplex framework.
"""

from __future__ import annotations

# Configuration
from soliplex_skills.config import ListSkillsConfig
from soliplex_skills.config import LoadSkillConfig
from soliplex_skills.config import ReadSkillResourceConfig
from soliplex_skills.config import RunSkillScriptConfig
from soliplex_skills.config import SkillsToolConfig
from soliplex_skills.config import SkillsToolSettings

# Exceptions
from soliplex_skills.exceptions import SkillsAdapterError
from soliplex_skills.exceptions import SkillsConfigurationError
from soliplex_skills.exceptions import SoliplexSkillsError

# Introspection tools
from soliplex_skills.introspection import DelegateToRoomConfig
from soliplex_skills.introspection import DelegationError
from soliplex_skills.introspection import DelegationResult
from soliplex_skills.introspection import DiscoverRoomsConfig
from soliplex_skills.introspection import IntrospectionToolConfig
from soliplex_skills.introspection import delegate_to_room
from soliplex_skills.introspection import discover_rooms

# Tools (for direct import in room configs)
from soliplex_skills.tools import list_skills
from soliplex_skills.tools import load_skill
from soliplex_skills.tools import read_skill_resource
from soliplex_skills.tools import run_skill_script

__all__ = [
    "DelegateToRoomConfig",
    "DelegationError",
    "DelegationResult",
    "DiscoverRoomsConfig",
    "IntrospectionToolConfig",
    "ListSkillsConfig",
    "LoadSkillConfig",
    "ReadSkillResourceConfig",
    "RunSkillScriptConfig",
    "SkillsAdapterError",
    "SkillsConfigurationError",
    "SkillsToolConfig",
    "SkillsToolSettings",
    "SoliplexSkillsError",
    "delegate_to_room",
    "discover_rooms",
    "list_skills",
    "load_skill",
    "read_skill_resource",
    "run_skill_script",
]

try:
    from importlib.metadata import version

    __version__ = version("soliplex-skills")
except Exception:
    __version__ = "0.0.0.dev0"
