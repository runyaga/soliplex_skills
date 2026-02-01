"""Helper to create RoomAuthorization without Soliplex changes.

This module provides a way to get auth-filtered room access from within
a tool context, without requiring changes to Soliplex's AgentDependencies.

Usage:
    from soliplex_skills.introspection.authz_helper import get_room_authz

    async def my_tool(ctx: RunContext[AgentDependencies]):
        async with get_room_authz(ctx.deps.the_installation) as room_authz:
            # room_authz may be None if soliplex.authz is not available
            if room_authz is not None:
                rooms = await installation.get_room_configs(
                    user=ctx.deps.user,
                    the_room_authz=room_authz,
                )
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@contextlib.asynccontextmanager
async def get_room_authz(
    installation: Any,
) -> AsyncGenerator[Any, None]:
    """Create a RoomAuthorization instance from the installation.

    This is a workaround for the fact that AgentDependencies doesn't
    include the_room_authz. We create our own session and authz instance.

    Args:
        installation: The Soliplex Installation instance

    Yields:
        RoomAuthorization instance, or None if not available

    Example:
        async with get_room_authz(ctx.deps.the_installation) as authz:
            if authz:
                rooms = await installation.get_room_configs(
                    user=user, the_room_authz=authz
                )
    """
    try:
        from soliplex.authz.schema import RoomAuthorization
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy.ext.asyncio import create_async_engine
    except ImportError:
        # Soliplex not installed or authz module not available
        yield None
        return

    # Get the database URI from installation
    try:
        dburi = installation.room_authz_dburi_async
    except AttributeError:
        # Installation doesn't have room_authz_dburi_async
        yield None
        return

    if not dburi:
        yield None
        return

    # Create engine and session
    engine = create_async_engine(dburi)
    try:
        async with AsyncSession(engine) as session:
            room_authz = RoomAuthorization(session)
            yield room_authz
    finally:
        await engine.dispose()
