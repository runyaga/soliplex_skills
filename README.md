# soliplex-skills

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Soliplex adapter for [pydantic-ai-skills](https://github.com/DougTrajano/pydantic-ai-skills) - progressive, on-demand capability loading for AI agents.

## What Are Skills?

Skills are **domain-specific capability bundles** that agents discover and load on-demand. Unlike static tools, skills provide:

- **Progressive Disclosure**: Agents load only what they need, when needed
- **Self-Documenting**: Instructions embedded in SKILL.md files
- **Composable**: Combine resources + scripts for complex workflows
- **Portable**: Same skill works across different rooms/agents

## Features

- **4 Core Tools**: `list_skills`, `load_skill`, `read_skill_resource`, `run_skill_script`
- **Pydantic-First Config**: Native types, no string parsing
- **Multi-Directory Support**: Load skills from multiple sources
- **Per-Room Configuration**: Different rooms can have different skill sets
- **Introspection Tools**: `discover_rooms`, `delegate_to_room` for cross-room coordination
- **Soliplex Integration**: Full compatibility with Soliplex's config system

## Installation

### From Source (Recommended)

```bash
git clone https://github.com/soliplex/soliplex_skills.git
cd soliplex_skills
uv sync
```

### From PyPI (when published)

```bash
# Using uv
uv add soliplex-skills

# Using pip
pip install soliplex-skills
```

### With Soliplex Integration

For full Soliplex integration, install Soliplex first:

```bash
git clone https://github.com/soliplex/soliplex.git ../soliplex
uv pip install -e ../soliplex
```

## Quick Start

### 1. Create a Skill

```
my_skills/
└── research-assistant/
    ├── SKILL.md              # Skill definition
    └── resources/
        └── citation-formats.md
```

**SKILL.md**:
```markdown
---
name: research-assistant
description: Helps with research tasks and finding information
---

# Research Assistant

Use this skill for research tasks including:
- Finding relevant papers and articles
- Summarizing information
- Citing sources properly

## Resources

- `citation-formats.md`: Reference for citation styles (APA, MLA, Chicago)
```

### 2. Configure a Room

```yaml
# room_config.yaml
id: research-room
name: Research Assistant
description: Academic research with citation support

agent:
  template_id: default_chat
  system_prompt: ./prompt.txt

tools:
  - tool_name: soliplex_skills.tools.list_skills
    directories:
      - ./skills

  - tool_name: soliplex_skills.tools.load_skill
    directories:
      - ./skills

  - tool_name: soliplex_skills.tools.read_skill_resource
    directories:
      - ./skills
```

### 3. Register Tool Configs

In your `installation.yaml`:

```yaml
meta:
  tool_configs:
    - soliplex_skills.config.ListSkillsConfig
    - soliplex_skills.config.LoadSkillConfig
    - soliplex_skills.config.ReadSkillResourceConfig
    - soliplex_skills.config.RunSkillScriptConfig
```

## Tools Reference

### list_skills

Lists all available skills with descriptions.

```python
result = await list_skills(tool_config)
# Returns: {"research-assistant": "Helps with research tasks..."}
```

### load_skill

Loads complete instructions for a specific skill.

```python
result = await load_skill(tool_config, skill_name="research-assistant")
# Returns: XML-formatted skill with instructions, resources, scripts
```

### read_skill_resource

Reads a skill resource file or invokes a callable resource.

```python
result = await read_skill_resource(
    tool_config,
    skill_name="research-assistant",
    resource_name="resources/citation-formats.md"
)
# Returns: Resource content as string
```

### run_skill_script

Executes a skill script with optional arguments.

```python
result = await run_skill_script(
    tool_config,
    skill_name="calculator",
    script_name="scripts/compute.py",
    args={"expression": "2 + 2"}
)
# Returns: Script output
```

## Configuration

### SkillsToolConfig

```python
from soliplex_skills import SkillsToolConfig

config = SkillsToolConfig(
    tool_name="soliplex_skills.tools.list_skills",
    directories=(Path("./skills"), Path("../shared_skills")),
    exclude_tools=frozenset(["run_skill_script"]),  # Disable scripts
    validate_skills=True,
    max_depth=3,
)
```

### Environment Variables

```bash
# Default skill directories (comma-separated)
export SOLIPLEX_SKILLS_DIRECTORIES="./skills,../shared_skills"

# Validate skill structure (default: true)
export SOLIPLEX_SKILLS_VALIDATE=true

# Discovery depth (default: 3)
export SOLIPLEX_SKILLS_MAX_DEPTH=3

# Disable specific tools
export SOLIPLEX_SKILLS_EXCLUDE_TOOLS="run_skill_script"
```

### YAML Configuration

```yaml
# Supports both list format (preferred)
directories:
  - ./skills
  - ../shared_skills

# And legacy string format
directories: ./skills,../shared_skills
```

## Introspection Tools

For cross-room coordination:

### discover_rooms

```python
from soliplex_skills import discover_rooms

result = await discover_rooms(ctx, tool_config=config)
# Returns: DiscoveryResult with room info, tools, models
```

### delegate_to_room

```python
from soliplex_skills import delegate_to_room

result = await delegate_to_room(
    ctx,
    room_id="research",
    query="Find papers on transformers"
)
# Returns: DelegationResult with response from delegated room
```

## Examples

See the `example/` directory for complete working examples:

- `example/rooms/research-assistant/` - RAG-powered research room
- `example/rooms/code-reviewer/` - Code review with style guides
- `example/rooms/coordinator/` - Cross-room delegation demo
- `example/skills/` - Sample skills

## Development

### Run Tests

```bash
uv run pytest
```

### Run Linter

```bash
uv run ruff check src tests
```

### Run with Coverage

```bash
uv run pytest --cov=soliplex_skills --cov-report=html
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Soliplex Room                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Agent                             │   │
│  │  "Load the research-assistant skill"                │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │              soliplex_skills Tools                   │   │
│  │  list_skills → load_skill → read_skill_resource     │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
          ┌───────────────▼───────────────┐
          │      Skills Directories        │
          │  ./skills/                     │
          │    research-assistant/         │
          │      SKILL.md                  │
          │      resources/                │
          │    code-review/                │
          │      SKILL.md                  │
          └───────────────────────────────┘
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Related Projects

- [pydantic-ai-skills](https://github.com/DougTrajano/pydantic-ai-skills) - Upstream skills library
- [Soliplex](https://github.com/soliplex/soliplex) - AI-powered RAG system
- [pydantic-ai](https://github.com/pydantic/pydantic-ai) - AI agent framework
