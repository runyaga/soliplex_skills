"""Core adapter bridging pydantic-ai-skills with Soliplex.

Wraps SkillsToolset to provide Soliplex-compatible tool functions.
"""

from __future__ import annotations

import asyncio
import pathlib
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from pydantic_ai_skills import SkillsToolset

    from soliplex_skills.config import SkillsToolConfig

# Type alias for cache key (all hashable types from SkillsToolConfig)
CacheKey = tuple[
    tuple[pathlib.Path, ...],  # directories
    bool,  # validate_skills
    int,  # max_depth
    frozenset[str],  # exclude_tools
]

# Module-level cache: config key -> toolset (supports concurrent rooms)
_toolset_cache: dict[CacheKey, SkillsToolset] = {}
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
    # Cache key uses hashable types from config (tuple, frozenset)
    key: CacheKey = (
        config.directories,  # tuple[pathlib.Path, ...]
        config.validate_skills,  # bool
        config.max_depth,  # int
        config.exclude_tools,  # frozenset[str]
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


async def close_all() -> None:
    """Clear all cached toolsets.

    Thread-safe cleanup for testing and shutdown.
    """
    async with _cache_lock:
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

        Raises:
            SkillNotFoundError: If skill does not exist
        """
        from pydantic_ai_skills import SkillNotFoundError

        if skill_name not in self._toolset.skills:
            keys = sorted(self._toolset.skills.keys())
            available = ", ".join(keys) or "none"
            msg = f"Skill '{skill_name}' not found. Available: {available}"
            raise SkillNotFoundError(msg)

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
<uri>{skill.uri or "N/A"}</uri>

<resources>
{chr(10).join(resources_list) if resources_list else "<!-- No resources -->"}
</resources>

<scripts>
{chr(10).join(scripts_list) if scripts_list else "<!-- No scripts -->"}
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
            ctx: RunContext for callable resources (optional)

        Returns:
            Resource content

        Raises:
            SkillNotFoundError: If skill does not exist
            SkillResourceNotFoundError: If resource does not exist
        """
        from pydantic_ai_skills import SkillNotFoundError
        from pydantic_ai_skills import SkillResourceNotFoundError

        if skill_name not in self._toolset.skills:
            msg = f"Skill '{skill_name}' not found."
            raise SkillNotFoundError(msg)

        skill = self._toolset.skills[skill_name]

        # Find the resource
        resource = None
        if skill.resources:
            for r in skill.resources:
                if r.name == resource_name:
                    resource = r
                    break

        if resource is None:
            available = (
                [r.name for r in skill.resources] if skill.resources else []
            )
            msg = (
                f"Resource '{resource_name}' not found in skill "
                f"'{skill_name}'. Available: {available}"
            )
            raise SkillResourceNotFoundError(msg)

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
            ctx: RunContext for the script (optional)

        Returns:
            Script output

        Raises:
            SkillNotFoundError: If skill does not exist
            SkillResourceNotFoundError: If script does not exist
        """
        from pydantic_ai_skills import SkillNotFoundError
        from pydantic_ai_skills import SkillResourceNotFoundError

        if skill_name not in self._toolset.skills:
            msg = f"Skill '{skill_name}' not found."
            raise SkillNotFoundError(msg)

        skill = self._toolset.skills[skill_name]

        # Find the script
        script = None
        if skill.scripts:
            for s in skill.scripts:
                if s.name == script_name:
                    script = s
                    break

        if script is None:
            scripts = skill.scripts or []
            available = [s.name for s in scripts]
            msg = (
                f"Script '{script_name}' not found in skill "
                f"'{skill_name}'. Available: {available}"
            )
            raise SkillResourceNotFoundError(msg)

        return await script.run(ctx=ctx, args=args)
