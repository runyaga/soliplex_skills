"""Tests for soliplex_skills.tools module."""

from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from soliplex_skills import tools
from soliplex_skills.adapter import close_all


class TestListSkills:
    """Test list_skills tool function."""

    @pytest.fixture(autouse=True)
    async def clear_cache(self):
        """Clear adapter cache before each test."""
        await close_all()
        yield
        await close_all()

    async def test_returns_skill_dict(self, mock_config):
        """Test list_skills returns dictionary of skills."""
        mock_adapter = MagicMock()
        mock_adapter.list_skills = AsyncMock(
            return_value={"test-skill": "A test skill"}
        )

        with patch.object(tools, "_get_adapter", return_value=mock_adapter):
            result = await tools.list_skills(mock_config)

        assert result == {"test-skill": "A test skill"}

    async def test_returns_error_string_on_failure(self, mock_config):
        """Test list_skills returns error string on exception."""
        with patch.object(
            tools, "_get_adapter", side_effect=Exception("Connection failed")
        ):
            result = await tools.list_skills(mock_config)

        assert isinstance(result, str)
        assert "Error:" in result
        assert "Connection failed" in result


class TestLoadSkill:
    """Test load_skill tool function."""

    @pytest.fixture(autouse=True)
    async def clear_cache(self):
        """Clear adapter cache before each test."""
        await close_all()
        yield
        await close_all()

    async def test_returns_skill_content(self, mock_config):
        """Test load_skill returns skill instructions."""
        mock_adapter = MagicMock()
        mock_adapter.load_skill = AsyncMock(return_value="<skill>...</skill>")

        with patch.object(tools, "_get_adapter", return_value=mock_adapter):
            result = await tools.load_skill(mock_config, "test-skill")

        assert result == "<skill>...</skill>"

    async def test_returns_error_string_on_not_found(self, mock_config):
        """Test load_skill returns error string for missing skill."""
        from pydantic_ai_skills import SkillNotFoundError

        mock_adapter = MagicMock()
        err = SkillNotFoundError("test")
        mock_adapter.load_skill = AsyncMock(side_effect=err)
        mock_adapter.skills = {"other-skill": MagicMock()}

        with patch.object(tools, "_get_adapter", return_value=mock_adapter):
            result = await tools.load_skill(mock_config, "missing-skill")

        assert "Error:" in result
        assert "missing-skill" in result
        assert "not found" in result.lower()

    async def test_returns_error_string_on_exception(self, mock_config):
        """Test load_skill returns error string on general exception."""
        mock_adapter = MagicMock()
        err = RuntimeError("IO Error")
        mock_adapter.load_skill = AsyncMock(side_effect=err)

        with patch.object(tools, "_get_adapter", return_value=mock_adapter):
            result = await tools.load_skill(mock_config, "test-skill")

        assert "Error" in result
        assert "IO Error" in result

    async def test_not_found_error_with_adapter_failure(self, mock_config):
        """Test load_skill handles failure getting available skills list."""
        from pydantic_ai_skills import SkillNotFoundError

        # First call succeeds (for load_skill), returns SkillNotFoundError
        # Second call (to get available skills) fails
        call_count = 0

        async def failing_get_adapter(config):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock = MagicMock()
                mock.load_skill = AsyncMock(
                    side_effect=SkillNotFoundError("test")
                )
                return mock
            else:
                msg = "Adapter unavailable"
                raise RuntimeError(msg)

        with patch.object(
            tools, "_get_adapter", side_effect=failing_get_adapter
        ):
            result = await tools.load_skill(mock_config, "missing-skill")

        assert "Error:" in result
        assert "missing-skill" in result
        assert "unavailable" in result


