"""Helper to create AuthorizationPolicy without Soliplex changes.

This module provides a way to get auth-filtered room access from within
a tool context, without requiring changes to Soliplex's AgentDependencies.

Usage:
    from soliplex_skills.introspection.authz_helper import get_room_authz

    async def my_tool(ctx: RunContext[AgentDependencies]):
        async with get_room_authz(ctx.deps.the_installation) as authz_policy:
            # authz_policy may be None if soliplex.authz is not available
            if authz_policy is not None:
                rooms = await installation.get_room_configs(
                    user=ctx.deps.user,
                    the_authz_policy=authz_policy,
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
    """Create an AuthorizationPolicy instance from the installation.

    This is a workaround for the fact that AgentDependencies doesn't
    include the_authz_policy. We create our own session and authz instance.

    Args:
        installation: The Soliplex Installation instance

    Yields:
        AuthorizationPolicy instance, or None if not available

    Example:
        async with get_room_authz(ctx.deps.the_installation) as authz:
            if authz:
                rooms = await installation.get_room_configs(
                    user=user, the_authz_policy=authz
                )
    """
    try:
        from soliplex.authz.schema import AuthorizationPolicy
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy.ext.asyncio import create_async_engine
    except ImportError:
        # Soliplex not installed or authz module not available
        yield None
        return

    # Get the database URI from installation
    try:
        dburi = installation.authorization_dburi_async
    except AttributeError:
        # Installation doesn't have authorization_dburi_async
        yield None
        return

    if not dburi:
        yield None
        return

    # Create engine and session
    engine = create_async_engine(dburi)
    try:
        async with AsyncSession(engine) as session:
            authz_policy = AuthorizationPolicy(session)
            yield authz_policy
    finally:
        await engine.dispose()
