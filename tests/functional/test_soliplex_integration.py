"""Integration tests for Soliplex configuration loading.

These tests verify SkillsToolConfig integrates correctly with Soliplex's
configuration system. Tests are skipped if soliplex is not installed.
"""

from __future__ import annotations

import pathlib

import pytest

# Skip all tests in this module if soliplex is not installed
soliplex = pytest.importorskip("soliplex")

from soliplex_skills.config import ListSkillsConfig  # noqa: E402
from soliplex_skills.config import LoadSkillConfig  # noqa: E402
from soliplex_skills.config import ReadSkillResourceConfig  # noqa: E402
from soliplex_skills.config import RunSkillScriptConfig  # noqa: E402
from soliplex_skills.config import SkillsToolConfig  # noqa: E402

# Path to example directory
EXAMPLE_DIR = pathlib.Path(__file__).parent.parent.parent / "example"
EXAMPLE_ROOM_CONFIG = (
    EXAMPLE_DIR / "rooms" / "research-assistant" / "room_config.yaml"
)


class TestToolConfigInheritance:
    """Test SkillsToolConfig inherits from soliplex.config.ToolConfig."""

    def test_skills_tool_config_is_tool_config(self):
        """SkillsToolConfig should inherit from ToolConfig."""
        from soliplex.config import ToolConfig

        assert issubclass(SkillsToolConfig, ToolConfig)

    def test_list_skills_config_is_tool_config(self):
        """ListSkillsConfig should inherit from ToolConfig."""
        from soliplex.config import ToolConfig

        assert issubclass(ListSkillsConfig, ToolConfig)
        assert issubclass(ListSkillsConfig, SkillsToolConfig)

    def test_load_skill_config_is_tool_config(self):
        """LoadSkillConfig should inherit from ToolConfig."""
        from soliplex.config import ToolConfig

        assert issubclass(LoadSkillConfig, ToolConfig)

    def test_read_skill_resource_config_is_tool_config(self):
        """ReadSkillResourceConfig should inherit from ToolConfig."""
        from soliplex.config import ToolConfig

        assert issubclass(ReadSkillResourceConfig, ToolConfig)

    def test_run_skill_script_config_is_tool_config(self):
        """RunSkillScriptConfig should inherit from ToolConfig."""
        from soliplex.config import ToolConfig

        assert issubclass(RunSkillScriptConfig, ToolConfig)


class TestFromYamlClassmethod:
    """Test SkillsToolConfig.from_yaml() classmethod."""

    def test_from_yaml_creates_config(self):
        """from_yaml should create SkillsToolConfig with values from dict."""
        config_dict = {
            "tool_name": "soliplex_skills.tools.list_skills",
            "directories": ["./skills", "../shared_skills"],
            "validate": True,  # YAML key matches env var style, not field name
            "max_depth": 5,
        }
        config_path = pathlib.Path("/fake/room/room_config.yaml")

        config = SkillsToolConfig.from_yaml(
            installation_config=None,
            config_path=config_path,
            config=config_dict,
        )

        assert config.tool_name == "soliplex_skills.tools.list_skills"
        assert config.validate_skills is True
        assert config.max_depth == 5
        # Directories should be resolved relative to config_path
        assert len(config.directories) == 2

    def test_from_yaml_resolves_relative_paths(self):
        """from_yaml should resolve relative paths against config_path."""
        config_dict = {
            "tool_name": "test",
            "directories": ["../../skills"],
        }
        config_path = pathlib.Path("/app/rooms/demo/room_config.yaml")

        config = SkillsToolConfig.from_yaml(
            installation_config=None,
            config_path=config_path,
            config=config_dict,
        )

        # ../../skills from /app/rooms/demo/ -> /app/skills
        expected = pathlib.Path("/app/skills").resolve()
        assert config.directories[0] == expected

    def test_from_yaml_handles_yaml_list_format(self):
        """from_yaml should handle YAML list format for directories."""
        config_dict = {
            "tool_name": "test",
            "directories": [
                "./skills",
                "/absolute/path/skills",
            ],
        }
        config_path = pathlib.Path("/app/room_config.yaml")

        config = SkillsToolConfig.from_yaml(
            installation_config=None,
            config_path=config_path,
            config=config_dict,
        )

        assert len(config.directories) == 2
        # Relative path should be resolved
        assert config.directories[0] == pathlib.Path("/app/skills").resolve()
        # Absolute path stays as-is
        assert config.directories[1] == pathlib.Path("/absolute/path/skills")

    def test_from_yaml_handles_exclude_tools_list(self):
        """from_yaml should handle YAML list format for exclude_tools."""
        config_dict = {
            "tool_name": "test",
            "directories": ["./skills"],
            "exclude_tools": ["run_skill_script"],
        }
        config_path = pathlib.Path("/app/room_config.yaml")

        config = SkillsToolConfig.from_yaml(
            installation_config=None,
            config_path=config_path,
            config=config_dict,
        )

        assert "run_skill_script" in config.exclude_tools

    def test_from_yaml_stores_installation_config(self):
        """from_yaml should store installation_config reference."""
        mock_installation = {"some": "config"}
        config_dict = {"tool_name": "test", "directories": ["./skills"]}
        config_path = pathlib.Path("/app/room_config.yaml")

        config = SkillsToolConfig.from_yaml(
            installation_config=mock_installation,
            config_path=config_path,
            config=config_dict,
        )

        assert config._installation_config == mock_installation

    def test_from_yaml_stores_config_path(self):
        """from_yaml should store config_path reference."""
        config_dict = {"tool_name": "test", "directories": ["./skills"]}
        config_path = pathlib.Path("/app/room_config.yaml")

        config = SkillsToolConfig.from_yaml(
            installation_config=None,
            config_path=config_path,
            config=config_dict,
        )

        assert config._config_path == config_path


