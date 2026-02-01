"""Tests for soliplex_skills.adapter module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from soliplex_skills.adapter import SoliplexSkillsAdapter
from soliplex_skills.adapter import _get_toolset
from soliplex_skills.adapter import _toolset_cache
from soliplex_skills.adapter import close_all


class TestGetToolset:
    """Test _get_toolset caching function."""

    @pytest.fixture(autouse=True)
    async def clear_cache(self):
        """Clear cache before each test."""
        await close_all()
        yield
        await close_all()

    async def test_creates_toolset_on_first_call(self, mock_config):
        """Test toolset is created on first call."""
        mock_toolset = MagicMock()
        mock_config.create_toolset = MagicMock(return_value=mock_toolset)

        result = await _get_toolset(mock_config)

        assert result is mock_toolset
        mock_config.create_toolset.assert_called_once()

    async def test_caches_toolset(self, mock_config):
        """Test toolset is cached on subsequent calls."""
        mock_toolset = MagicMock()
        mock_config.create_toolset = MagicMock(return_value=mock_toolset)

        result1 = await _get_toolset(mock_config)
        result2 = await _get_toolset(mock_config)

        assert result1 is result2
        mock_config.create_toolset.assert_called_once()

    async def test_different_configs_different_toolsets(self, temp_dir):
        """Test different configs create different toolsets."""
        from soliplex_skills.config import SkillsToolConfig

        config1 = SkillsToolConfig(
            tool_name="test1",
            directories=((temp_dir / "skills1").resolve(),),
        )
        config2 = SkillsToolConfig(
            tool_name="test2",
            directories=((temp_dir / "skills2").resolve(),),
        )

        toolset1 = MagicMock()
        toolset2 = MagicMock()
        config1.create_toolset = MagicMock(return_value=toolset1)
        config2.create_toolset = MagicMock(return_value=toolset2)

        result1 = await _get_toolset(config1)
        result2 = await _get_toolset(config2)

        assert result1 is not result2


class TestCloseAll:
    """Test close_all cache clearing function."""

    async def test_clears_cache(self, mock_config):
        """Test close_all clears the cache."""
        mock_toolset = MagicMock()
        mock_config.create_toolset = MagicMock(return_value=mock_toolset)

        await _get_toolset(mock_config)
        assert len(_toolset_cache) > 0

        await close_all()
        assert len(_toolset_cache) == 0


class TestSoliplexSkillsAdapter:
    """Test SoliplexSkillsAdapter class."""

    def test_skills_property(self, mock_toolset, mock_skill):
        """Test skills property returns toolset skills."""
        adapter = SoliplexSkillsAdapter(mock_toolset)
        assert adapter.skills == {mock_skill.name: mock_skill}

    async def test_list_skills(self, mock_toolset, mock_skill):
        """Test list_skills returns name->description mapping."""
        adapter = SoliplexSkillsAdapter(mock_toolset)
        result = await adapter.list_skills()

        assert result == {mock_skill.name: mock_skill.description}

    async def test_list_skills_empty(self):
        """Test list_skills with no skills."""
        toolset = MagicMock()
        toolset.skills = {}
        adapter = SoliplexSkillsAdapter(toolset)

        result = await adapter.list_skills()
        assert result == {}

    async def test_load_skill_success(self, mock_toolset, mock_skill):
        """Test load_skill returns formatted instructions."""
        adapter = SoliplexSkillsAdapter(mock_toolset)
        result = await adapter.load_skill(mock_skill.name)

        assert "<skill>" in result
        assert f"<name>{mock_skill.name}</name>" in result
        assert mock_skill.content in result

    async def test_load_skill_not_found(self, mock_toolset):
        """Test load_skill raises SkillNotFoundError."""
        from pydantic_ai_skills import SkillNotFoundError

        adapter = SoliplexSkillsAdapter(mock_toolset)

        with pytest.raises(SkillNotFoundError) as exc_info:
            await adapter.load_skill("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    async def test_read_skill_resource_success(
        self, mock_skill_with_resources
    ):
        """Test read_skill_resource loads resource content."""
        toolset = MagicMock()
        skill = mock_skill_with_resources
        toolset.skills = {skill.name: skill}
        adapter = SoliplexSkillsAdapter(toolset)

        result = await adapter.read_skill_resource(
            mock_skill_with_resources.name,
            "references",
        )

        assert result == "Reference content"

    async def test_read_skill_resource_not_found(
        self, mock_toolset, mock_skill
    ):
        """Test read_skill_resource raises error for missing resource."""
        from pydantic_ai_skills import SkillResourceNotFoundError

        adapter = SoliplexSkillsAdapter(mock_toolset)

        with pytest.raises(SkillResourceNotFoundError):
            await adapter.read_skill_resource(mock_skill.name, "nonexistent")

    async def test_run_skill_script_success(
        self, mock_skill_with_resources
    ):
        """Test run_skill_script executes script."""
        toolset = MagicMock()
        skill = mock_skill_with_resources
        toolset.skills = {skill.name: skill}
        adapter = SoliplexSkillsAdapter(toolset)

        result = await adapter.run_skill_script(
            mock_skill_with_resources.name,
            "search",
        )

        assert result == "Search results"

    async def test_run_skill_script_not_found(self, mock_toolset, mock_skill):
        """Test run_skill_script raises error for missing script."""
        from pydantic_ai_skills import SkillResourceNotFoundError

        adapter = SoliplexSkillsAdapter(mock_toolset)

        with pytest.raises(SkillResourceNotFoundError):
            await adapter.run_skill_script(mock_skill.name, "nonexistent")
