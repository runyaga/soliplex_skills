#!/usr/bin/env python3
"""Soliplex API CLI client.

Usage via skill tools:
    run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                     args={"command": "list_rooms"})

    run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                     args={"command": "room_info", "room_id": "gpt-20b"})

    run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                     args={"command": "ask", "room_id": "gpt-20b",
                           "query": "Calculate factorial(5)"})

    # DirectClient-only introspection commands:
    run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                     args={"direct": "path/to/installation.yaml",
                           "command": "installation_info"})

    run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                     args={"direct": "path/to/installation.yaml",
                           "command": "list_skills"})

Direct CLI usage:
    python soliplex_client.py --command list_rooms
    python soliplex_client.py --command room_info --room_id gpt-20b
    python soliplex_client.py --command ask --room_id gpt-20b --query "Hello"

    # JSON output (for structured parsing):
    python soliplex_client.py --command list_rooms --format json

    # DirectClient introspection (requires --direct flag):
    python soliplex_client.py --direct i.yaml --command installation_info
    python soliplex_client.py --direct i.yaml --command list_skills
    python soliplex_client.py --direct i.yaml --command agent_configs

Environment:
    SOLIPLEX_URL          Server URL (default: http://127.0.0.1:8002)
    SOLIPLEX_INSTALLATION Path to installation.yaml for DirectClient
"""

import argparse
import json
import sys

from client import DirectClient
from client import create_client


def list_rooms(client, use_json: bool = False) -> None:
    """List all available rooms."""
    rooms = client.list_rooms()
    if use_json:
        data = {
            rid: {
                "name": info.name,
                "description": info.description,
                "model": info.model,
            }
            for rid, info in rooms.items()
        }
        print(json.dumps(data, indent=2))
    else:
        for room_id, info in rooms.items():
            print(f"{room_id}: {info.name}")
            if info.description:
                print(f"  {info.description}")


def room_info(client, room_id: str, use_json: bool = False) -> None:
    """Get detailed room information."""
    try:
        room = client.get_room(room_id)
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if use_json:
        data = {
            "id": room.id,
            "name": room.name,
            "model": room.model,
            "description": room.description,
            "welcome_message": room.welcome_message,
            "suggestions": room.suggestions,
        }
        print(json.dumps(data, indent=2))
    else:
        print(f"Room: {room.name}")
        print(f"ID: {room.id}")
        if room.model:
            print(f"Model: {room.model}")
        if room.description:
            print(f"Description: {room.description}")
        if room.welcome_message:
            print(f"Welcome: {room.welcome_message.strip()}")
        if room.suggestions:
            print(f"Suggestions: {room.suggestions}")


def ask(client, room_id: str, query: str, use_json: bool = False) -> None:
    """Send a query to a room."""
    if isinstance(client, DirectClient):
        print(
            "Error: ask() requires HTTPClient. "
            "Remove --direct flag or set SOLIPLEX_URL.",
            file=sys.stderr,
        )
        sys.exit(1)

    response = client.ask(room_id, query)
    if use_json:
        data = {"room_id": room_id, "query": query, "response": response}
        print(json.dumps(data))
    else:
        print(response)


def installation_info(client, use_json: bool = False) -> None:
    """Get installation-level information (DirectClient only)."""
    if not isinstance(client, DirectClient):
        print("Error: requires --direct flag", file=sys.stderr)
        sys.exit(1)

    info = client.get_installation_info()
    if use_json:
        data = {
            "id": info.id,
            "room_count": info.room_count,
            "skill_count": info.skill_count,
            "agent_configs": info.agent_configs,
            "environment": info.environment,
        }
        print(json.dumps(data, indent=2))
    else:
        print(f"Installation ID: {info.id}")
        print(f"Rooms: {info.room_count}")
        print(f"Skills: {info.skill_count}")
        print(f"Agent Configs: {', '.join(info.agent_configs)}")
        if info.environment:
            print("Environment:")
            for key, val in info.environment.items():
                display_val = val if val else "(not set)"
                print(f"  {key}: {display_val}")


def list_skills(client, use_json: bool = False) -> None:
    """List all skills in the installation (DirectClient only)."""
    if not isinstance(client, DirectClient):
        print("Error: list_skills requires --direct flag", file=sys.stderr)
        sys.exit(1)

    skills = client.list_skills()
    if use_json:
        data = {
            name: {
                "description": skill.description,
                "scripts": skill.scripts,
                "resources": skill.resources,
            }
            for name, skill in skills.items()
        }
        print(json.dumps(data, indent=2))
    else:
        if not skills:
            print("No skills found")
            return
        for name, skill in skills.items():
            print(f"{name}: {skill.description}")
            if skill.scripts:
                print(f"  Scripts: {', '.join(skill.scripts)}")
            if skill.resources:
                print(f"  Resources: {', '.join(skill.resources)}")


