# Agent Skills Documentation

LLM-agnostic documentation for available skills and tool usage.

## Skill Architecture

This project provides skills in `example/skills/`. Each skill has:
- `SKILL.md` - Entry point with activation triggers and usage
- `scripts/` - Executable Python scripts
- `references/` - Detailed documentation (optional)

**Crucial:** Before using a skill, **read** `example/skills/<skill_name>/SKILL.md` for:
- Strict rules (e.g., Math Solver forbids LLM calculation)
- Required scripts and arguments
- Methodologies and workflows

## Available Skills

| Skill | Description |
|-------|-------------|
| `math-solver` | Precise Python-based calculation (factorials, fibonacci, etc.) |
| `soliplex-api` | Soliplex server introspection and API interaction |
| `research-assistant` | Academic research with citation support |

## Using Skills

Skills are invoked via `run_skill_script()`:

```python
run_skill_script("<skill_name>", "scripts/<script>.py",
                 args={"arg1": "value1", "arg2": "value2"})
```

### Example: math-solver

```python
run_skill_script("math-solver", "scripts/calculate.py",
                 args={"operation": "factorial", "n": "23"})
```

### Example: soliplex-api

```python
# List rooms
run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                 args={"command": "list_rooms"})

# Query a room
run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                 args={"command": "ask", "room_id": "gpt-20b",
                       "query": "Calculate factorial(5)"})

# JSON output for structured parsing
run_skill_script("soliplex-api", "scripts/soliplex_client.py",
                 args={"command": "list_rooms", "format": "json"})
```

## Skill Reference

For detailed skill documentation, read each skill's SKILL.md:
- `example/skills/math-solver/SKILL.md`
- `example/skills/soliplex-api/SKILL.md`
- `example/skills/research-assistant/SKILL.md`
