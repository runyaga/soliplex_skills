"""Integration tests for Soliplex clients.

These tests validate that both DirectClient and HTTPClient work correctly
against real Soliplex configurations and servers.

Run all tests:
    pytest test_client_integration.py -v

Run DirectClient tests only (no server required):
    pytest test_client_integration.py -v -k "direct"

Run HTTPClient tests only (server must be running):
    pytest test_client_integration.py -v -k "http"
"""

import os
from pathlib import Path

import pytest
from client import DirectClient
from client import HTTPClient
from client import RoomInfo
from client import create_client

# Path to test installation
INSTALLATION_PATH = (
    Path(__file__).parent.parent.parent.parent / "installation.yaml"
)

# Default server URL
SERVER_URL = os.environ.get("SOLIPLEX_URL", "http://127.0.0.1:8002")


def has_soliplex_installed() -> bool:
    """Check if soliplex package is available."""
    try:
        from soliplex.config import load_installation  # noqa: F401
    except ImportError:
        return False
    else:
        return True


def can_load_installation() -> bool:
    """Check if installation.yaml loads with current soliplex version."""
    if not has_soliplex_installed():
        return False
    if not INSTALLATION_PATH.exists():
        return False
    try:
        from soliplex.config import load_installation

        config = load_installation(INSTALLATION_PATH)
        config.reload_configurations()
    except Exception:
        return False
    else:
        return True


def is_server_running() -> bool:
    """Check if Soliplex server is accessible."""
    try:
        import httpx

        resp = httpx.get(f"{SERVER_URL}/api/ok", timeout=2)
    except Exception:
        return False
    else:
        return resp.status_code == 200


# Skip markers for conditional tests
requires_soliplex = pytest.mark.skipif(
    not has_soliplex_installed(),
    reason="soliplex package not installed",
)

requires_server = pytest.mark.skipif(
    not is_server_running(),
    reason=f"Soliplex server not running at {SERVER_URL}",
)

requires_installation = pytest.mark.skipif(
    not INSTALLATION_PATH.exists(),
    reason=f"Installation file not found: {INSTALLATION_PATH}",
)

requires_loadable_config = pytest.mark.skipif(
    not can_load_installation(),
    reason="Cannot load installation.yaml with current soliplex version",
)


class TestDirectClientIntegration:
    """Integration tests for DirectClient."""

    @requires_loadable_config
    def test_direct_client_list_rooms(self):
        """Test DirectClient can list rooms from installation.yaml."""
        client = DirectClient(INSTALLATION_PATH)
        rooms = client.list_rooms()

        assert isinstance(rooms, dict)
        assert len(rooms) > 0, "Expected at least one room"

        # Verify room structure
        for room_id, room in rooms.items():
            assert isinstance(room_id, str)
            assert isinstance(room, RoomInfo)
            assert room.id == room_id
            assert room.name is not None

    @requires_loadable_config
    def test_direct_client_get_room(self):
        """Test DirectClient can get specific room details."""
        client = DirectClient(INSTALLATION_PATH)
        rooms = client.list_rooms()

        # Get first available room
        room_id = next(iter(rooms.keys()))
        room = client.get_room(room_id)

        assert isinstance(room, RoomInfo)
        assert room.id == room_id
        assert room.name is not None

    @requires_loadable_config
    def test_direct_client_get_room_not_found(self):
        """Test DirectClient raises KeyError for nonexistent room."""
        client = DirectClient(INSTALLATION_PATH)

        with pytest.raises(KeyError, match="not found"):
            client.get_room("nonexistent-room-xyz")

    @requires_loadable_config
    def test_direct_client_ask_not_supported(self):
        """Test DirectClient raises NotImplementedError for ask()."""
        client = DirectClient(INSTALLATION_PATH)

        with pytest.raises(NotImplementedError):
            client.ask("any-room", "any query")


class TestHTTPClientIntegration:
    """Integration tests for HTTPClient."""

    @requires_server
    def test_http_client_list_rooms(self):
        """Test HTTPClient can list rooms from server."""
        client = HTTPClient(SERVER_URL)
        rooms = client.list_rooms()

        assert isinstance(rooms, dict)
        assert len(rooms) > 0, "Expected at least one room"

        # Verify room structure
        for room_id, room in rooms.items():
            assert isinstance(room_id, str)
            assert isinstance(room, RoomInfo)
            assert room.id == room_id
            assert room.name is not None

    @requires_server
    def test_http_client_get_room(self):
        """Test HTTPClient can get specific room details."""
        client = HTTPClient(SERVER_URL)
        rooms = client.list_rooms()

        # Get first available room
        room_id = next(iter(rooms.keys()))
        room = client.get_room(room_id)

        assert isinstance(room, RoomInfo)
        assert room.id == room_id
        assert room.name is not None

    @requires_server
    def test_http_client_ask_simple_query(self):
        """Test HTTPClient can send queries and get responses from LLM."""
        client = HTTPClient(SERVER_URL)
        rooms = client.list_rooms()

        # Get first available room
        room_id = next(iter(rooms.keys()))

        # Send a simple query that should get a response
        response = client.ask(room_id, "Say hello in one word.")

        assert isinstance(response, str)
        assert len(response) > 0, "Expected non-empty response from LLM"
        print(f"LLM Response: {response[:100]}...")

    @requires_server
    def test_http_client_ask_math_query(self):
        """Test HTTPClient can send math queries to LLM with tool support."""
        client = HTTPClient(SERVER_URL)

        # Use gpt-20b room if available (has math tools)
        rooms = client.list_rooms()
        room_id = "gpt-20b" if "gpt-20b" in rooms else next(iter(rooms.keys()))

        # Send a math query
        response = client.ask(room_id, "What is 5 + 3?", timeout=120)

        assert isinstance(response, str)
        assert len(response) > 0, "Expected non-empty response"
        print(f"Math Response: {response}")

    @requires_server
    def test_http_client_ask_timeout(self):
        """Test HTTPClient respects timeout parameter."""
        client = HTTPClient(SERVER_URL)
        rooms = client.list_rooms()
        room_id = next(iter(rooms.keys()))

        # This should work with reasonable timeout
        response = client.ask(room_id, "Hi", timeout=60)
        assert isinstance(response, str)