class TestReadSkillResource:
    """Test read_skill_resource tool function."""

    @pytest.fixture(autouse=True)
    async def clear_cache(self):
        """Clear adapter cache before each test."""
        await close_all()
        yield
        await close_all()

    async def test_returns_resource_content(self, mock_config):
        """Test read_skill_resource returns resource content."""
        mock_adapter = MagicMock()
        mock_adapter.read_skill_resource = AsyncMock(
            return_value="Resource data"
        )

        with patch.object(tools, "_get_adapter", return_value=mock_adapter):
            result = await tools.read_skill_resource(
                mock_config, "test-skill", "my-resource"
            )

        assert result == "Resource data"

    async def test_returns_error_on_skill_not_found(self, mock_config):
        """Test returns error when skill not found."""
        from pydantic_ai_skills import SkillNotFoundError

        mock_adapter = MagicMock()
        mock_adapter.read_skill_resource = AsyncMock(
            side_effect=SkillNotFoundError("test")
        )

        with patch.object(tools, "_get_adapter", return_value=mock_adapter):
            result = await tools.read_skill_resource(
                mock_config, "missing-skill", "resource"
            )

        assert "Error:" in result
        assert "missing-skill" in result

    async def test_returns_error_on_resource_not_found(self, mock_config):
        """Test returns error when resource not found."""
        from pydantic_ai_skills import SkillResourceNotFoundError

        mock_adapter = MagicMock()
        mock_adapter.read_skill_resource = AsyncMock(
            side_effect=SkillResourceNotFoundError("Resource 'x' not found")
        )

        with patch.object(tools, "_get_adapter", return_value=mock_adapter):
            result = await tools.read_skill_resource(
                mock_config, "test-skill", "missing"
            )

        assert "Error:" in result

    async def test_returns_error_on_general_exception(self, mock_config):
        """Test returns error on general exception during resource read."""
        mock_adapter = MagicMock()
        mock_adapter.read_skill_resource = AsyncMock(
            side_effect=RuntimeError("IO Error")
        )

        with patch.object(tools, "_get_adapter", return_value=mock_adapter):
            result = await tools.read_skill_resource(
                mock_config, "test-skill", "my-resource"
            )

        assert "Error" in result
        assert "my-resource" in result
        assert "test-skill" in result
        assert "IO Error" in result


class TestRunSkillScript:
    """Test run_skill_script tool function."""

    @pytest.fixture(autouse=True)
    async def clear_cache(self):
        """Clear adapter cache before each test."""
        await close_all()
        yield
        await close_all()

    async def test_returns_script_output(self, mock_config):
        """Test run_skill_script returns script output."""
        mock_adapter = MagicMock()
        mock_adapter.run_skill_script = AsyncMock(return_value="Script output")

        with patch.object(tools, "_get_adapter", return_value=mock_adapter):
            result = await tools.run_skill_script(
                mock_config, "test-skill", "my-script"
            )

        assert result == "Script output"

    async def test_passes_args_to_script(self, mock_config):
        """Test run_skill_script passes args to adapter."""
        mock_adapter = MagicMock()
        mock_adapter.run_skill_script = AsyncMock(return_value="Result")

        with patch.object(tools, "_get_adapter", return_value=mock_adapter):
            await tools.run_skill_script(
                mock_config,
                "test-skill",
                "my-script",
                args={"query": "test"},
            )

        mock_adapter.run_skill_script.assert_called_once_with(
            "test-skill", "my-script", args={"query": "test"}
        )

    async def test_returns_error_on_skill_not_found(self, mock_config):
        """Test returns error when skill not found."""
        from pydantic_ai_skills import SkillNotFoundError

        mock_adapter = MagicMock()
        mock_adapter.run_skill_script = AsyncMock(
            side_effect=SkillNotFoundError("test")
        )

        with patch.object(tools, "_get_adapter", return_value=mock_adapter):
            result = await tools.run_skill_script(
                mock_config, "missing-skill", "script"
            )

        assert "Error:" in result
        assert "missing-skill" in result

    async def test_returns_error_on_script_not_found(self, mock_config):
        """Test returns error when script not found."""
        from pydantic_ai_skills import SkillResourceNotFoundError

        mock_adapter = MagicMock()
        mock_adapter.run_skill_script = AsyncMock(
            side_effect=SkillResourceNotFoundError("Script 'x' not found")
        )

        with patch.object(tools, "_get_adapter", return_value=mock_adapter):
            result = await tools.run_skill_script(
                mock_config, "test-skill", "missing-script"
            )

        assert "Error:" in result

    async def test_returns_error_on_execution_failure(self, mock_config):
        """Test returns error when script execution fails."""
        mock_adapter = MagicMock()
        mock_adapter.run_skill_script = AsyncMock(
            side_effect=RuntimeError("Execution failed")
        )

        with patch.object(tools, "_get_adapter", return_value=mock_adapter):
            result = await tools.run_skill_script(
                mock_config, "test-skill", "bad-script"
            )

        assert "Error" in result
        assert "Execution failed" in result
