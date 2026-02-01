"""Functional tests for skills integration with real skill directories."""

from __future__ import annotations

import asyncio

from soliplex_skills import tools
from soliplex_skills.adapter import SoliplexSkillsAdapter
from soliplex_skills.adapter import _get_toolset
from soliplex_skills.config import SkillsToolConfig


class TestListSkillsFunctional:
    """Functional tests for list_skills with real skills."""

    async def test_lists_calculator_skill(self, single_dir_config):
        """Test listing skills from test directory."""
        result = await tools.list_skills(single_dir_config)

        assert isinstance(result, dict)
        assert "calculator" in result
        desc = result["calculator"].lower()
        assert "calculator" in desc or "math" in desc

    async def test_lists_skills_from_multiple_dirs(self, multi_dir_config):
        """Test listing skills from multiple directories."""
        result = await tools.list_skills(multi_dir_config)

        assert isinstance(result, dict)
        assert "calculator" in result  # From test_skills
        assert "greeter" in result  # From test_skills_alt

    async def test_returns_empty_for_nonexistent_dir(self, test_skills_path):
        """Test returns empty dict for non-existent directory."""
        config = SkillsToolConfig(
            tool_name="test",
            directories=((test_skills_path / "nonexistent").resolve(),),
        )
        result = await tools.list_skills(config)

        # Should return empty dict, not error
        assert result == {} or isinstance(result, str)


class TestLoadSkillFunctional:
    """Functional tests for load_skill with real skills."""

    async def test_loads_calculator_skill(self, single_dir_config):
        """Test loading calculator skill returns formatted content."""
        result = await tools.load_skill(single_dir_config, "calculator")

        assert "<skill>" in result
        assert "<name>calculator</name>" in result
        lower = result.lower()
        assert "mathematical" in lower or "calculator" in lower
        assert "<resources>" in result
        assert "<scripts>" in result

    async def test_load_skill_includes_resources(self, single_dir_config):
        """Test loaded skill lists available resources."""
        result = await tools.load_skill(single_dir_config, "calculator")

        assert "formulas" in result
        assert "constants" in result

    async def test_load_skill_includes_scripts(self, single_dir_config):
        """Test loaded skill lists available scripts."""
        result = await tools.load_skill(single_dir_config, "calculator")

        assert "compute" in result

    async def test_load_nonexistent_skill_error(self, single_dir_config):
        """Test loading non-existent skill returns error message."""
        result = await tools.load_skill(single_dir_config, "nonexistent-skill")

        assert "Error:" in result
        assert "not found" in result.lower()

    async def test_load_skill_from_alt_directory(self, multi_dir_config):
        """Test loading skill from alternate directory."""
        result = await tools.load_skill(multi_dir_config, "greeter")

        assert "<skill>" in result
        assert "<name>greeter</name>" in result


class TestReadSkillResourceFunctional:
    """Functional tests for read_skill_resource with real resources."""

    async def test_reads_formulas_resource(self, single_dir_config):
        """Test reading formulas resource returns content."""
        # pydantic-ai-skills uses full path as resource name
        result = await tools.read_skill_resource(
            single_dir_config, "calculator", "resources/formulas.md"
        )

        assert "Mathematical Formulas" in result or "Circle area" in result

    async def test_reads_constants_resource(self, single_dir_config):
        """Test reading constants resource returns content."""
        result = await tools.read_skill_resource(
            single_dir_config, "calculator", "resources/constants.md"
        )

        assert "Pi" in result or "3.14159" in result

    async def test_read_nonexistent_resource_error(self, single_dir_config):
        """Test reading non-existent resource returns error."""
        result = await tools.read_skill_resource(
            single_dir_config, "calculator", "nonexistent"
        )

        assert "Error:" in result

    async def test_read_resource_nonexistent_skill(self, single_dir_config):
        """Test reading resource from non-existent skill returns error."""
        result = await tools.read_skill_resource(
            single_dir_config, "nonexistent", "resources/formulas.md"
        )

        assert "Error:" in result
        assert "not found" in result.lower()

    async def test_reads_resource_from_alt_dir(self, multi_dir_config):
        """Test reading resource from skill in alternate directory."""
        result = await tools.read_skill_resource(
            multi_dir_config, "greeter", "resources/templates.md"
        )

        assert "Greeting" in result or "Hello" in result


class TestRunSkillScriptFunctional:
    """Functional tests for run_skill_script with real scripts."""

    async def test_runs_compute_script(self, single_dir_config):
        """Test running compute script executes without error."""
        # pydantic-ai-skills uses full path as script name
        result = await tools.run_skill_script(
            single_dir_config,
            "calculator",
            "scripts/compute.py",
            args={"expression": "2 + 2"},
        )

        # Script execution should return a string (even if empty/default)
        assert isinstance(result, str)
        # Should not be an error about script not found
        assert "not found" not in result.lower()

    async def test_compute_with_args(self, single_dir_config):
        """Test compute script accepts args without error."""
        result = await tools.run_skill_script(
            single_dir_config,
            "calculator",
            "scripts/compute.py",
            args={"expression": "sqrt(16)"},
        )

        # Should execute without script-not-found error
        assert isinstance(result, str)
        assert "not found" not in result.lower()

    async def test_compute_without_args(self, single_dir_config):
        """Test compute script runs without args."""
        result = await tools.run_skill_script(
            single_dir_config,
            "calculator",
            "scripts/compute.py",
            args={},
        )

        # Should execute without script-not-found error
        assert isinstance(result, str)

    async def test_run_nonexistent_script_error(self, single_dir_config):
        """Test running non-existent script returns error."""
        result = await tools.run_skill_script(
            single_dir_config, "calculator", "nonexistent"
        )

        assert "Error:" in result


