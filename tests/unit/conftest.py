"""Shared test fixtures for unit tests."""

from __future__ import annotations

import pathlib
import tempfile
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield pathlib.Path(tmpdir)


@pytest.fixture
def mock_skill():
    """Create a mock Skill object."""
    skill = MagicMock()
    skill.name = "test-skill"
    skill.description = "A test skill"
    skill.content = "Test instructions"
    skill.uri = "https://example.com/test-skill"
    skill.resources = []
    skill.scripts = []
    return skill


@pytest.fixture
def mock_skill_with_resources():
    """Create a mock Skill with resources and scripts."""
    skill = MagicMock()
    skill.name = "research-assistant"
    skill.description = "Helps with research"
    skill.content = "Research instructions"
    skill.uri = None

    resource = MagicMock()
    resource.name = "references"
    resource.load = AsyncMock(return_value="Reference content")
    skill.resources = [resource]

    script = MagicMock()
    script.name = "search"
    script.run = AsyncMock(return_value="Search results")
    skill.scripts = [script]

    return skill


@pytest.fixture
def mock_toolset(mock_skill):
    """Create a mock SkillsToolset."""
    toolset = MagicMock()
    toolset.skills = {mock_skill.name: mock_skill}
    return toolset


@pytest.fixture
def mock_config(temp_dir):
    """Create a mock SkillsToolConfig."""
    from soliplex_skills.config import SkillsToolConfig

    config = SkillsToolConfig(
        tool_name="soliplex_skills.tools.list_skills",
        directories=((temp_dir / "skills").resolve(),),
        validate_skills=True,
        max_depth=3,
        exclude_tools=frozenset(),
        _config_path=temp_dir / "room_config.yaml",
    )
    return config


@pytest.fixture
def sample_room_config_yaml():
    """Return sample room_config.yaml content."""
    return """
id: test-room
name: Test Room
description: A test room

agent:
  template_id: default_chat

tools:
  - tool_name: soliplex_skills.tools.list_skills
    directories: ./skills

  - tool_name: soliplex_skills.tools.load_skill
    directories: ./skills
"""
