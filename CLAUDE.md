# Soliplex Skills Project

Adapter for pydantic-ai-skills to interact with Soliplex installations.

## Development Commands

- **Install:** `uv sync`
- **Test:** `uv run pytest`
- **Lint:** `uv run ruff check .`
- **Run Server:** `uv run soliplex-cli serve example/installation.yaml --no-auth-mode`

## Skill Architecture

This project contains the core adapter (`src/`) and example skills (`example/skills/`).

**Crucial:** When working with a specific skill, **read** `example/skills/<skill_name>/SKILL.md` first. These files contain:
- Strict rules (e.g., Math Solver forbids LLM calculation)
- Required scripts and arguments
- Methodologies and workflows

## Available Skills

| Skill | Description |
|-------|-------------|
| `math-solver` | Precise Python-based calculation (factorials, fibonacci, etc.) |
| `soliplex-api` | Soliplex server introspection and API interaction |
| `research-assistant` | Academic research with citation support |

## Project Structure

```
soliplex_skills/
├── src/soliplex_skills/     # Main adapter package
├── example/
│   ├── installation.yaml    # Soliplex installation config
│   ├── rooms/               # Room configurations
│   └── skills/              # Skill definitions (read SKILL.md in each)
└── tests/                   # Unit and integration tests
```
