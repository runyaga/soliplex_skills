"""Unit tests for introspection tools."""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest

from soliplex_skills.introspection.config import DelegateToRoomConfig
from soliplex_skills.introspection.config import DiscoverRoomsConfig
from soliplex_skills.introspection.config import IntrospectionToolConfig
from soliplex_skills.introspection.tools import DelegationResult
from soliplex_skills.introspection.tools import DiscoveryResult
from soliplex_skills.introspection.tools import RoomInfo
from soliplex_skills.introspection.tools import delegate_to_room
from soliplex_skills.introspection.tools import discover_rooms


# Mock room config matching Soliplex's RoomConfig structure
@dataclasses.dataclass
class MockAgentConfig:
    """Mock agent config."""

    model_name: str = "gpt-4"


@dataclasses.dataclass
class MockRoomConfig:
    """Mock room config matching Soliplex patterns."""

    id: str
    name: str
    description: str
    tool_configs: dict[str, Any] = dataclasses.field(default_factory=dict)
    agent_config: MockAgentConfig = dataclasses.field(
        default_factory=MockAgentConfig
    )
    welcome_message: str | None = None
    suggestions: list[str] = dataclasses.field(default_factory=list)


# Mock Agent result
@dataclasses.dataclass
class MockAgentResult:
    """Mock result from agent.run()."""

    data: str


# Mock Agent
class MockAgent:
    """Mock pydantic_ai.Agent for testing."""

    def __init__(self, response: str = "Mock response"):
        self._response = response
        self._should_fail = False
        self._fail_error: Exception | None = None

    def set_response(self, response: str):
        self._response = response

    def set_failure(self, error: Exception):
        self._should_fail = True
        self._fail_error = error

    async def run(self, query: str, deps: Any = None) -> MockAgentResult:
        if self._should_fail:
            raise self._fail_error
        return MockAgentResult(data=self._response)


# Mock Installation class
class MockInstallation:
    """Mock Installation for testing."""

    def __init__(
        self,
        room_configs: dict[str, MockRoomConfig],
        agents: dict[str, MockAgent] | None = None,
    ):
        self._room_configs = room_configs
        self._agents = agents or {}

    async def get_room_configs(
        self,
        *,
        user: dict | None = None,
        the_room_authz: Any = None,
    ) -> dict[str, MockRoomConfig]:
        """Return mock room configs."""
        return self._room_configs

    async def get_room_config(
        self,
        *,
        room_id: str,
        user: dict | None = None,
        the_room_authz: Any = None,
    ) -> MockRoomConfig:
        """Return a single room config."""
        if room_id not in self._room_configs:
            raise KeyError(room_id)
        return self._room_configs[room_id]

    async def get_agent_for_room(
        self,
        *,
        room_id: str,
        user: dict | None = None,
        the_room_authz: Any = None,
    ) -> MockAgent:
        """Return agent for a room."""
        if room_id not in self._room_configs:
            raise KeyError(room_id)
        # Return custom agent if provided, otherwise create default
        if room_id in self._agents:
            return self._agents[room_id]
        return MockAgent(f"Response from {room_id}")


# Mock AgentDependencies
@dataclasses.dataclass
class MockAgentDependencies:
    """Mock agent dependencies."""

    the_installation: MockInstallation
    user: dict | None = None
    tool_configs: dict | None = None
    agui_emitter: Any = None
    state: dict = dataclasses.field(default_factory=dict)


# Mock RunContext
class MockRunContext:
    """Mock pydantic_ai.RunContext."""

    def __init__(self, deps: MockAgentDependencies):
        self.deps = deps


