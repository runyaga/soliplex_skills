# Soliplex API Reference

Detailed client usage, script reference, and examples.

## Client Library (client.py)

### Creating Clients

```python
from client import create_client, HTTPClient, DirectClient

# Auto-detect best client
client = create_client()

# Or explicitly choose
client = HTTPClient("http://127.0.0.1:8000")
client = DirectClient("/path/to/installation.yaml")
```

### Client Interface

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

## CLI Usage (soliplex_client.py)

### HTTPClient Commands

```bash
# List all rooms
python scripts/soliplex_client.py --command list_rooms

# Get room details
python scripts/soliplex_client.py --command room_info --room_id gpt-20b

# Send query to room
python scripts/soliplex_client.py --command ask --room_id gpt-20b --query "Calculate factorial(5)"
```

### DirectClient Commands

```bash
# Installation overview
python scripts/soliplex_client.py --direct installation.yaml --command installation_info

# List all skills
python scripts/soliplex_client.py --direct installation.yaml --command list_skills

# Get skill details
python scripts/soliplex_client.py --direct installation.yaml --command skill_info --skill_name math-solver

# Get room tools
python scripts/soliplex_client.py --direct installation.yaml --command room_tools --room_id gpt-20b

# Get agent configurations
python scripts/soliplex_client.py --direct installation.yaml --command agent_configs
```

### Via Skill Tools (kwargs format)

```python
run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                 args={"command": "list_rooms"})

run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                 args={"command": "room_info", "room_id": "gpt-20b"})

run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                 args={"command": "ask", "room_id": "gpt-20b",
                       "query": "Calculate factorial(5)"})
```

## Examples

### Discovery (HTTPClient)

```python
from client import HTTPClient

client = HTTPClient("http://127.0.0.1:8000")
rooms = client.list_rooms()
for room_id, info in rooms.items():
    print(f"{room_id}: {info.name}")
    if info.description:
        print(f"  {info.description}")
```

### Query Execution

```python
from client import HTTPClient

client = HTTPClient("http://127.0.0.1:8000")
result = client.ask("gpt-20b", "What is factorial(23)?")
print(result)  # 25852016738884976640000
```

### Offline Introspection (DirectClient)

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

## HTTPClient vs DirectClient

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

## DirectClient Compatibility

DirectClient uses `soliplex.config.load_installation()` to parse config files directly. This requires:

1. The `soliplex` package installed (`pip install soliplex`)
2. Compatible soliplex version that supports your installation.yaml schema

If DirectClient fails to load configs, use HTTPClient instead (recommended).
HTTPClient works with any running Soliplex server regardless of version.

## All Commands Reference

| Command | Client | Required Args | Description |
|---------|--------|---------------|-------------|
| `list_rooms` | Both | - | List all rooms |
| `room_info` | Both | `--room_id` | Room details |
| `ask` | HTTPClient | `--room_id`, `--query` | Send query |
| `installation_info` | DirectClient | - | Installation overview |
| `list_skills` | DirectClient | - | All available skills |
| `skill_info` | DirectClient | `--skill_name` | Skill details |
| `room_tools` | DirectClient | `--room_id` | Room tool configs |
| `agent_configs` | DirectClient | - | Agent configurations |