class TestLLMToolCalling:
    """Tests that verify tool calling through the LLM API."""

    @requires_server
    def test_math_tool_factorial(self):
        """Test LLM can use factorial tool through API."""
        client = HTTPClient(SERVER_URL)
        rooms = client.list_rooms()

        # Use gpt-20b room (has math-solver skill)
        if "gpt-20b" not in rooms:
            pytest.skip("gpt-20b room not available")

        response = client.ask(
            "gpt-20b",
            "Calculate factorial of 5 using the calculate tool.",
            timeout=120,
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # factorial(5) = 120
        assert "120" in response, f"Expected 120 in response: {response}"
        print(f"Factorial response: {response}")

    @requires_server
    def test_math_tool_add(self):
        """Test LLM can use add operation through API."""
        client = HTTPClient(SERVER_URL)
        rooms = client.list_rooms()

        if "gpt-20b" not in rooms:
            pytest.skip("gpt-20b room not available")

        response = client.ask(
            "gpt-20b",
            "Use the calculate tool to add 15 and 27.",
            timeout=120,
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # 15 + 27 = 42
        assert "42" in response, f"Expected 42 in response: {response}"
        print(f"Add response: {response}")

    @requires_server
    def test_math_tool_power(self):
        """Test LLM can use power operation through API."""
        client = HTTPClient(SERVER_URL)
        rooms = client.list_rooms()

        if "gpt-20b" not in rooms:
            pytest.skip("gpt-20b room not available")

        response = client.ask(
            "gpt-20b",
            "Use the calculate tool to compute 2 to the power of 10.",
            timeout=120,
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # 2^10 = 1024
        assert "1024" in response, f"Expected 1024 in response: {response}"
        print(f"Power response: {response}")


class TestCreateClientIntegration:
    """Integration tests for create_client factory."""

    @requires_loadable_config
    def test_create_client_with_installation_path(self):
        """Test create_client returns DirectClient for installation path."""
        client = create_client(installation_path=INSTALLATION_PATH)
        assert isinstance(client, DirectClient)

        # Verify it works
        rooms = client.list_rooms()
        assert len(rooms) > 0

    @requires_server
    def test_create_client_with_url(self):
        """Test create_client returns HTTPClient for URL."""
        client = create_client(url=SERVER_URL)
        assert isinstance(client, HTTPClient)

        # Verify it works
        rooms = client.list_rooms()
        assert len(rooms) > 0

    @requires_loadable_config
    def test_create_client_env_installation(self, monkeypatch):
        """Test create_client uses SOLIPLEX_INSTALLATION env var."""
        monkeypatch.setenv("SOLIPLEX_INSTALLATION", str(INSTALLATION_PATH))
        monkeypatch.delenv("SOLIPLEX_URL", raising=False)

        client = create_client()
        assert isinstance(client, DirectClient)

    @requires_server
    def test_create_client_env_url(self, monkeypatch):
        """Test create_client uses SOLIPLEX_URL env var."""
        monkeypatch.setenv("SOLIPLEX_URL", SERVER_URL)
        monkeypatch.delenv("SOLIPLEX_INSTALLATION", raising=False)

        client = create_client()
        assert isinstance(client, HTTPClient)


class TestClientConsistency:
    """Tests that both clients return consistent data."""

    @requires_loadable_config
    @requires_server
    def test_both_clients_list_same_rooms(self):
        """Test DirectClient and HTTPClient list the same rooms."""
        direct = DirectClient(INSTALLATION_PATH)
        http = HTTPClient(SERVER_URL)

        direct_rooms = direct.list_rooms()
        http_rooms = http.list_rooms()

        # Both should have the same room IDs
        assert set(direct_rooms.keys()) == set(http_rooms.keys())

        # Room names should match
        for room_id in direct_rooms:
            assert direct_rooms[room_id].name == http_rooms[room_id].name

    @requires_loadable_config
    @requires_server
    def test_both_clients_get_same_room_details(self):
        """Test DirectClient and HTTPClient return same room details."""
        direct = DirectClient(INSTALLATION_PATH)
        http = HTTPClient(SERVER_URL)

        # Get a room from both clients
        rooms = direct.list_rooms()
        room_id = next(iter(rooms.keys()))

        direct_room = direct.get_room(room_id)
        http_room = http.get_room(room_id)

        # Core fields should match
        assert direct_room.id == http_room.id
        assert direct_room.name == http_room.name
        assert direct_room.model == http_room.model


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
