"""Introspection tools for cross-room discovery and delegation.

These tools allow agents to discover other rooms and delegate queries.

Note on Authorization:
    These tools do NOT filter rooms by user authorization.
    The `RoomAuthorization` protocol is only available in the FastAPI
    request context, not in tool context.

    For production use, consider:
    1. Adding `the_room_authz` to AgentDependencies (Soliplex change)
    2. Using these tools only in trusted environments
    3. Configuring `exclude_rooms` to hide sensitive rooms

Note on Delegation:
    The `delegate_to_room` tool executes synchronously - the client will
    see the calling agent as "thinking" until the delegated agent completes.
    No streaming of intermediate results is supported.

    The delegated agent runs with fresh state and does NOT have access to:
    - The calling room's conversation history
    - The calling room's AG-UI emitter (no state updates to client)
    - The calling room's tool configs
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING
from typing import Any

import pydantic

if TYPE_CHECKING:
    import pydantic_ai

    from soliplex_skills.introspection.config import IntrospectionToolConfig


class RoomInfo(pydantic.BaseModel):
    """Information about a discovered room."""

    id: str
    name: str
    description: str
    tools: list[str] | None = None
    model: str | None = None
    welcome_message: str | None = None
    suggestions: list[str] | None = None


class DiscoveryResult(pydantic.BaseModel):
    """Result of room discovery."""

    rooms: dict[str, RoomInfo]
    total_count: int
    filtered_count: int
    note: str | None = None


async def discover_rooms(
    ctx: pydantic_ai.RunContext[Any],
    tool_config: IntrospectionToolConfig | None = None,
) -> DiscoveryResult:
    """Discover available rooms and their capabilities.

    Returns information about all configured rooms including their names,
    descriptions, available tools, and agent models.

    By default, this tool does NOT filter by user authorization. Set
    `use_auth_filter: true` in config to enable auth filtering (requires
    soliplex.authz module).

    Args:
        ctx: The run context containing agent dependencies
        tool_config: Configuration for discovery behavior

    Returns:
        DiscoveryResult with room information
    """
    from soliplex_skills.introspection.authz_helper import get_room_authz

    # Get installation from context
    installation = ctx.deps.the_installation
    user = getattr(ctx.deps, "user", None)

    # Determine if we should use auth filtering
    use_auth = False
    exclude_rooms: frozenset[str] = frozenset()
    include_tools = True
    include_model = True

    if tool_config is not None:
        use_auth = tool_config.use_auth_filter
        exclude_rooms = tool_config.exclude_rooms
        include_tools = tool_config.include_tools
        include_model = tool_config.include_model

    # Get room configs with optional auth filtering
    if use_auth:
        async with get_room_authz(installation) as room_authz:
            room_configs = await installation.get_room_configs(
                user=user,
                the_room_authz=room_authz,  # May be None if unavailable
            )
    else:
        room_configs = await installation.get_room_configs(
            user=user,
            the_room_authz=None,
        )

    total_count = len(room_configs)

    # Build room info dict
    rooms: dict[str, RoomInfo] = {}
    for room_id, room_config in room_configs.items():
        if room_id in exclude_rooms:
            continue

        # Extract tool names if requested
        tools = None
        if include_tools:
            tools = list(room_config.tool_configs.keys())

        # Extract model info if requested
        model = None
        if include_model and hasattr(room_config, "agent_config"):
            agent_config = room_config.agent_config
            if hasattr(agent_config, "model_name"):
                model = agent_config.model_name

        rooms[room_id] = RoomInfo(
            id=room_id,
            name=room_config.name,
            description=room_config.description,
            tools=tools,
            model=model,
            welcome_message=getattr(room_config, "welcome_message", None),
            suggestions=getattr(room_config, "suggestions", None),
        )

    filtered_count = len(rooms)

    # Add note if rooms were filtered
    note = None
    if filtered_count < total_count:
        hidden = total_count - filtered_count
        note = f"{hidden} room(s) hidden by configuration"

    return DiscoveryResult(
        rooms=rooms,
        total_count=total_count,
        filtered_count=filtered_count,
        note=note,
    )


class DelegationResult(pydantic.BaseModel):
    """Result of delegating a query to another room."""

    room_id: str
    room_name: str
    query: str
    response: str
    success: bool
    error: str | None = None
    delegation_depth: int = 1


class DelegationError(Exception):
    """Error during room delegation."""

    pass


async def delegate_to_room(
    ctx: pydantic_ai.RunContext[Any],
    room_id: str,
    query: str,
    tool_config: IntrospectionToolConfig | None = None,
) -> DelegationResult:
    """Delegate a query to another room's agent.

    Executes the query using the target room's agent and returns the result.
    This is a synchronous operation - the calling agent will wait for the
    delegated agent to complete before continuing.

    IMPORTANT: This tool does NOT stream results back to the client.
    The client will see this as the calling agent "thinking" until complete.

    Args:
        ctx: The run context containing agent dependencies
        room_id: The ID of the room to delegate to
        query: The query/prompt to send to the target room's agent
        tool_config: Configuration for delegation behavior

    Returns:
        DelegationResult with the response from the target room

    Raises:
        DelegationError: If the room is not found or delegation fails
    """
    # Get current delegation depth from state
    current_depth = ctx.deps.state.get("_delegation_depth", 0)

    # Check max depth
    max_depth = 2
    if tool_config is not None:
        max_depth = tool_config.max_delegation_depth

    if current_depth >= max_depth:
        return DelegationResult(
            room_id=room_id,
            room_name="<unknown>",
            query=query,
            response="",
            success=False,
            error=f"Max delegation depth ({max_depth}) exceeded",
            delegation_depth=current_depth,
        )

    # Check if room is excluded
    if tool_config is not None and room_id in tool_config.exclude_rooms:
        return DelegationResult(
            room_id=room_id,
            room_name="<hidden>",
            query=query,
            response="",
            success=False,
            error=f"Room '{room_id}' is not available for delegation",
            delegation_depth=current_depth + 1,
        )

    from soliplex_skills.introspection.authz_helper import get_room_authz

    installation = ctx.deps.the_installation
    user = getattr(ctx.deps, "user", None)

    # Determine if we should use auth filtering
    use_auth = tool_config.use_auth_filter if tool_config else False

    # Get target room config with optional auth filtering
    try:
        if use_auth:
            async with get_room_authz(installation) as room_authz:
                target_room = await installation.get_room_config(
                    room_id=room_id,
                    user=user,
                    the_room_authz=room_authz,
                )
        else:
            target_room = await installation.get_room_config(
                room_id=room_id,
                user=user,
                the_room_authz=None,
            )
    except KeyError:
        return DelegationResult(
            room_id=room_id,
            room_name="<not found>",
            query=query,
            response="",
            success=False,
            error=f"Room '{room_id}' not found",
            delegation_depth=current_depth + 1,
        )

    # Get target room's agent
    try:
        target_agent = await installation.get_agent_for_room(
            room_id=room_id,
            user=user,
            the_room_authz=None,
        )
    except KeyError:
        return DelegationResult(
            room_id=room_id,
            room_name=target_room.name,
            query=query,
            response="",
            success=False,
            error=f"Could not get agent for room '{room_id}'",
            delegation_depth=current_depth + 1,
        )

    # Create AgentDependencies for target agent
    # We need to import this dynamically to avoid circular imports
    # and to handle the case where soliplex is not installed
    try:
        from soliplex.agents import AgentDependencies
    except ImportError:
        # Create a minimal dataclass for testing without soliplex
        @dataclasses.dataclass
        class AgentDependencies:  # type: ignore[no-redef]
            the_installation: Any
            user: Any = None
            tool_configs: Any = None
            agui_emitter: Any = None
            state: dict = dataclasses.field(default_factory=dict)

    target_deps = AgentDependencies(
        the_installation=installation,
        user=user,
        tool_configs=target_room.tool_configs,
        agui_emitter=None,  # No streaming to client
        state={"_delegation_depth": current_depth + 1},
    )

    # Get emitter for progress events (may be None)
    emitter = getattr(ctx.deps, "agui_emitter", None)
    step_name = f"delegate:{room_id}"

    # Start delegation step
    if emitter is not None:
        try:
            emitter.start_step(step_name)
        except Exception:
            pass  # Don't fail delegation if emitter errors

    # Run the query through the target agent
    try:
        result = await target_agent.run(query, deps=target_deps)
        response_text = str(result.data) if result.data else ""

        return DelegationResult(
            room_id=room_id,
            room_name=target_room.name,
            query=query,
            response=response_text,
            success=True,
            delegation_depth=current_depth + 1,
        )
    except Exception as e:
        return DelegationResult(
            room_id=room_id,
            room_name=target_room.name,
            query=query,
            response="",
            success=False,
            error=f"Delegation failed: {e!s}",
            delegation_depth=current_depth + 1,
        )
    finally:
        # Finish delegation step
        if emitter is not None:
            try:
                emitter.finish_step(step_name)
            except Exception:
                pass  # Don't fail if emitter errors
