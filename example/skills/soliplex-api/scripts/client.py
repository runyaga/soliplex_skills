"""Soliplex client module with dual client support.

Provides two client implementations:
- HTTPClient: Uses HTTP calls to running Soliplex server
- DirectClient: Uses Soliplex Python API directly (discovery only)

Usage:
    from client import create_client, HTTPClient, DirectClient

    # Auto-detect best client
    client = create_client()

    # Or explicitly choose
    client = HTTPClient("http://127.0.0.1:8002")
    client = DirectClient("/path/to/installation.yaml")
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from typing import runtime_checkable


@dataclass
class RoomInfo:
    """Room information."""

    id: str
    name: str
    description: str | None = None
    model: str | None = None
    welcome_message: str | None = None
    suggestions: list[str] | None = None


@dataclass
class SkillInfo:
    """Skill information."""

    name: str
    description: str
    path: str | None = None
    scripts: list[str] | None = None
    resources: list[str] | None = None


@dataclass
class ToolConfigInfo:
    """Tool configuration information."""

    name: str
    tool_type: str
    tool_name: str | None = None
    directories: list[str] | None = None


@dataclass
class AgentConfigInfo:
    """Agent configuration information."""

    id: str
    model_name: str
    retries: int = 3


@dataclass
class InstallationInfo:
    """Installation information."""

    id: str
    room_count: int
    skill_count: int
    agent_configs: list[str]
    environment: dict[str, str | None]


@runtime_checkable
class SoliplexClient(Protocol):
    """Protocol for Soliplex client implementations."""

    def list_rooms(self) -> dict[str, RoomInfo]:
        """List all available rooms.

        Returns:
            Dictionary mapping room IDs to RoomInfo objects.
        """
        ...

    def get_room(self, room_id: str) -> RoomInfo:
        """Get detailed information about a room.

        Args:
            room_id: The room identifier.

        Returns:
            RoomInfo for the specified room.

        Raises:
            KeyError: If room not found.
        """
        ...


class HTTPClient:
    """HTTP client for Soliplex API.

    Uses HTTP calls to a running Soliplex server.
    Supports all operations including ask().
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8002"):
        """Initialize HTTP client.

        Args:
            base_url: Soliplex server URL.
        """
        self.base_url = base_url.rstrip("/")
        self._httpx = None

    def _get_httpx(self):
        """Lazy load httpx."""
        if self._httpx is None:
            try:
                import httpx

                self._httpx = httpx
            except ImportError as e:
                msg = (
                    "httpx required for HTTPClient. "
                    "Install with: pip install httpx"
                )
                raise ImportError(msg) from e
        return self._httpx

    def list_rooms(self) -> dict[str, RoomInfo]:
        """List all available rooms."""
        httpx = self._get_httpx()
        resp = httpx.get(f"{self.base_url}/api/v1/rooms", timeout=10)
        resp.raise_for_status()
        data = resp.json()

        rooms = {}
        for room_id, room_data in data.items():
            rooms[room_id] = RoomInfo(
                id=room_id,
                name=room_data.get("name", room_id),
                description=room_data.get("description"),
                model=room_data.get("model"),
                welcome_message=room_data.get("welcome_message"),
                suggestions=room_data.get("suggestions"),
            )
        return rooms

    def get_room(self, room_id: str) -> RoomInfo:
        """Get detailed room information."""
        httpx = self._get_httpx()
        resp = httpx.get(f"{self.base_url}/api/v1/rooms/{room_id}", timeout=10)
        resp.raise_for_status()
        data = resp.json()

        return RoomInfo(
            id=room_id,
            name=data.get("name", room_id),
            description=data.get("description"),
            model=data.get("model"),
            welcome_message=data.get("welcome_message"),
            suggestions=data.get("suggestions"),
        )

    def ask(self, room_id: str, query: str, timeout: int = 120) -> str:
        """Send a query to a room and get the response.

        Uses AG-UI two-step protocol:
        1. Create thread and run
        2. Execute run with SSE streaming

        Args:
            room_id: Target room ID.
            query: User query to send.
            timeout: Request timeout in seconds.

        Returns:
            Complete response text from the room.
        """
        httpx = self._get_httpx()

        # Step 1: Create thread and run
        thread_id = f"client-{uuid.uuid4().hex[:8]}"
        create_payload = {
            "thread_id": thread_id,
            "messages": [{"id": "msg-1", "role": "user", "content": query}],
        }

        create_resp = httpx.post(
            f"{self.base_url}/api/v1/rooms/{room_id}/agui",
            json=create_payload,
            timeout=10,
        )
        create_resp.raise_for_status()
        create_data = create_resp.json()

        thread_id = create_data["thread_id"]
        run_id = next(iter(create_data["runs"].keys()))

        # Step 2: Execute run with SSE streaming
        exec_payload = {
            "threadId": thread_id,
            "runId": run_id,
            "state": {},
            "messages": [{"id": "msg-1", "role": "user", "content": query}],
            "tools": [],
            "context": [],
            "forwardedProps": {},
        }

        response_text = []
        with httpx.stream(
            "POST",
            f"{self.base_url}/api/v1/rooms/{room_id}/agui/{thread_id}/{run_id}",
            json=exec_payload,
            headers={"Accept": "text/event-stream"},
            timeout=timeout,
        ) as response:
            for line in response.iter_lines():
                if line and line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        if event.get("type") == "TEXT_MESSAGE_CONTENT":
                            delta = event.get("delta", "")
                            response_text.append(delta)
                    except json.JSONDecodeError:
                        pass

        return "".join(response_text)