def skill_info(client, skill_name: str, use_json: bool = False) -> None:
    """Get detailed skill information (DirectClient only)."""
    if not isinstance(client, DirectClient):
        print("Error: skill_info requires --direct flag", file=sys.stderr)
        sys.exit(1)

    try:
        skill = client.get_skill(skill_name)
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if use_json:
        data = {
            "name": skill.name,
            "description": skill.description,
            "path": skill.path,
            "scripts": skill.scripts,
            "resources": skill.resources,
        }
        print(json.dumps(data, indent=2))
    else:
        print(f"Skill: {skill.name}")
        print(f"Description: {skill.description}")
        if skill.path:
            print(f"Path: {skill.path}")
        if skill.scripts:
            print(f"Scripts: {', '.join(skill.scripts)}")
        if skill.resources:
            print(f"Resources: {', '.join(skill.resources)}")


def room_tools(client, room_id: str, use_json: bool = False) -> None:
    """Get tool configurations for a room (DirectClient only)."""
    if not isinstance(client, DirectClient):
        print("Error: room_tools requires --direct flag", file=sys.stderr)
        sys.exit(1)

    try:
        tools = client.get_room_tools(room_id)
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if use_json:
        data = [
            {
                "name": tool.name,
                "tool_type": tool.tool_type,
                "tool_name": tool.tool_name,
                "directories": tool.directories,
            }
            for tool in tools
        ]
        print(json.dumps({"room_id": room_id, "tools": data}, indent=2))
    else:
        if not tools:
            print(f"No tools configured for room '{room_id}'")
            return
        print(f"Tools in room '{room_id}':")
        for tool in tools:
            print(f"  {tool.name} ({tool.tool_type})")
            if tool.tool_name:
                print(f"    Tool: {tool.tool_name}")
            if tool.directories:
                print(f"    Directories: {', '.join(tool.directories)}")


def agent_configs(client, use_json: bool = False) -> None:
    """List all agent configurations (DirectClient only)."""
    if not isinstance(client, DirectClient):
        print("Error: agent_configs requires --direct flag", file=sys.stderr)
        sys.exit(1)

    configs = client.get_agent_configs()
    if use_json:
        data = [
            {"id": ac.id, "model_name": ac.model_name, "retries": ac.retries}
            for ac in configs
        ]
        print(json.dumps({"agent_configs": data}, indent=2))
    else:
        if not configs:
            print("No agent configurations found")
            return
        print("Agent Configurations:")
        for ac in configs:
            print(f"  {ac.id}:")
            print(f"    Model: {ac.model_name}")
            print(f"    Retries: {ac.retries}")


def main():
    parser = argparse.ArgumentParser(description="Soliplex API client")

    # Kwargs-style arguments (for skill tool invocation)
    all_commands = [
        "list_rooms",
        "room_info",
        "ask",
        # DirectClient-only commands:
        "installation_info",
        "list_skills",
        "skill_info",
        "room_tools",
        "agent_configs",
    ]
    parser.add_argument(
        "--command",
        choices=all_commands,
        help="Command to execute",
    )
    parser.add_argument("--room_id", help="Room ID for room commands")
    parser.add_argument("--query", help="Query for ask command")
    parser.add_argument("--skill_name", help="Skill name for skill_info")
    parser.add_argument(
        "--direct",
        metavar="PATH",
        help="Use DirectClient with installation.yaml path",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Create appropriate client
    client = DirectClient(args.direct) if args.direct else create_client()
    use_json = args.format == "json"

    try:
        if args.command == "list_rooms":
            list_rooms(client, use_json)
        elif args.command == "room_info":
            if not args.room_id:
                print("Error: --room_id required", file=sys.stderr)
                sys.exit(1)
            room_info(client, args.room_id, use_json)
        elif args.command == "ask":
            if not args.room_id:
                print("Error: --room_id required for ask", file=sys.stderr)
                sys.exit(1)
            if not args.query:
                print("Error: --query required for ask", file=sys.stderr)
                sys.exit(1)
            ask(client, args.room_id, args.query, use_json)
        elif args.command == "installation_info":
            installation_info(client, use_json)
        elif args.command == "list_skills":
            list_skills(client, use_json)
        elif args.command == "skill_info":
            if not args.skill_name:
                print("Error: --skill_name required", file=sys.stderr)
                sys.exit(1)
            skill_info(client, args.skill_name, use_json)
        elif args.command == "room_tools":
            if not args.room_id:
                print("Error: --room_id required", file=sys.stderr)
                sys.exit(1)
            room_tools(client, args.room_id, use_json)
        elif args.command == "agent_configs":
            agent_configs(client, use_json)
    except ImportError as e:
        print(f"Dependency Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        error_type = type(e).__name__
        if "HTTP" in error_type or "Request" in error_type:
            print(f"Connection Error: {e}", file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
