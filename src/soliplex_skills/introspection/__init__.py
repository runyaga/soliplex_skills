"""Introspection tools for cross-room discovery and delegation.

This module provides tools for agents to:
- Discover other rooms and their capabilities
- Delegate queries to other room agents

Auth filtering is supported via `use_auth_filter: true` in config.
No Soliplex changes required - we create RoomAuthorization directly.
"""

from __future__ import annotations

from soliplex_skills.introspection.authz_helper import get_room_authz
from soliplex_skills.introspection.config import DelegateToRoomConfig
from soliplex_skills.introspection.config import DiscoverRoomsConfig
from soliplex_skills.introspection.config import IntrospectionToolConfig
from soliplex_skills.introspection.tools import DelegationError
from soliplex_skills.introspection.tools import DelegationResult
from soliplex_skills.introspection.tools import delegate_to_room
from soliplex_skills.introspection.tools import discover_rooms

__all__ = [
    "DelegateToRoomConfig",
    "DelegationError",
    "DelegationResult",
    "DiscoverRoomsConfig",
    "IntrospectionToolConfig",
    "delegate_to_room",
    "discover_rooms",
    "get_room_authz",
]
