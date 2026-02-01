"""Soliplex-compatible tool functions.

These tools follow Soliplex conventions:
- Accept tool_config: SkillsToolConfig (injected by Soliplex)
- Async tool functions
- Return user-friendly error strings instead of raising exceptions
"""

from __future__ import annotations

from typing import Any

from pydantic_ai_skills import SkillNotFoundError
from pydantic_ai_skills import SkillResourceNotFoundError

from soliplex_skills.adapter import SoliplexSkillsAdapter
from soliplex_skills.adapter import _get_toolset
from soliplex_skills.config import SkillsToolConfig


async def _get_adapter(config: SkillsToolConfig) -> SoliplexSkillsAdapter:
    """Get adapter from config."""
    toolset = await _get_toolset(config)
    return SoliplexSkillsAdapter(toolset)


async def list_skills(
    tool_config: SkillsToolConfig,
) -> dict[str, str] | str:
    """List all available skills.

    Returns:
        Dictionary mapping skill names to their descriptions.
        Empty dictionary if no skills are available.
        Returns error message string on failure.
    """
    try:
        adapter = await _get_adapter(tool_config)
        return await adapter.list_skills()
    except Exception as e:
        return f"Error: Failed to list skills: {e}"


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
        Returns error message string if skill not found.
    """
    try:
        adapter = await _get_adapter(tool_config)
        return await adapter.load_skill(skill_name)
    except SkillNotFoundError:
        try:
            adapter = await _get_adapter(tool_config)
            available = ", ".join(sorted(adapter.skills.keys())) or "none"
        except Exception:
            available = "unavailable"
        return (
            f"Error: Skill '{skill_name}' not found. "
            f"Available skills: {available}"
        )
    except Exception as e:
        return f"Error loading skill '{skill_name}': {e}"


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
        Returns error message string if resource not found.
    """
    try:
        adapter = await _get_adapter(tool_config)
        return await adapter.read_skill_resource(
            skill_name, resource_name, args=args
        )
    except SkillNotFoundError:
        return f"Error: Skill '{skill_name}' not found."
    except SkillResourceNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        return (
            f"Error reading resource '{resource_name}' "
            f"from '{skill_name}': {e}"
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
        Returns error message string if script not found or execution fails.
    """
    try:
        adapter = await _get_adapter(tool_config)
        return await adapter.run_skill_script(
            skill_name, script_name, args=args
        )
    except SkillNotFoundError:
        return f"Error: Skill '{skill_name}' not found."
    except SkillResourceNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error running script '{script_name}' from '{skill_name}': {e}"
