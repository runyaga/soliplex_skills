# Soliplex Skills Project

This project provides a Soliplex adapter for pydantic-ai-skills.

## Soliplex API Skill

Use the `soliplex-api` skill in `example/skills/soliplex-api/` to interact with Soliplex installations.

### Quick Reference

**List rooms (HTTPClient - requires running server):**
```bash
cd example && uv run python skills/soliplex-api/scripts/soliplex_client.py --command list_rooms
```

**Get room details:**
```bash
cd example && uv run python skills/soliplex-api/scripts/soliplex_client.py --command room_info --room_id gpt-20b
```

**Send query to room:**
```bash
cd example && uv run python skills/soliplex-api/scripts/soliplex_client.py --command ask --room_id gpt-20b --query "Calculate factorial(10)"
```

### DirectClient (Offline Introspection)

For offline config analysis without a running server:

```bash
cd example && uv run python skills/soliplex-api/scripts/soliplex_client.py \
  --direct installation.yaml --command installation_info

cd example && uv run python skills/soliplex-api/scripts/soliplex_client.py \
  --direct installation.yaml --command list_skills

cd example && uv run python skills/soliplex-api/scripts/soliplex_client.py \
  --direct installation.yaml --command room_tools --room_id gpt-20b
```

### Available Commands

| Command | Requires Server | Description |
|---------|-----------------|-------------|
| `list_rooms` | HTTPClient or DirectClient | List all rooms |
| `room_info` | HTTPClient or DirectClient | Room details (+ `--room_id`) |
| `ask` | HTTPClient only | Send query (+ `--room_id`, `--query`) |
| `installation_info` | DirectClient only | Installation overview |
| `list_skills` | DirectClient only | All available skills |
| `skill_info` | DirectClient only | Skill details (+ `--skill_name`) |
| `room_tools` | DirectClient only | Room tool configs (+ `--room_id`) |
| `agent_configs` | DirectClient only | Agent configurations |

### Starting the Server

```bash
cd example && OLLAMA_BASE_URL=http://bizon:11434 uv run python run_server.py
```

Or if a CLI is available:
```bash
cd example && OLLAMA_BASE_URL=http://bizon:11434 uv run soliplex --no-auth-mode
```

### Documentation

For Soliplex architecture and adapter development, read:
- `example/skills/soliplex-api/resources/architecture.md`
- `example/skills/soliplex-api/resources/config-system.md`
- `example/skills/soliplex-api/resources/adapter-patterns.md`

## Project Structure

```
soliplex_skills/
├── src/soliplex_skills/     # Main adapter package
├── example/
│   ├── installation.yaml    # Example Soliplex installation
│   ├── rooms/               # Room configurations
│   ├── skills/              # Skills including soliplex-api
│   └── run_server.py        # Server startup script
└── tests/                   # Unit and integration tests
```