class TestPerToolConfigClasses:
    """Test per-tool config classes have correct default tool_name."""

    def test_list_skills_config_tool_name(self):
        """ListSkillsConfig should have correct default tool_name."""
        config = ListSkillsConfig(directories=())
        assert config.tool_name == "soliplex_skills.tools.list_skills"

    def test_load_skill_config_tool_name(self):
        """LoadSkillConfig should have correct default tool_name."""
        config = LoadSkillConfig(directories=())
        assert config.tool_name == "soliplex_skills.tools.load_skill"

    def test_read_skill_resource_config_tool_name(self):
        """ReadSkillResourceConfig should have correct default tool_name."""
        config = ReadSkillResourceConfig(directories=())
        assert config.tool_name == "soliplex_skills.tools.read_skill_resource"

    def test_run_skill_script_config_tool_name(self):
        """RunSkillScriptConfig should have correct default tool_name."""
        config = RunSkillScriptConfig(directories=())
        assert config.tool_name == "soliplex_skills.tools.run_skill_script"


class TestExampleRoomConfigLoading:
    """Test loading example room configurations."""

    @pytest.mark.skipif(
        not EXAMPLE_ROOM_CONFIG.exists(),
        reason="Example room config not found",
    )
    def test_example_room_config_exists(self):
        """Example room_config.yaml should exist."""
        assert EXAMPLE_ROOM_CONFIG.exists()

    @pytest.mark.skipif(
        not EXAMPLE_ROOM_CONFIG.exists(),
        reason="Example room config not found",
    )
    def test_can_parse_example_room_yaml(self):
        """Should be able to parse example room_config.yaml."""
        import yaml

        with open(EXAMPLE_ROOM_CONFIG) as f:
            data = yaml.safe_load(f)

        assert "id" in data
        assert "tools" in data
        # Should have skills tools configured
        tool_names = [t.get("tool_name", "") for t in data["tools"]]
        assert any("soliplex_skills" in tn for tn in tool_names)

    @pytest.mark.skipif(
        not EXAMPLE_ROOM_CONFIG.exists(),
        reason="Example room config not found",
    )
    def test_directories_use_yaml_list_format(self):
        """Example configs should use YAML list format for directories."""
        import yaml

        with open(EXAMPLE_ROOM_CONFIG) as f:
            data = yaml.safe_load(f)

        # Find first soliplex_skills tool
        for tool in data["tools"]:
            tool_name = tool.get("tool_name", "")
            if "soliplex_skills" in tool_name:
                directories = tool.get("directories")
                # Should be a list, not a string
                assert isinstance(directories, list), (
                    f"directories should be YAML list, got {type(directories)}"
                )
                break
