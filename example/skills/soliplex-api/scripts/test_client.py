"""Tests for Soliplex client module.

Run with: pytest test_client.py
"""

import os
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from client import DirectClient
from client import HTTPClient
from client import RoomInfo
from client import create_client


class TestRoomInfo:
    """Tests for RoomInfo dataclass."""

    def test_room_info_required_fields(self):
        """Test RoomInfo with required fields only."""
        info = RoomInfo(id="test", name="Test Room")
        assert info.id == "test"
        assert info.name == "Test Room"
        assert info.description is None

    def test_room_info_all_fields(self):
        """Test RoomInfo with all fields."""
        info = RoomInfo(
            id="test",
            name="Test Room",
            description="A test room",
            model="gpt-4",
            welcome_message="Welcome!",
            suggestions=["Try this", "Or that"],
        )
        assert info.id == "test"
        assert info.name == "Test Room"
        assert info.description == "A test room"
        assert info.model == "gpt-4"
        assert info.welcome_message == "Welcome!"
        assert info.suggestions == ["Try this", "Or that"]


class TestHTTPClient:
    """Tests for HTTPClient."""

    def test_init_default_url(self):
        """Test default URL."""
        client = HTTPClient()
        assert client.base_url == "http://127.0.0.1:8002"

    def test_init_custom_url(self):
        """Test custom URL."""
        client = HTTPClient("http://example.com:9000")
        assert client.base_url == "http://example.com:9000"

    def test_init_strips_trailing_slash(self):
        """Test URL normalization."""
        client = HTTPClient("http://example.com/")
        assert client.base_url == "http://example.com"

    def test_httpx_import_error(self):
        """Test error when httpx not installed."""
        client = HTTPClient()
        client._httpx = None

        with (
            patch.dict("sys.modules", {"httpx": None}),
            patch("builtins.__import__", side_effect=ImportError),
            pytest.raises(ImportError, match="httpx required"),
        ):
            client._get_httpx()

    @patch("client.HTTPClient._get_httpx")
    def test_list_rooms(self, mock_httpx):
        """Test list_rooms method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "room1": {"name": "Room 1", "description": "First room"},
            "room2": {"name": "Room 2", "model": "gpt-4"},
        }
        mock_httpx.return_value.get.return_value = mock_response

        client = HTTPClient()
        rooms = client.list_rooms()

        assert "room1" in rooms
        assert "room2" in rooms
        assert rooms["room1"].name == "Room 1"
        assert rooms["room1"].description == "First room"
        assert rooms["room2"].model == "gpt-4"

    @patch("client.HTTPClient._get_httpx")
    def test_get_room(self, mock_httpx):
        """Test get_room method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "Test Room",
            "description": "A test",
            "model": "gpt-4",
            "welcome_message": "Hello!",
            "suggestions": ["Try me"],
        }
        mock_httpx.return_value.get.return_value = mock_response

        client = HTTPClient()
        room = client.get_room("test-room")

        assert room.id == "test-room"
        assert room.name == "Test Room"
        assert room.description == "A test"
        assert room.model == "gpt-4"
        assert room.welcome_message == "Hello!"
        assert room.suggestions == ["Try me"]


class TestDirectClient:
    """Tests for DirectClient."""

    def test_init(self):
        """Test initialization."""
        client = DirectClient("/path/to/installation.yaml")
        assert client.installation_path == Path("/path/to/installation.yaml")
        assert client._config is None

    def test_ask_not_implemented(self):
        """Test ask() raises NotImplementedError."""
        client = DirectClient("/path/to/installation.yaml")

        with pytest.raises(NotImplementedError, match="DirectClient cannot"):
            client.ask("room", "query")

    def test_soliplex_import_error(self):
        """Test error when soliplex not installed."""
        client = DirectClient("/path/to/installation.yaml")

        with (
            patch.dict("sys.modules", {"soliplex": None}),
            patch("builtins.__import__", side_effect=ImportError),
            pytest.raises(ImportError, match="soliplex required"),
        ):
            client._load_config()

    @patch("client.DirectClient._load_config")
    def test_list_rooms(self, mock_load):
        """Test list_rooms method."""
        mock_room = MagicMock()
        mock_room.name = "Test Room"
        mock_room.description = "A test room"
        mock_room.model = "gpt-4"
        mock_room.welcome_message = None
        mock_room.suggestions = None

        mock_config = MagicMock()
        mock_config.room_configs = {"test-room": mock_room}
        mock_load.return_value = mock_config

        client = DirectClient("/path/to/installation.yaml")
        rooms = client.list_rooms()

        assert "test-room" in rooms
        assert rooms["test-room"].name == "Test Room"
        assert rooms["test-room"].description == "A test room"

    @patch("client.DirectClient._load_config")
    def test_get_room(self, mock_load):
        """Test get_room method."""
        mock_room = MagicMock()
        mock_room.name = "Test Room"
        mock_room.description = "A test room"
        mock_room.model = "gpt-4"
        mock_room.welcome_message = "Welcome!"
        mock_room.suggestions = ["Try this"]

        mock_config = MagicMock()
        mock_config.room_configs = {"test-room": mock_room}
        mock_load.return_value = mock_config

        client = DirectClient("/path/to/installation.yaml")
        room = client.get_room("test-room")

        assert room.id == "test-room"
        assert room.name == "Test Room"

    @patch("client.DirectClient._load_config")
    def test_get_room_not_found(self, mock_load):
        """Test get_room with nonexistent room."""
        mock_config = MagicMock()
        mock_config.room_configs = {}
        mock_load.return_value = mock_config

        client = DirectClient("/path/to/installation.yaml")

        with pytest.raises(KeyError, match="not found"):
            client.get_room("nonexistent")


class TestCreateClient:
    """Tests for create_client factory function."""

    def test_explicit_url(self):
        """Test explicit URL parameter."""
        client = create_client(url="http://example.com")
        assert isinstance(client, HTTPClient)
        assert client.base_url == "http://example.com"

    def test_explicit_installation_path(self):
        """Test explicit installation path parameter."""
        client = create_client(installation_path="/path/to/installation.yaml")
        assert isinstance(client, DirectClient)
        assert client.installation_path == Path("/path/to/installation.yaml")

    def test_url_takes_priority(self):
        """Test URL takes priority over installation path."""
        client = create_client(
            url="http://example.com",
            installation_path="/path/to/installation.yaml",
        )
        assert isinstance(client, HTTPClient)

    def test_env_url(self):
        """Test SOLIPLEX_URL environment variable."""
        with patch.dict(os.environ, {"SOLIPLEX_URL": "http://env.com"}):
            client = create_client()
            assert isinstance(client, HTTPClient)
            assert client.base_url == "http://env.com"

    def test_env_installation(self):
        """Test SOLIPLEX_INSTALLATION environment variable."""
        with patch.dict(
            os.environ,
            {"SOLIPLEX_INSTALLATION": "/env/installation.yaml"},
            clear=True,
        ):
            # Clear SOLIPLEX_URL to test SOLIPLEX_INSTALLATION
            os.environ.pop("SOLIPLEX_URL", None)
            client = create_client()
            assert isinstance(client, DirectClient)

    def test_default_http_client(self):
        """Test default is HTTPClient with localhost."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SOLIPLEX_URL", None)
            os.environ.pop("SOLIPLEX_INSTALLATION", None)
            client = create_client()
            assert isinstance(client, HTTPClient)
            assert client.base_url == "http://127.0.0.1:8002"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
