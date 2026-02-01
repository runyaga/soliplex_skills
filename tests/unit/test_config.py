"""Tests for soliplex_skills.config module."""

from __future__ import annotations

import pathlib

from soliplex_skills.config import ListSkillsConfig
from soliplex_skills.config import LoadSkillConfig
from soliplex_skills.config import ReadSkillResourceConfig
from soliplex_skills.config import RunSkillScriptConfig
from soliplex_skills.config import SkillsToolConfig
from soliplex_skills.config import SkillsToolSettings
from soliplex_skills.config import _parse_directories_input
from soliplex_skills.config import _parse_exclude_tools_input


class TestSkillsToolSettings:
    """Test SkillsToolSettings environment configuration."""

    def test_default_values(self):
        """Test default settings values."""
        settings = SkillsToolSettings()
        assert settings.directories == "./skills"
        assert settings.validate is True
        assert settings.max_depth == 3
        assert settings.exclude_tools == ""

    def test_env_var_override(self, monkeypatch):
        """Test environment variable overrides."""
        monkeypatch.setenv("SOLIPLEX_SKILLS_DIRECTORIES", "/custom/skills")
        monkeypatch.setenv("SOLIPLEX_SKILLS_VALIDATE", "false")
        monkeypatch.setenv("SOLIPLEX_SKILLS_MAX_DEPTH", "5")
        monkeypatch.setenv("SOLIPLEX_SKILLS_EXCLUDE_TOOLS", "run_skill_script")

        settings = SkillsToolSettings()
        assert settings.directories == "/custom/skills"
        assert settings.validate is False
        assert settings.max_depth == 5
        assert settings.exclude_tools == "run_skill_script"

    def test_parse_directories(self):
        """Test parse_directories helper method."""
        settings = SkillsToolSettings()
        settings.directories = "./skills, ./other"
        paths = settings.parse_directories()
        assert len(paths) == 2
        assert all(isinstance(p, pathlib.Path) for p in paths)

    def test_parse_exclude_tools(self):
        """Test parse_exclude_tools helper method."""
        settings = SkillsToolSettings()
        settings.exclude_tools = "tool_a, tool_b"
        excluded = settings.parse_exclude_tools()
        assert excluded == {"tool_a", "tool_b"}


class TestParseHelpers:
    """Test the parsing helper functions."""

    def test_parse_directories_from_string(self, temp_dir):
        """Test parsing comma-separated string."""
        result = _parse_directories_input("./a, ./b", temp_dir / "config.yaml")
        assert len(result) == 2
        assert isinstance(result, tuple)
        assert all(isinstance(p, pathlib.Path) for p in result)

    def test_parse_directories_from_list(self, temp_dir):
        """Test parsing YAML list."""
        result = _parse_directories_input(
            ["./a", "./b"], temp_dir / "config.yaml"
        )
        assert len(result) == 2
        assert isinstance(result, tuple)

    def test_parse_directories_from_path_list(self, temp_dir):
        """Test parsing list of Path objects."""
        input_paths = [pathlib.Path("./a"), pathlib.Path("./b")]
        cfg_path = temp_dir / "config.yaml"
        result = _parse_directories_input(input_paths, cfg_path)
        assert len(result) == 2
        assert all(p.is_absolute() for p in result)

    def test_parse_directories_none(self):
        """Test parsing None returns empty tuple."""
        result = _parse_directories_input(None, None)
        assert result == ()

    def test_parse_exclude_tools_from_string(self):
        """Test parsing comma-separated string."""
        result = _parse_exclude_tools_input("tool_a, tool_b")
        assert result == frozenset({"tool_a", "tool_b"})

    def test_parse_exclude_tools_from_list(self):
        """Test parsing YAML list."""
        result = _parse_exclude_tools_input(["tool_a", "tool_b"])
        assert result == frozenset({"tool_a", "tool_b"})

    def test_parse_exclude_tools_from_set(self):
        """Test parsing set."""
        result = _parse_exclude_tools_input({"tool_a", "tool_b"})
        assert result == frozenset({"tool_a", "tool_b"})

    def test_parse_exclude_tools_none(self):
        """Test parsing None returns empty frozenset."""
        result = _parse_exclude_tools_input(None)
        assert result == frozenset()


class TestSkillsToolConfig:
    """Test SkillsToolConfig dataclass."""

    def test_default_creation(self):
        """Test creating config with defaults."""
        config = SkillsToolConfig(tool_name="test.tool")
        assert config.tool_name == "test.tool"
        # directories should be a tuple of Path objects
        assert isinstance(config.directories, tuple)

    def test_directories_is_tuple_of_paths(self, temp_dir):
        """Test directories field is tuple of Path objects."""
        config = SkillsToolConfig(
            tool_name="test",
            directories=(temp_dir / "skills1", temp_dir / "skills2"),
        )
        assert isinstance(config.directories, tuple)
        assert len(config.directories) == 2
        assert all(isinstance(p, pathlib.Path) for p in config.directories)

    def test_directories_empty_tuple(self):
        """Test empty directories tuple."""
        config = SkillsToolConfig(tool_name="test", directories=())
        assert config.directories == ()

    def test_exclude_tools_is_frozenset(self):
        """Test exclude_tools field is frozenset."""
        excluded = frozenset({"run_skill_script", "read_skill_resource"})
        config = SkillsToolConfig(
            tool_name="test",
            exclude_tools=excluded,
        )
        assert isinstance(config.exclude_tools, frozenset)
        assert config.exclude_tools == excluded

    def test_exclude_tools_empty_frozenset(self):
        """Test empty exclude_tools frozenset."""
        config = SkillsToolConfig(tool_name="test", exclude_tools=frozenset())
        assert config.exclude_tools == frozenset()

    def test_config_hashable_for_cache(self, temp_dir):
        """Test config fields are hashable (for cache keys)."""
        config = SkillsToolConfig(
            tool_name="test",
            directories=(temp_dir / "skills",),
            exclude_tools=frozenset({"tool_a"}),
        )
        # This should not raise - tuple and frozenset are hashable
        cache_key = (
            config.directories,
            config.validate_skills,
            config.max_depth,
            config.exclude_tools,
        )
        assert hash(cache_key) is not None


