# Soliplex Architecture

## Core Concepts

Soliplex is a multi-room AI agent platform. Understanding these concepts is essential:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Installation                             │
│  ┌───────────────────┐  ┌───────────────────┐                   │
│  │      Room A       │  │      Room B       │                   │
│  │  ┌─────────────┐  │  │  ┌─────────────┐  │                   │
│  │  │   Agent     │  │  │  │   Agent     │  │                   │
│  │  │  ┌───────┐  │  │  │  │  ┌───────┐  │  │                   │
│  │  │  │Tools[]│  │  │  │  │  │Tools[]│  │  │                   │
│  │  │  │MCP{}  │  │  │  │  │  │MCP{}  │  │  │                   │
│  │  │  └───────┘  │  │  │  │  └───────┘  │  │                   │
│  │  └─────────────┘  │  │  └─────────────┘  │                   │
│  │  Model: gpt-20b   │  │  Model: llama3    │                   │
│  └───────────────────┘  └───────────────────┘                   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                 Authorization Layer                      │    │
│  │  AdminUsers │ RoomPolicies │ ACLEntries                 │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

An **Installation** is the top-level container that defines a Soliplex deployment.

**File:** `installation.yaml`

```yaml
id: my-soliplex
name: My Soliplex

# Register custom ToolConfig classes (CRITICAL)
meta:
  tool_configs:
    - my_adapter.config.QueryServiceConfig

# Environment variables
environment:
  OLLAMA_BASE_URL: http://bizon:11434

# Room paths
room_paths:
  - ./rooms/math-room
  - ./rooms/code-room

# Authorization database (⚠️ defaults to in-memory!)
room_authz_dburi: sqlite:///./authz.db
```

**Key properties:**
- `id` - Unique installation identifier
- `meta.tool_configs` - **CRITICAL**: Custom ToolConfig class registration
- `environment.OLLAMA_BASE_URL` - LLM backend (NOT `ollama_host` at root!)
- `room_paths` - List of room directories to load
- `room_authz_dburi` - Authorization database

See [config-system.md](config-system.md) for detailed configuration reference.

## Room

A **Room** is an isolated conversation space with its own agent, tools, and MCP connections.

**File:** `room_config.yaml`

```yaml
id: gpt-20b
name: GPT-OSS 20B

# Agent settings NESTED under 'agent:' key
agent:
  model: gpt-oss:20b
  system_prompt: |
    You are a math assistant.

# Tools use tool_name (dotted path)
tools:
  - tool_name: soliplex_skills.tools.run_skill
    path: ../../skills

# MCP servers in separate block
mcp_client_toolsets:
  filesystem:
    kind: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem"]
```

**Key properties:**
- `agent.model` - LLM model name (nested!)
- `agent.system_prompt` - Instructions for the LLM (nested!)
- `tools` - List of ToolConfig objects (keyed by `tool_name`)
- `mcp_client_toolsets` - MCP server connections (separate from tools)

## Tool

A **Tool** is a capability available to the room's agent.

### Built-in Tools

| Tool | Purpose | Config Required |
|------|---------|-----------------|
| `get_current_datetime` | Returns ISO datetime | No |
| `get_current_user` | Returns UserProfile | No |
| `search_documents` | Semantic search LanceDB | Yes |
| `research_report` | Deep research via graph agent | Yes |

### Custom Tools

Tools are configured by `tool_name` (dotted import path), NOT by `type`. See [adapter-patterns.md](adapter-patterns.md) for building custom tools.

## Runtime Flow

```
User Query
    │
    ▼
┌─────────────┐     ┌─────────────┐
│   Auth      │────▶│  Authz      │
│  (JWT/OIDC) │     │ (Room ACL)  │
└─────┬───────┘     └─────────────┘
      │
      ▼
┌─────────────┐
│    Room     │
│  (Agent)    │
└─────┬───────┘
      │
      ▼
┌─────────────┐     ┌─────────────┐
│   Model     │────▶│   Tools     │
│  (Ollama)   │◀────│  (Skills)   │
└─────────────┘     └─────────────┘
      │
      ▼
  SSE Response
```

1. User authenticates via OAuth2/OIDC (JWT token) → See [auth.md](auth.md)
2. Authorization checks room access (ACL policies)
3. User sends query to room via AG-UI protocol → See [ag-ui.md](ag-ui.md)
4. Room's agent processes with configured model
5. Model may invoke tools to complete the task
6. Response streams back via SSE

## Related Documentation

| Topic | File |
|-------|------|
| AG-UI Protocol | [ag-ui.md](ag-ui.md) - Events, state management, SSE parsing |
| Authentication & Authorization | [auth.md](auth.md) - OIDC, ACL, security warnings |
| Configuration | [config-system.md](config-system.md) - YAML structures, tool_name resolution |
| Building Adapters | [adapter-patterns.md](adapter-patterns.md) - Tool patterns, caching |
| API Endpoints | [api-reference.md](api-reference.md) - HTTP API, event types |

## Directory Structure

```
installation/
├── installation.yaml          # Top-level config
├── rooms/
│   ├── room-a/
│   │   └── room_config.yaml
│   └── room-b/
│       └── room_config.yaml
└── skills/
    ├── skill-x/
    │   ├── SKILL.md
    │   ├── scripts/
    │   └── references/
    └── skill-y/
        └── ...
```

## Key Classes (Python)

| Class | Purpose |
|-------|---------|
| `InstallationConfig` | Loads installation.yaml |
| `RoomConfig` | Loads room_config.yaml |
| `ToolConfig` | Base class for tool configurations |
| `AgentDependencies` | Runtime context for tools |
| `ThreadStorage` | Thread/run CRUD contract |
| `EventStreamParser` | AG-UI event state machine |

## Known Limitations

### Critical

1. **Data Loss on Disconnect** - Client disconnect during SSE = events not saved
2. **Agent Caching** - Config frozen at creation; see [adapter-patterns.md](adapter-patterns.md#2-agent-caching-and-config-lifecycle)
3. **Public-by-Default Rooms** - No policy = public; see [auth.md](auth.md)
4. **Multi-Worker Session Breakage** - Requires `SESSION_SECRET_KEY`

### Medium

5. **Thinking Events Not Persisted** - Live but filtered from replay
6. **MCP Client No Caching** - Fetches tool list every run
7. **MCP Token No Revocation** - Valid until expiry

See `KNOWN_ISSUES.md` in project root for full tracking.
