# Contributing to soliplex-skills

Thank you for your interest in contributing to soliplex-skills!

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Clone and Install

```bash
git clone https://github.com/soliplex/soliplex_skills.git
cd soliplex_skills
uv sync
```

### Optional: Install Soliplex

For full integration testing:

```bash
git clone https://github.com/soliplex/soliplex.git ../soliplex
uv pip install -e ../soliplex
```

## Code Quality

### Linting

We use [ruff](https://github.com/astral-sh/ruff) for linting and formatting.

```bash
# Check for issues
uv run ruff check src tests

# Auto-fix issues
uv run ruff check --fix src tests

# Format code
uv run ruff format src tests
```

### Type Hints

All code must have type hints. We follow these conventions:

```python
from __future__ import annotations

def my_function(
    config: SkillsToolConfig,
    skill_name: str,
    args: dict[str, Any] | None = None,
) -> str:
    ...
```

### Docstrings

All public APIs must have docstrings:

```python
async def load_skill(
    tool_config: SkillsToolConfig,
    skill_name: str,
) -> str:
    """Load complete instructions for a specific skill.

    Args:
        tool_config: Skills configuration with directories.
        skill_name: Exact name from your available skills list.
            Must match exactly (e.g., "data-analysis" not "data analysis").

    Returns:
        Structured documentation containing skill instructions,
        available resources, and scripts.

    Raises:
        SkillNotFoundError: If skill_name doesn't exist.
    """
```

## Testing

### Run All Tests

```bash
uv run pytest
```

### Run with Coverage

```bash
uv run pytest --cov=soliplex_skills --cov-report=html
open htmlcov/index.html
```

### Run Specific Tests

```bash
# Unit tests only
uv run pytest tests/unit

# Functional tests only
uv run pytest tests/functional

# Specific test file
uv run pytest tests/unit/test_config.py

# Specific test
uv run pytest tests/unit/test_config.py::TestSkillsToolConfig::test_default_creation
```

### Coverage Requirements

- Minimum coverage: 80% (enforced by CI)
- Target coverage: 95%

## Project Structure

```
soliplex_skills/
├── src/soliplex_skills/
│   ├── __init__.py          # Public exports
│   ├── config.py            # Pydantic config models
│   ├── adapter.py           # Core adapter with caching
│   ├── tools.py             # Soliplex-compatible tools
│   ├── exceptions.py        # Exception hierarchy
│   └── introspection/       # Cross-room tools
│       ├── __init__.py
│       ├── config.py
│       └── tools.py
├── tests/
│   ├── unit/                # Unit tests (mocked)
│   └── functional/          # Integration tests (real skills)
└── example/
    ├── skills/              # Sample skills
    └── rooms/               # Sample room configs
```

## Making Changes

### Branch Naming

- `feat/description` - New features
- `fix/description` - Bug fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation
- `test/description` - Test improvements

### Commit Messages

Follow conventional commits:

```
feat(config): add support for YAML list format

fix(adapter): handle empty directories gracefully

refactor(tools): simplify error handling

docs: update README with examples

test: add per-room configuration tests
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure all tests pass: `uv run pytest`
4. Ensure linting passes: `uv run ruff check src tests`
5. Update documentation if needed
6. Submit PR with clear description

### PR Template

```markdown
## Summary
Brief description of changes.

## Changes
- **Component**: What changed

## Test Plan
- [x] Unit tests added/updated
- [x] Functional tests added/updated
- [x] Manual testing performed

## Checklist
- [ ] Tests pass locally
- [ ] Ruff passes
- [ ] Documentation updated
```

## Architecture Guidelines

### Pydantic-First Design

Always use native Pydantic types:

```python
# Good
directories: tuple[pathlib.Path, ...]
exclude_tools: frozenset[str]

# Bad
directories: str  # Then parse with .split(",")
```

### Error Handling

Return user-friendly strings from tools (not exceptions):

```python
async def load_skill(tool_config, skill_name):
    try:
        # ... implementation
    except SkillNotFoundError as e:
        return f"Error: {e}"
```

### Async by Default

All tool functions should be async:

```python
async def list_skills(tool_config: SkillsToolConfig) -> dict[str, str]:
    ...
```

### Thread Safety

Use async locks for shared state:

```python
_cache_lock = asyncio.Lock()

async def _get_toolset(config):
    async with _cache_lock:
        # ... cache access
```

## Getting Help

- **Issues**: https://github.com/soliplex/soliplex_skills/issues
- **Discussions**: https://github.com/soliplex/soliplex_skills/discussions

## Code of Conduct

Be respectful and constructive. We're all here to build something useful.
