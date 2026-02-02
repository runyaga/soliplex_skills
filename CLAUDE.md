# Soliplex Skills Project

Adapter for pydantic-ai-skills to interact with Soliplex installations.

## Development Commands

- **Install:** `uv sync`
- **Test:** `uv run pytest`
- **Lint:** `uv run ruff check .`
- **Run Server:** `uv run soliplex-cli serve example/installation.yaml --no-auth-mode`

## Tooling & Skills

Skill documentation and `run_skill_script` usage is in `AGENTS.md`.

**Instruction:** If a task requires tools or scripts, read `AGENTS.md` first to understand correct usage and arguments.

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