class DirectClient:
    """Direct client using Soliplex Python API.

    Reads configuration files directly without requiring a running server.
    Useful for discovery and introspection.

    Note: ask() is not supported - use HTTPClient for that.
    """

    def __init__(self, installation_path: str | Path):
        """Initialize direct client.

        Args:
            installation_path: Path to installation.yaml file.
        """
        self.installation_path = Path(installation_path)
        self._config = None

    def _load_config(self):
        """Lazy load Soliplex configuration."""
        if self._config is not None:
            return self._config

        try:
            from soliplex.config import load_installation
        except ImportError as e:
            msg = (
                "soliplex required for DirectClient. "
                "Install with: pip install soliplex"
            )
            raise ImportError(msg) from e

        self._config = load_installation(self.installation_path)
        self._config.reload_configurations()
        return self._config

    def list_rooms(self) -> dict[str, RoomInfo]:
        """List all available rooms from configuration."""
        config = self._load_config()

        rooms = {}
        for room_id, room_config in config.room_configs.items():
            rooms[room_id] = RoomInfo(
                id=room_id,
                name=getattr(room_config, "name", room_id),
                description=getattr(room_config, "description", None),
                model=getattr(room_config, "model", None),
                welcome_message=getattr(room_config, "welcome_message", None),
                suggestions=getattr(room_config, "suggestions", None),
            )
        return rooms

    def get_room(self, room_id: str) -> RoomInfo:
        """Get detailed room information from configuration."""
        config = self._load_config()

        if room_id not in config.room_configs:
            available = list(config.room_configs.keys())
            msg = f"Room '{room_id}' not found. Available: {available}"
            raise KeyError(msg)

        room_config = config.room_configs[room_id]
        return RoomInfo(
            id=room_id,
            name=getattr(room_config, "name", room_id),
            description=getattr(room_config, "description", None),
            model=getattr(room_config, "model", None),
            welcome_message=getattr(room_config, "welcome_message", None),
            suggestions=getattr(room_config, "suggestions", None),
        )

    def ask(self, room_id: str, query: str) -> str:
        """Not supported by DirectClient.

        Raises:
            NotImplementedError: Always raised.
        """
        raise NotImplementedError(
            "DirectClient cannot execute queries. "
            "Use HTTPClient with a running Soliplex server."
        )

    def get_installation_info(self) -> InstallationInfo:
        """Get installation-level information."""
        config = self._load_config()
        skills = self.list_skills()

        return InstallationInfo(
            id=config.id,
            room_count=len(config.room_configs),
            skill_count=len(skills),
            agent_configs=[a.id for a in config.agent_configs],
            environment=dict(config.environment),
        )

    def list_skills(self) -> dict[str, SkillInfo]:
        """List all skills available in the installation."""
        config = self._load_config()

        # Collect all skill directories from all rooms
        skill_dirs: set[Path] = set()
        for room_config in config.room_configs.values():
            if hasattr(room_config, "tool_configs"):
                for tc in room_config.tool_configs.values():
                    if hasattr(tc, "directories") and tc.directories:
                        skill_dirs.update(tc.directories)

        if not skill_dirs:
            return {}

        # Load skills from directories
        try:
            from pydantic_ai_skills import SkillsToolset
        except ImportError:
            return {}

        toolset = SkillsToolset(directories=[str(d) for d in skill_dirs])

        skills = {}
        for name, skill in toolset.skills.items():
            scripts = []
            if skill.scripts:
                scripts = [s.name for s in skill.scripts]

            resources = []
            if skill.resources:
                resources = [r.name for r in skill.resources]

            skills[name] = SkillInfo(
                name=name,
                description=skill.description,
                path=str(skill.path) if hasattr(skill, "path") else None,
                scripts=scripts if scripts else None,
                resources=resources if resources else None,
            )

        return skills

    def get_skill(self, skill_name: str) -> SkillInfo:
        """Get detailed information about a specific skill."""
        skills = self.list_skills()
        if skill_name not in skills:
            available = list(skills.keys())
            msg = f"Skill '{skill_name}' not found. Available: {available}"
            raise KeyError(msg)
        return skills[skill_name]

    def get_room_tools(self, room_id: str) -> list[ToolConfigInfo]:
        """Get tool configurations for a room."""
        config = self._load_config()

        if room_id not in config.room_configs:
            available = list(config.room_configs.keys())
            msg = f"Room '{room_id}' not found. Available: {available}"
            raise KeyError(msg)

        room_config = config.room_configs[room_id]
        tools = []

        if hasattr(room_config, "tool_configs"):
            for name, tc in room_config.tool_configs.items():
                dirs = None
                if hasattr(tc, "directories") and tc.directories:
                    dirs = [str(d) for d in tc.directories]

                tools.append(
                    ToolConfigInfo(
                        name=name,
                        tool_type=type(tc).__name__,
                        tool_name=getattr(tc, "tool_name", None),
                        directories=dirs,
                    )
                )

        return tools

    def get_agent_configs(self) -> list[AgentConfigInfo]:
        """Get all agent configurations."""
        config = self._load_config()

        return [
            AgentConfigInfo(
                id=ac.id,
                model_name=ac.model_name,
                retries=getattr(ac, "retries", 3),
            )
            for ac in config.agent_configs
        ]