class TestIntrospectionToolConfig:
    """Tests for IntrospectionToolConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = IntrospectionToolConfig()
        assert config.include_tools is True
        assert config.include_model is True
        assert config.exclude_rooms == frozenset()
        assert config.max_delegation_depth == 2

    def test_from_yaml_minimal(self, tmp_path):
        """Test from_yaml with minimal config."""
        config_path = tmp_path / "room_config.yaml"
        config_path.touch()

        config = IntrospectionToolConfig.from_yaml(
            installation_config=None,
            config_path=config_path,
            config={"tool_name": "test.tool"},
        )

        assert config.tool_name == "test.tool"
        assert config.include_tools is True
        assert config.exclude_rooms == frozenset()

    def test_from_yaml_with_exclude_rooms(self, tmp_path):
        """Test from_yaml with exclude_rooms list."""
        config_path = tmp_path / "room_config.yaml"
        config_path.touch()

        config = IntrospectionToolConfig.from_yaml(
            installation_config=None,
            config_path=config_path,
            config={
                "tool_name": "test.tool",
                "exclude_rooms": ["private-room", "admin-room"],
            },
        )

        expected_rooms = frozenset(["private-room", "admin-room"])
        assert config.exclude_rooms == expected_rooms

    def test_from_yaml_all_options(self, tmp_path):
        """Test from_yaml with all options."""
        config_path = tmp_path / "room_config.yaml"
        config_path.touch()

        config = IntrospectionToolConfig.from_yaml(
            installation_config=None,
            config_path=config_path,
            config={
                "tool_name": "test.tool",
                "include_tools": False,
                "include_model": False,
                "exclude_rooms": ["hidden"],
                "max_delegation_depth": 5,
            },
        )

        assert config.include_tools is False
        assert config.include_model is False
        assert config.exclude_rooms == frozenset(["hidden"])
        assert config.max_delegation_depth == 5


class TestDiscoverRoomsConfig:
    """Tests for DiscoverRoomsConfig."""

    def test_default_tool_name(self):
        """Test default tool_name is set."""
        config = DiscoverRoomsConfig()
        assert (
            config.tool_name
            == "soliplex_skills.introspection.tools.discover_rooms"
        )


class TestDiscoverRooms:
    """Tests for discover_rooms tool."""

    @pytest.fixture
    def sample_rooms(self) -> dict[str, MockRoomConfig]:
        """Create sample room configs for testing."""
        return {
            "research": MockRoomConfig(
                id="research",
                name="Research Assistant",
                description="Helps with research tasks",
                tool_configs={
                    "search_documents": {},
                    "summarize": {},
                },
                agent_config=MockAgentConfig(model_name="gpt-4"),
                welcome_message="Welcome to Research!",
                suggestions=["Search for papers", "Summarize document"],
            ),
            "coder": MockRoomConfig(
                id="coder",
                name="Code Assistant",
                description="Helps write code",
                tool_configs={
                    "execute_code": {},
                    "read_file": {},
                    "write_file": {},
                },
                agent_config=MockAgentConfig(model_name="claude-3-opus"),
            ),
            "admin": MockRoomConfig(
                id="admin",
                name="Admin Room",
                description="Administrative functions",
                tool_configs={"manage_users": {}},
                agent_config=MockAgentConfig(model_name="gpt-4"),
            ),
        }

    @pytest.fixture
    def mock_ctx(
        self, sample_rooms: dict[str, MockRoomConfig]
    ) -> MockRunContext:
        """Create mock run context."""
        installation = MockInstallation(sample_rooms)
        deps = MockAgentDependencies(
            the_installation=installation,
            user={"preferred_username": "testuser"},
        )
        return MockRunContext(deps)

    @pytest.mark.asyncio
    async def test_discover_all_rooms(self, mock_ctx: MockRunContext):
        """Test discovering all rooms without filters."""
        result = await discover_rooms(mock_ctx, tool_config=None)

        assert isinstance(result, DiscoveryResult)
        assert result.total_count == 3
        assert result.filtered_count == 3
        assert "research" in result.rooms
        assert "coder" in result.rooms
        assert "admin" in result.rooms
        assert result.note is None

    @pytest.mark.asyncio
    async def test_room_info_structure(self, mock_ctx: MockRunContext):
        """Test that room info contains expected fields."""
        result = await discover_rooms(mock_ctx, tool_config=None)

        research = result.rooms["research"]
        assert isinstance(research, RoomInfo)
        assert research.id == "research"
        assert research.name == "Research Assistant"
        assert research.description == "Helps with research tasks"
        assert research.tools == ["search_documents", "summarize"]
        assert research.model == "gpt-4"
        assert research.welcome_message == "Welcome to Research!"
        expected_suggestions = ["Search for papers", "Summarize document"]
        assert research.suggestions == expected_suggestions

    @pytest.mark.asyncio
    async def test_exclude_rooms_filter(self, mock_ctx: MockRunContext):
        """Test that exclude_rooms config hides rooms."""
        config = IntrospectionToolConfig(
            exclude_rooms=frozenset(["admin"]),
        )

        result = await discover_rooms(mock_ctx, tool_config=config)

        assert result.total_count == 3
        assert result.filtered_count == 2
        assert "admin" not in result.rooms
        assert "research" in result.rooms
        assert "coder" in result.rooms
        assert result.note == "1 room(s) hidden by configuration"

    @pytest.mark.asyncio
    async def test_exclude_multiple_rooms(self, mock_ctx: MockRunContext):
        """Test excluding multiple rooms."""
        config = IntrospectionToolConfig(
            exclude_rooms=frozenset(["admin", "coder"]),
        )

        result = await discover_rooms(mock_ctx, tool_config=config)

        assert result.total_count == 3
        assert result.filtered_count == 1
        assert "admin" not in result.rooms
        assert "coder" not in result.rooms
        assert "research" in result.rooms
        assert result.note == "2 room(s) hidden by configuration"

    @pytest.mark.asyncio
    async def test_include_tools_false(self, mock_ctx: MockRunContext):
        """Test that include_tools=False omits tool lists."""
        config = IntrospectionToolConfig(include_tools=False)

        result = await discover_rooms(mock_ctx, tool_config=config)

        research = result.rooms["research"]
        assert research.tools is None

    @pytest.mark.asyncio
    async def test_include_model_false(self, mock_ctx: MockRunContext):
        """Test that include_model=False omits model info."""
        config = IntrospectionToolConfig(include_model=False)

        result = await discover_rooms(mock_ctx, tool_config=config)

        research = result.rooms["research"]
        assert research.model is None

    @pytest.mark.asyncio
    async def test_empty_installation(self):
        """Test discovery with no rooms configured."""
        installation = MockInstallation({})
        deps = MockAgentDependencies(the_installation=installation)
        ctx = MockRunContext(deps)

        result = await discover_rooms(ctx, tool_config=None)

        assert result.total_count == 0
        assert result.filtered_count == 0
        assert result.rooms == {}
        assert result.note is None

    @pytest.mark.asyncio
    async def test_room_without_optional_fields(self):
        """Test room with minimal fields."""
        rooms = {
            "minimal": MockRoomConfig(
                id="minimal",
                name="Minimal Room",
                description="No extras",
                tool_configs={},
            ),
        }
        installation = MockInstallation(rooms)
        deps = MockAgentDependencies(the_installation=installation)
        ctx = MockRunContext(deps)

        result = await discover_rooms(ctx, tool_config=None)

        minimal = result.rooms["minimal"]
        assert minimal.id == "minimal"
        assert minimal.tools == []
        assert minimal.model == "gpt-4"  # MockAgentConfig default
        assert minimal.welcome_message is None
        # suggestions defaults to empty list in MockRoomConfig
        assert minimal.suggestions == []


class TestRoomInfoModel:
    """Tests for RoomInfo Pydantic model."""

    def test_minimal_room_info(self):
        """Test creating RoomInfo with minimal fields."""
        info = RoomInfo(
            id="test",
            name="Test Room",
            description="A test",
        )
        assert info.id == "test"
        assert info.tools is None
        assert info.model is None

    def test_full_room_info(self):
        """Test creating RoomInfo with all fields."""
        info = RoomInfo(
            id="test",
            name="Test Room",
            description="A test",
            tools=["tool1", "tool2"],
            model="gpt-4",
            welcome_message="Hello",
            suggestions=["Try this"],
        )
        assert info.tools == ["tool1", "tool2"]
        assert info.model == "gpt-4"

    def test_room_info_serialization(self):
        """Test that RoomInfo serializes to dict."""
        info = RoomInfo(
            id="test",
            name="Test Room",
            description="A test",
            tools=["tool1"],
        )
        data = info.model_dump()
        assert data["id"] == "test"
        assert data["tools"] == ["tool1"]


class TestDiscoveryResultModel:
    """Tests for DiscoveryResult Pydantic model."""

    def test_discovery_result_serialization(self):
        """Test that DiscoveryResult serializes correctly."""
        result = DiscoveryResult(
            rooms={
                "test": RoomInfo(
                    id="test",
                    name="Test",
                    description="Test room",
                )
            },
            total_count=1,
            filtered_count=1,
            note=None,
        )
        data = result.model_dump()
        assert data["total_count"] == 1
        assert "test" in data["rooms"]


class TestDelegateToRoomConfig:
    """Tests for DelegateToRoomConfig."""

    def test_default_tool_name(self):
        """Test default tool_name is set."""
        config = DelegateToRoomConfig()
        assert (
            config.tool_name
            == "soliplex_skills.introspection.tools.delegate_to_room"
        )


class TestDelegateToRoom:
    """Tests for delegate_to_room tool.

    NOTE: delegate_to_room is SYNCHRONOUS - no streaming support.
    The calling agent blocks until the delegated agent completes.
    """

    @pytest.fixture
    def sample_rooms(self) -> dict[str, MockRoomConfig]:
        """Create sample room configs for testing."""
        return {
            "research": MockRoomConfig(
                id="research",
                name="Research Assistant",
                description="Helps with research tasks",
                tool_configs={"search_documents": {}},
            ),
            "coder": MockRoomConfig(
                id="coder",
                name="Code Assistant",
                description="Helps write code",
                tool_configs={"execute_code": {}},
            ),
            "admin": MockRoomConfig(
                id="admin",
                name="Admin Room",
                description="Administrative functions",
                tool_configs={"manage_users": {}},
            ),
        }

    @pytest.fixture
    def mock_installation(
        self, sample_rooms: dict[str, MockRoomConfig]
    ) -> MockInstallation:
        """Create mock installation with custom agents."""
        agents = {
            "research": MockAgent("Research results: quantum computing..."),
            "coder": MockAgent("```python\ndef hello(): pass\n```"),
        }
        return MockInstallation(sample_rooms, agents)

    @pytest.fixture
    def mock_ctx(self, mock_installation: MockInstallation) -> MockRunContext:
        """Create mock run context."""
        deps = MockAgentDependencies(
            the_installation=mock_installation,
            user={"preferred_username": "testuser"},
            state={},
        )
        return MockRunContext(deps)

    @pytest.mark.asyncio
    async def test_successful_delegation(self, mock_ctx: MockRunContext):
        """Test successful delegation to another room."""
        result = await delegate_to_room(
            mock_ctx,
            room_id="research",
            query="Tell me about quantum computing",
        )

        assert isinstance(result, DelegationResult)
        assert result.success is True
        assert result.room_id == "research"
        assert result.room_name == "Research Assistant"
        assert result.query == "Tell me about quantum computing"
        assert "quantum computing" in result.response
        assert result.error is None
        assert result.delegation_depth == 1

    @pytest.mark.asyncio
    async def test_delegation_to_nonexistent_room(
        self, mock_ctx: MockRunContext
    ):
        """Test delegation to a room that doesn't exist."""
        result = await delegate_to_room(
            mock_ctx,
            room_id="nonexistent",
            query="Hello",
        )

        assert result.success is False
        assert result.room_id == "nonexistent"
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_delegation_to_excluded_room(self, mock_ctx: MockRunContext):
        """Test delegation to a room that is excluded."""
        config = IntrospectionToolConfig(
            exclude_rooms=frozenset(["admin"]),
        )

        result = await delegate_to_room(
            mock_ctx,
            room_id="admin",
            query="Hello",
            tool_config=config,
        )

        assert result.success is False
        assert "not available for delegation" in result.error

    @pytest.mark.asyncio
    async def test_max_delegation_depth_exceeded(
        self, mock_installation: MockInstallation
    ):
        """Test that max delegation depth is enforced."""
        # Set current depth to 2
        deps = MockAgentDependencies(
            the_installation=mock_installation,
            user={"preferred_username": "testuser"},
            state={"_delegation_depth": 2},
        )
        ctx = MockRunContext(deps)

        config = IntrospectionToolConfig(max_delegation_depth=2)

        result = await delegate_to_room(
            ctx,
            room_id="research",
            query="Hello",
            tool_config=config,
        )

        assert result.success is False
        assert "Max delegation depth" in result.error

    @pytest.mark.asyncio
    async def test_custom_max_delegation_depth(
        self, mock_installation: MockInstallation
    ):
        """Test custom max_delegation_depth config."""
        deps = MockAgentDependencies(
            the_installation=mock_installation,
            state={"_delegation_depth": 3},
        )
        ctx = MockRunContext(deps)

        # Allow depth up to 5
        config = IntrospectionToolConfig(max_delegation_depth=5)

        result = await delegate_to_room(
            ctx,
            room_id="research",
            query="Hello",
            tool_config=config,
        )

        # Should succeed because 3 < 5
        assert result.success is True

    @pytest.mark.asyncio
    async def test_delegation_increments_depth(
        self, mock_ctx: MockRunContext
    ):
        """Test that delegation_depth is incremented in result."""
        result = await delegate_to_room(
            mock_ctx,
            room_id="research",
            query="Hello",
        )

        # Starting depth was 0, so result should be 1
        assert result.delegation_depth == 1

    @pytest.mark.asyncio
    async def test_delegation_agent_failure(
        self, sample_rooms: dict[str, MockRoomConfig]
    ):
        """Test handling of agent execution failure."""
        # Create agent that will fail
        failing_agent = MockAgent()
        failing_agent.set_failure(RuntimeError("LLM API error"))

        installation = MockInstallation(
            sample_rooms,
            agents={"research": failing_agent},
        )
        deps = MockAgentDependencies(
            the_installation=installation,
            state={},
        )
        ctx = MockRunContext(deps)

        result = await delegate_to_room(
            ctx,
            room_id="research",
            query="Hello",
        )

        assert result.success is False
        assert "Delegation failed" in result.error
        assert "LLM API error" in result.error

    @pytest.mark.asyncio
    async def test_delegation_emits_step_events(
        self, sample_rooms: dict[str, MockRoomConfig]
    ):
        """Test that delegation emits start_step/finish_step on emitter."""
        from unittest.mock import Mock

        # Create mock emitter
        mock_emitter = Mock()

        installation = MockInstallation(
            sample_rooms,
            agents={"research": MockAgent("Result")},
        )
        deps = MockAgentDependencies(
            the_installation=installation,
            state={},
            agui_emitter=mock_emitter,
        )
        ctx = MockRunContext(deps)

        result = await delegate_to_room(
            ctx,
            room_id="research",
            query="Hello",
        )

        assert result.success is True
        # Verify emitter was called
        mock_emitter.start_step.assert_called_once_with("delegate:research")
        mock_emitter.finish_step.assert_called_once_with("delegate:research")

    @pytest.mark.asyncio
    async def test_delegation_emits_finish_on_failure(
        self, sample_rooms: dict[str, MockRoomConfig]
    ):
        """Test that finish_step is called even when delegation fails."""
        from unittest.mock import Mock

        mock_emitter = Mock()

        failing_agent = MockAgent()
        failing_agent.set_failure(RuntimeError("API error"))

        installation = MockInstallation(
            sample_rooms,
            agents={"research": failing_agent},
        )
        deps = MockAgentDependencies(
            the_installation=installation,
            state={},
            agui_emitter=mock_emitter,
        )
        ctx = MockRunContext(deps)

        result = await delegate_to_room(
            ctx,
            room_id="research",
            query="Hello",
        )

        assert result.success is False
        # Both should still be called (finally block)
        mock_emitter.start_step.assert_called_once()
        mock_emitter.finish_step.assert_called_once()

    @pytest.mark.asyncio
    async def test_delegation_works_without_emitter(
        self, mock_ctx: MockRunContext
    ):
        """Test that delegation works when emitter is None."""
        # mock_ctx has agui_emitter=None by default
        assert mock_ctx.deps.agui_emitter is None

        result = await delegate_to_room(
            mock_ctx,
            room_id="research",
            query="Hello",
        )

        # Should work fine without emitter
        assert result.success is True


class TestDelegationResultModel:
    """Tests for DelegationResult Pydantic model."""

    def test_successful_result(self):
        """Test creating successful delegation result."""
        result = DelegationResult(
            room_id="test",
            room_name="Test Room",
            query="Hello",
            response="Hi there!",
            success=True,
        )
        assert result.error is None
        assert result.delegation_depth == 1

    def test_failed_result(self):
        """Test creating failed delegation result."""
        result = DelegationResult(
            room_id="test",
            room_name="Test Room",
            query="Hello",
            response="",
            success=False,
            error="Room not found",
        )
        assert result.success is False
        assert result.error == "Room not found"

    def test_result_serialization(self):
        """Test that DelegationResult serializes correctly."""
        result = DelegationResult(
            room_id="test",
            room_name="Test",
            query="q",
            response="r",
            success=True,
        )
        data = result.model_dump()
        assert data["room_id"] == "test"
        assert data["success"] is True
