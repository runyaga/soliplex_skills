"""Shared fixtures for functional tests."""

from __future__ import annotations

import pathlib

import pytest

from soliplex_skills.adapter import close_all
from soliplex_skills.config import SkillsToolConfig

# Path to test skills directories
FUNCTIONAL_DIR = pathlib.Path(__file__).parent
TEST_SKILLS_DIR = FUNCTIONAL_DIR / "test_skills"
TEST_SKILLS_ALT_DIR = FUNCTIONAL_DIR / "test_skills_alt"


@pytest.fixture
def test_skills_path() -> pathlib.Path:
    """Return path to primary test skills directory."""
    return TEST_SKILLS_DIR


@pytest.fixture
def test_skills_alt_path() -> pathlib.Path:
    """Return path to alternate test skills directory."""
    return TEST_SKILLS_ALT_DIR


@pytest.fixture
def single_dir_config(test_skills_path: pathlib.Path) -> SkillsToolConfig:
    """Config with single skills directory."""
    return SkillsToolConfig(
        tool_name="test",
        directories=(test_skills_path.resolve(),),
        validate_skills=True,
        max_depth=3,
        exclude_tools=frozenset(),
    )


@pytest.fixture
def multi_dir_config(
    test_skills_path: pathlib.Path,
    test_skills_alt_path: pathlib.Path,
) -> SkillsToolConfig:
    """Config with multiple skills directories."""
    return SkillsToolConfig(
        tool_name="test",
        directories=(
            test_skills_path.resolve(),
            test_skills_alt_path.resolve(),
        ),
        validate_skills=True,
        max_depth=3,
        exclude_tools=frozenset(),
    )


@pytest.fixture(autouse=True)
async def clear_cache():
    """Clear adapter cache before and after each test."""
    await close_all()
    yield
    await close_all()
