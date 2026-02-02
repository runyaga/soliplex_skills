---
name: soliplex-api
description: Interact with Soliplex AI rooms via API client, and learn to build Soliplex adapters. Use when working with Soliplex servers, querying rooms, building tool integrations, or understanding Soliplex architecture (AG-UI protocol, authentication, MCP).
---

# Soliplex API Skill

## When to Activate This Skill

Use this skill when the user needs to:

**API Operations:**
- List or query Soliplex rooms
- Send questions to room agents
- Discover room capabilities (tools, models)
- Work with Soliplex server APIs

**Development Tasks:**
- Build a Soliplex adapter or integration
- Understand ToolConfig, RoomConfig, or InstallationConfig
- Configure tools in room_config.yaml or installation.yaml
- Debug AG-UI streaming, SSE events, or authentication issues

**Keywords:** soliplex, room, agent, tool, adapter, AG-UI, MCP, ToolConfig, installation.yaml, room_config.yaml

## Capabilities

| Capability | Description |
|------------|-------------|
| **HTTPClient** | Query running Soliplex servers (list rooms, send queries) |
| **DirectClient** | Offline config introspection (skills, tools, agents) |
| **Documentation** | Architecture, config system, adapter patterns |

## Quick Start

**List rooms from a running server:**
```python
run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                 args={"command": "list_rooms"})
```

**Query a room:**
```python
run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                 args={"command": "ask", "room_id": "gpt-20b",
                       "query": "Calculate factorial(5)"})
```

**Offline config introspection:**
```python
run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                 args={"direct": "installation.yaml", "command": "list_skills"})
```

**JSON output (for structured parsing):**
```python
run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                 args={"command": "list_rooms", "format": "json"})
```

## Reference Files

Read these files for detailed information:

| File | Purpose |
|------|---------|
| `references/INDEX.md` | Meta-guide: what's in each file, reading order |
| `references/architecture.md` | Core concepts, runtime flow, directory structure |
| `references/ag-ui.md` | AG-UI protocol, 25+ event types, SSE parsing |
| `references/auth.md` | Authentication, authorization, security warnings |
| `references/config-system.md` | YAML structures, ToolConfig, environment vars |
| `references/adapter-patterns.md` | Tool patterns (Pattern A/B), agent caching |
| `references/api-reference.md` | HTTP endpoints, request/response formats |
| `references/client-usage.md` | Client usage, script reference, examples |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/soliplex_client.py` | CLI for HTTPClient and DirectClient |
| `scripts/client.py` | Python client library |
| `scripts/validate_resources.py` | Check documentation for context rot |

## Environment

```bash
SOLIPLEX_URL=http://127.0.0.1:8000      # HTTPClient server
SOLIPLEX_INSTALLATION=/path/to/install   # DirectClient config
```

## Learning Path

1. `references/architecture.md` - Core concepts
2. `references/config-system.md` - Configuration
3. `references/adapter-patterns.md` - Building adapters
4. `references/api-reference.md` - API integration