def create_client(
    url: str | None = None,
    installation_path: str | Path | None = None,
) -> SoliplexClient:
    """Create appropriate client based on available configuration.

    Priority:
    1. Explicit url parameter -> HTTPClient
    2. Explicit installation_path parameter -> DirectClient
    3. SOLIPLEX_URL environment variable -> HTTPClient
    4. SOLIPLEX_INSTALLATION environment variable -> DirectClient
    5. Default HTTPClient with localhost

    Args:
        url: Optional server URL for HTTPClient.
        installation_path: Optional path to installation.yaml for DirectClient.

    Returns:
        SoliplexClient instance (HTTPClient or DirectClient).
    """
    # Explicit parameters take priority
    if url:
        return HTTPClient(url)

    if installation_path:
        return DirectClient(installation_path)

    # Check environment variables
    env_url = os.environ.get("SOLIPLEX_URL")
    if env_url:
        return HTTPClient(env_url)

    env_installation = os.environ.get("SOLIPLEX_INSTALLATION")
    if env_installation:
        return DirectClient(env_installation)

    # Default to HTTP with localhost
    return HTTPClient("http://127.0.0.1:8002")


def can_import_soliplex() -> bool:
    """Check if soliplex package is importable."""
    try:
        from soliplex.config import load_installation  # noqa: F401
    except ImportError:
        return False
    else:
        return True