class TestSkillsToolConfigFromYaml:
    """Test SkillsToolConfig.from_yaml path resolution."""

    def test_relative_path_resolution(self, temp_dir):
        """Test relative paths resolve against config_path."""
        config_path = temp_dir / "rooms" / "myroom" / "room_config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.touch()

        config = SkillsToolConfig.from_yaml(
            installation_config=None,
            config_path=config_path,
            config={
                "tool_name": "soliplex_skills.tools.list_skills",
                "directories": "./skills",
            },
        )

        # directories is now a tuple of Path objects
        assert len(config.directories) == 1
        assert config.directories[0].is_absolute()
        assert "rooms/myroom/skills" in str(config.directories[0])

    def test_absolute_path_preserved(self, temp_dir):
        """Test absolute paths are preserved."""
        config_path = temp_dir / "room_config.yaml"
        absolute_skills = temp_dir / "global_skills"

        config = SkillsToolConfig.from_yaml(
            installation_config=None,
            config_path=config_path,
            config={
                "tool_name": "test",
                "directories": str(absolute_skills),
            },
        )

        assert len(config.directories) == 1
        assert config.directories[0] == absolute_skills.resolve()

    def test_multiple_directories_resolved(self, temp_dir):
        """Test multiple directories all get resolved."""
        config_path = temp_dir / "room" / "room_config.yaml"
        config_path.parent.mkdir(parents=True)

        config = SkillsToolConfig.from_yaml(
            installation_config=None,
            config_path=config_path,
            config={
                "tool_name": "test",
                "directories": "./skills, ../shared_skills",
            },
        )

        assert len(config.directories) == 2
        assert all(p.is_absolute() for p in config.directories)

    def test_yaml_list_format(self, temp_dir):
        """Test YAML list format for directories."""
        config_path = temp_dir / "room_config.yaml"

        config = SkillsToolConfig.from_yaml(
            installation_config=None,
            config_path=config_path,
            config={
                "tool_name": "test",
                "directories": ["./skills", "./other_skills"],
            },
        )

        assert len(config.directories) == 2
        assert all(p.is_absolute() for p in config.directories)

    def test_yaml_list_exclude_tools(self, temp_dir):
        """Test YAML list format for exclude_tools."""
        config_path = temp_dir / "room_config.yaml"

        config = SkillsToolConfig.from_yaml(
            installation_config=None,
            config_path=config_path,
            config={
                "tool_name": "test",
                "exclude_tools": ["run_skill_script", "load_skill"],
            },
        )

        assert config.exclude_tools == frozenset(
            {"run_skill_script", "load_skill"}
        )

    def test_yaml_overrides_env_defaults(self, temp_dir, monkeypatch):
        """Test YAML config overrides environment defaults."""
        monkeypatch.setenv("SOLIPLEX_SKILLS_VALIDATE", "false")
        monkeypatch.setenv("SOLIPLEX_SKILLS_MAX_DEPTH", "10")

        config_path = temp_dir / "room_config.yaml"

        config = SkillsToolConfig.from_yaml(
            installation_config=None,
            config_path=config_path,
            config={
                "tool_name": "test",
                "validate": True,  # Override env
                "max_depth": 2,  # Override env
            },
        )

        assert config.validate_skills is True
        assert config.max_depth == 2


class TestPerToolConfigs:
    """Test per-tool config subclasses."""

    def test_list_skills_config_tool_name(self):
        """Test ListSkillsConfig has correct tool_name."""
        config = ListSkillsConfig()
        assert config.tool_name == "soliplex_skills.tools.list_skills"

    def test_load_skill_config_tool_name(self):
        """Test LoadSkillConfig has correct tool_name."""
        config = LoadSkillConfig()
        assert config.tool_name == "soliplex_skills.tools.load_skill"

    def test_read_skill_resource_config_tool_name(self):
        """Test ReadSkillResourceConfig has correct tool_name."""
        config = ReadSkillResourceConfig()
        assert config.tool_name == "soliplex_skills.tools.read_skill_resource"

    def test_run_skill_script_config_tool_name(self):
        """Test RunSkillScriptConfig has correct tool_name."""
        config = RunSkillScriptConfig()
        assert config.tool_name == "soliplex_skills.tools.run_skill_script"

    def test_subclasses_inherit_from_yaml(self, temp_dir):
        """Test subclasses can use from_yaml."""
        config_path = temp_dir / "room_config.yaml"

        config = ListSkillsConfig.from_yaml(
            installation_config=None,
            config_path=config_path,
            config={
                "tool_name": "soliplex_skills.tools.list_skills",
                "directories": "./my_skills",
            },
        )

        assert isinstance(config, SkillsToolConfig)
        assert len(config.directories) == 1
