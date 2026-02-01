# Soliplex Architecture

## Core Concepts

Soliplex is a multi-room AI agent platform. Understanding these three concepts is essential:

```
┌─────────────────────────────────────────────────────────────┐
│                     Installation                             │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │     Room A      │  │     Room B      │                   │
│  │  ┌───────────┐  │  │  ┌───────────┐  │                   │
│  │  │  Tool 1   │  │  │  │  Tool 3   │  │                   │
│  │  │  Tool 2   │  │  │  │  Tool 4   │  │                   │
│  │  └───────────┘  │  │  └───────────┘  │                   │
│  │  Model: gpt-20b │  │  Model: llama3  │                   │
│  └─────────────────┘  └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## Installation

An **Installation** is the top-level container that defines a Soliplex deployment.

**File:** `installation.yaml`

```yaml
name: my-soliplex
description: My Soliplex installation
host: 127.0.0.1
port: 8002
ollama_host: bizon:11434
rooms:
  - path: ./rooms/math-room
  - path: ./rooms/code-room
```

**Key properties:**
- `name` - Installation identifier
- `host/port` - Server binding
- `ollama_host` - LLM backend (Ollama server)
- `rooms` - List of room paths to load
- `room_authz_dburi` - Optional authorization database

## Room

A **Room** is an isolated conversation space with its own:
- Model configuration
- System prompt
- Available tools
- Welcome message and suggestions

**File:** `room_config.yaml`

```yaml
id: gpt-20b
name: GPT-OSS 20B
description: Math-capable room
model: gpt-oss:20b

system_prompt: |
  You are a math assistant. Use available tools.

welcome_message: |
  Welcome! I can help with calculations.

suggestions:
  - "Calculate factorial of 23"
  - "What is 2^100?"

tools:
  - type: skills
    path: ../../skills
```

**Key properties:**
- `id` - Unique room identifier (used in API paths)
- `model` - Ollama model name
- `system_prompt` - Instructions for the LLM
- `tools` - List of tool configurations

## Tool

A **Tool** is a capability available to the room's agent. Soliplex supports several tool types:

### Built-in Tool Types

| Type | Description |
|------|-------------|
| `skills` | pydantic-ai-skills integration |
| `mcp` | Model Context Protocol servers |
| `function` | Direct Python functions |

### Skills Tool Configuration

```yaml
tools:
  - type: skills
    path: ../../skills           # Path to skills directory
    include:                      # Optional: whitelist skills
      - math-solver
    exclude:                      # Optional: blacklist skills
      - dangerous-skill
```

The `skills` tool type loads skills from a directory. Each skill provides:
- Tool definitions (from SKILL.md)
- Executable scripts (from scripts/)
- Resources (from resources/)

## Runtime Flow

```
User Query
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
  Response
```

1. User sends query to room via AG-UI protocol
2. Room's agent processes with configured model
3. Model may invoke tools to complete the task
4. Tools execute and return results
5. Model formulates final response
6. Response streams back via SSE

## Directory Structure

```
installation/
├── installation.yaml          # Top-level config
├── rooms/
│   ├── room-a/
│   │   └── room_config.yaml   # Room A config
│   └── room-b/
│       └── room_config.yaml   # Room B config
└── skills/
    ├── skill-x/
    │   ├── SKILL.md           # Skill definition
    │   ├── scripts/           # Executable tools
    │   └── resources/         # Reference docs
    └── skill-y/
        └── ...
```

## Key Classes (Python)

| Class | Purpose |
|-------|---------|
| `InstallationConfig` | Loads installation.yaml |
| `RoomConfig` | Loads room_config.yaml |
| `ToolConfig` | Base class for tool configurations |
| `SkillsToolConfig` | Skills-specific tool config |

See `config-system.md` for details on the configuration hierarchy.