class TestAdapterDirectFunctional:
    """Functional tests using SoliplexSkillsAdapter directly."""

    async def test_adapter_skills_property(self, single_dir_config):
        """Test adapter exposes skills dict."""
        toolset = await _get_toolset(single_dir_config)
        adapter = SoliplexSkillsAdapter(toolset)

        assert "calculator" in adapter.skills
        skill = adapter.skills["calculator"]
        assert skill.name == "calculator"

    async def test_adapter_list_skills(self, single_dir_config):
        """Test adapter list_skills method."""
        toolset = await _get_toolset(single_dir_config)
        adapter = SoliplexSkillsAdapter(toolset)

        result = await adapter.list_skills()
        assert "calculator" in result


class TestCachingFunctional:
    """Functional tests for toolset caching."""

    async def test_same_config_returns_cached_toolset(self, single_dir_config):
        """Test same config returns cached toolset."""
        toolset1 = await _get_toolset(single_dir_config)
        toolset2 = await _get_toolset(single_dir_config)

        assert toolset1 is toolset2

    async def test_different_configs_different_toolsets(
        self,
        single_dir_config,
        multi_dir_config,
    ):
        """Test different configs return different toolsets."""
        toolset1 = await _get_toolset(single_dir_config)
        toolset2 = await _get_toolset(multi_dir_config)

        assert toolset1 is not toolset2

    async def test_concurrent_access_same_config(self, single_dir_config):
        """Test concurrent access to same config is safe."""

        async def get_toolset():
            return await _get_toolset(single_dir_config)

        # Run multiple concurrent requests
        results = await asyncio.gather(*[get_toolset() for _ in range(10)])

        # All should return the same cached instance
        first = results[0]
        assert all(r is first for r in results)


class TestPerRoomConfiguration:
    """Test per-room skills configuration scenarios.

    Validates that different rooms can have independent skill configurations,
    simulating how Soliplex would configure different rooms with different
    skill directories.
    """

    async def test_room_a_sees_only_its_skills(self, single_dir_config):
        """Room A with single directory sees only calculator skill."""
        result = await tools.list_skills(single_dir_config)

        assert "calculator" in result
        assert "greeter" not in result  # greeter is in alt directory

    async def test_room_b_sees_all_skills(self, multi_dir_config):
        """Room B with multiple directories sees all skills."""
        result = await tools.list_skills(multi_dir_config)

        assert "calculator" in result
        assert "greeter" in result

    async def test_rooms_operate_independently(
        self,
        single_dir_config,
        multi_dir_config,
    ):
        """Different room configs maintain independent skill sets."""
        # Room A loads calculator
        room_a_result = await tools.load_skill(single_dir_config, "calculator")
        assert "<skill>" in room_a_result

        # Room B loads greeter (not available in Room A)
        room_b_result = await tools.load_skill(multi_dir_config, "greeter")
        assert "<skill>" in room_b_result

        # Room A cannot load greeter
        room_a_greeter = await tools.load_skill(single_dir_config, "greeter")
        assert "Error:" in room_a_greeter
        assert "not found" in room_a_greeter.lower()

    async def test_exclude_tools_per_room(self, test_skills_path):
        """Test exclude_tools configuration per room."""
        # Room with script execution disabled
        restricted_config = SkillsToolConfig(
            tool_name="restricted-room",
            directories=(test_skills_path.resolve(),),
            exclude_tools=frozenset(["run_skill_script"]),
        )

        # Should still list and load skills
        skills = await tools.list_skills(restricted_config)
        assert "calculator" in skills

        skill_content = await tools.load_skill(restricted_config, "calculator")
        assert "<skill>" in skill_content

    async def test_validate_skills_per_room(self, test_skills_path):
        """Test validate_skills can be configured per room."""
        # Room with validation disabled
        no_validate_config = SkillsToolConfig(
            tool_name="no-validate-room",
            directories=(test_skills_path.resolve(),),
            validate_skills=False,
        )

        # Should still work
        skills = await tools.list_skills(no_validate_config)
        assert isinstance(skills, dict)

    async def test_max_depth_per_room(self, test_skills_path):
        """Test max_depth can be configured per room."""
        # Room with limited depth
        shallow_config = SkillsToolConfig(
            tool_name="shallow-room",
            directories=(test_skills_path.resolve(),),
            max_depth=1,
        )

        # Should still discover top-level skills
        skills = await tools.list_skills(shallow_config)
        assert isinstance(skills, dict)
