# Soliplex Skills Examples

This directory contains example scenarios demonstrating how Skills enhance
Soliplex room functionality.

## What Are Skills?

Skills are **progressive, domain-specific capability bundles** that agents
can discover and load on-demand. Unlike static tools, skills:

1. **Progressive Disclosure**: Agent loads only what it needs, when needed
2. **Self-Documenting**: Instructions embedded in SKILL.md files
3. **Composable**: Combine resources + scripts for complex workflows
4. **Portable**: Same skill works across different rooms/agents

## Example Scenarios

### 1. Research Assistant Room

**Use Case**: A room where users ask research questions and the agent
searches academic sources, synthesizes findings, and cites references.

**Skills Add**:
- `academic-search`: Instructions for searching arxiv, PubMed, etc.
- `citation-manager`: Resource with citation formatting templates
- `summarization`: Script that generates structured summaries

**Without Skills**: You'd hardcode search logic into room-specific tools.
**With Skills**: The skill provides portable research methodology that
works in any "research-focused" room.

See: `rooms/research-assistant/`

### 2. Code Reviewer Room

**Use Case**: A room that reviews pull requests, suggests improvements,
and enforces coding standards.

**Skills Add**:
- `code-review`: Checklist-based review methodology
- `style-guides`: Resource files for Python, TypeScript, Go standards
- `security-audit`: Script running security pattern detection

**Key Benefit**: The `style-guides` resource can be updated centrally,
and all code review rooms automatically get the latest standards.

See: `rooms/code-reviewer/`

### 3. Data Analysis Room

**Use Case**: Users upload CSVs and ask questions about the data.

**Skills Add**:
- `data-profiling`: Script generating statistics and quality reports
- `visualization`: Instructions for chart recommendations
- `sql-generation`: Converts natural language to SQL queries

**Key Benefit**: The `data-profiling` script can execute Python code
to generate actual statistics, not just explanations.

## Skills Directory Structure

```
example/
├── skills/                          # Shared skills for all rooms
│   ├── research-assistant/
│   │   ├── SKILL.md                 # Skill definition
│   │   ├── resources/
│   │   │   └── citation-formats.md  # Static resource
│   │   └── scripts/
│   │       └── search.py            # Executable script
│   └── code-review/
│       ├── SKILL.md
│       └── resources/
│           ├── python-style.md
│           └── security-checklist.md
└── rooms/
    ├── research-assistant/
    │   ├── room_config.yaml
    │   └── prompt.txt
    └── code-reviewer/
        ├── room_config.yaml
        └── prompt.txt
```

## Room Configuration Pattern

Each room specifies which skill directories to search:

```yaml
# room_config.yaml
id: research-assistant
name: Research Assistant
description: Research and citation support

agent:
  template_id: default_chat
  system_prompt: ./prompt.txt

tools:
  # Skills tools - all use same directories
  - tool_name: soliplex_skills.tools.list_skills
    directories: ../../skills

  - tool_name: soliplex_skills.tools.load_skill
    directories: ../../skills

  - tool_name: soliplex_skills.tools.read_skill_resource
    directories: ../../skills

  - tool_name: soliplex_skills.tools.run_skill_script
    directories: ../../skills
```

## Workflow Example

**User**: "Find recent papers on transformer architectures"

**Agent** (using skills):
1. `list_skills()` → discovers `research-assistant` skill
2. `load_skill("research-assistant")` → reads methodology
3. `run_skill_script("research-assistant", "search", {"query": "..."})` → executes search
4. `read_skill_resource("research-assistant", "citation-formats")` → formats citations

**Result**: The agent follows a documented research methodology rather than
improvising, producing consistent, high-quality results.

## Key Differentiators

| Without Skills | With Skills |
|----------------|-------------|
| Logic hardcoded in room tools | Portable methodology in SKILL.md |
| Updates require code changes | Update SKILL.md, all rooms benefit |
| Agent invents approach | Agent follows documented process |
| One-off implementations | Reusable across rooms |
| Scattered knowledge | Centralized skill library |

## Environment Variables

Configure global defaults:

```bash
# Default skill directories (comma-separated)
export SOLIPLEX_SKILLS_DIRECTORIES="/path/to/global/skills"

# Validate skill structure (default: true)
export SOLIPLEX_SKILLS_VALIDATE=true

# Discovery depth (default: 3)
export SOLIPLEX_SKILLS_MAX_DEPTH=3

# Disable specific tools
export SOLIPLEX_SKILLS_EXCLUDE_TOOLS="run_skill_script"
```

Room configs override these defaults.
