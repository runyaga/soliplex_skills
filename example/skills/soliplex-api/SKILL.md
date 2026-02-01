---
name: soliplex-api
description: Soliplex API client and adapter development guide - interact with Soliplex and learn to build adapters
---

# Soliplex API Skill

This skill provides two capabilities:

1. **API Client** - Query and delegate tasks to Soliplex rooms
2. **Adapter Guide** - Documentation for building Soliplex integrations

## When to Use This Skill

**As a Tool:**
- Discover available Soliplex rooms and their capabilities
- Delegate specialized tasks to rooms (math, code review, research)
- Get computed results from room agents

**As Documentation:**
- Learn Soliplex architecture and concepts
- Understand adapter patterns for wrapping external libraries
- Reference when building new Soliplex integrations

## Resources

### Start Here
- `INDEX.md` - Meta-guide: what's in each resource, reading order
- `design-principles.md` - Core principles for Soliplex development

### API & Architecture
- `api-reference.md` - HTTP endpoints and AG-UI protocol
- `architecture.md` - Core concepts: rooms, tools, installations
- `config-system.md` - ToolConfig, RoomConfig, InstallationConfig

### Adapter Development
- `adapter-patterns.md` - Patterns for building Soliplex adapters
- `soliplex-skills-example.md` - Case study: how soliplex_skills was built

### Validation
Run `scripts/validate_resources.py` to check for context rot in docs.

## Scripts

### client.py

Python module with dual client support:

```python
from client import create_client, HTTPClient, DirectClient

# Auto-detect best client
client = create_client()

# Or explicitly choose
client = HTTPClient("http://127.0.0.1:8002")
client = DirectClient("/path/to/installation.yaml")
```

**Client Interface:**
| Method | HTTPClient | DirectClient | Description |
|--------|------------|--------------|-------------|
| `list_rooms()` | ✅ | ✅ | Get all available rooms |
| `get_room(id)` | ✅ | ✅ | Get room details |
| `ask(id, query)` | ✅ | ❌ | Send query, get response |
| `get_installation_info()` | ❌ | ✅ | Installation overview |
| `list_skills()` | ❌ | ✅ | Get all skills |
| `get_skill(name)` | ❌ | ✅ | Get skill details |
| `get_room_tools(id)` | ❌ | ✅ | Get room's tool configs |
| `get_agent_configs()` | ❌ | ✅ | Get agent configurations |

DirectClient methods require compatible soliplex package version.

### soliplex_client.py

CLI wrapper for quick access.

**Via skill tools (kwargs format):**
```python
run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                 args={"command": "list_rooms"})

run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                 args={"command": "room_info", "room_id": "gpt-20b"})

run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                 args={"command": "ask", "room_id": "gpt-20b",
                       "query": "Calculate factorial(5)"})
```

**Direct CLI usage:**
```bash
# HTTPClient commands (uses SOLIPLEX_URL or default localhost)
python soliplex_client.py --command list_rooms
python soliplex_client.py --command room_info --room_id gpt-20b
python soliplex_client.py --command ask --room_id gpt-20b --query "Hello"

# DirectClient commands (requires --direct flag)
python soliplex_client.py --direct installation.yaml --command installation_info
python soliplex_client.py --direct installation.yaml --command list_skills
python soliplex_client.py --direct installation.yaml --command skill_info --skill_name math-solver
python soliplex_client.py --direct installation.yaml --command room_tools --room_id gpt-20b
python soliplex_client.py --direct installation.yaml --command agent_configs
```

## Configuration

```bash
# Server URL for HTTPClient
export SOLIPLEX_URL=http://127.0.0.1:8002

# Installation path for DirectClient
export SOLIPLEX_INSTALLATION=/path/to/installation.yaml
```

## Quick Start

### 1. Discovery (HTTPClient - recommended)

```python
from client import HTTPClient

client = HTTPClient("http://127.0.0.1:8002")
rooms = client.list_rooms()
for room_id, info in rooms.items():
    print(f"{room_id}: {info.name}")
    if info.description:
        print(f"  {info.description}")
```

### 2. Execution (requires running server)

```python
from client import HTTPClient

client = HTTPClient("http://127.0.0.1:8002")
result = client.ask("gpt-20b", "What is factorial(23)?")
print(result)  # 25852016738884976640000
```

### 3. Offline Introspection (DirectClient)

```python
from client import DirectClient

client = DirectClient("/path/to/installation.yaml")

# Installation overview
info = client.get_installation_info()
print(f"Rooms: {info.room_count}, Skills: {info.skill_count}")

# List all skills
for name, skill in client.list_skills().items():
    print(f"{name}: {skill.description}")

# Get room tools
for tool in client.get_room_tools("gpt-20b"):
    print(f"{tool.name}: {tool.tool_name}")
```

## Notes

### DirectClient Compatibility

DirectClient uses `soliplex.config.load_installation()` to parse config files
directly. This requires:

1. The `soliplex` package installed (`pip install soliplex`)
2. Compatible soliplex version that supports your installation.yaml schema

If DirectClient fails to load configs, use HTTPClient instead (recommended).
HTTPClient works with any running Soliplex server regardless of version.

### HTTPClient vs DirectClient

| Feature | HTTPClient | DirectClient |
|---------|------------|--------------|
| Requires running server | Yes | No |
| Room discovery | ✅ | ✅ |
| Send queries | ✅ | ❌ |
| Skill introspection | ❌ | ✅ |
| Tool config details | ❌ | ✅ |
| Agent config details | ❌ | ✅ |
| Version sensitivity | Low | High |

**Use HTTPClient** for runtime operations (queries, responses).
**Use DirectClient** for offline config introspection and development.

## Learning Path

To understand Soliplex and build adapters:

1. Read `architecture.md` - Understand core concepts
2. Read `config-system.md` - Learn the configuration patterns
3. Read `adapter-patterns.md` - Study adapter design
4. Read `soliplex-skills-example.md` - See a real implementation
5. Use the client scripts to experiment
