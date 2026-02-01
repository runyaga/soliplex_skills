# Python Style Guide

## Formatting

- Use `ruff` for formatting and linting
- Line length: 79 characters (88 for Black-formatted projects)
- Indentation: 4 spaces, no tabs
- Trailing commas in multi-line structures

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Module | snake_case | `my_module.py` |
| Class | PascalCase | `MyClass` |
| Function | snake_case | `my_function()` |
| Variable | snake_case | `my_variable` |
| Constant | UPPER_SNAKE | `MAX_SIZE` |
| Private | _prefix | `_internal_method()` |

## Imports

```python
# Standard library
import os
import sys

# Third-party
import pydantic
import pytest

# Local
from myproject import utils
```

- One import per line (use `isort --force-single-line`)
- Group: stdlib, third-party, local (blank line between)

## Type Hints

```python
# Required for public APIs
def process_data(items: list[str], max_count: int = 10) -> dict[str, int]:
    ...

# Use | for unions (Python 3.10+)
def find(value: str | int) -> Result | None:
    ...
```

## Docstrings

```python
def calculate_score(items: list[Item], weights: dict[str, float]) -> float:
    """Calculate weighted score from items.

    Args:
        items: List of items to score
        weights: Mapping of item type to weight multiplier

    Returns:
        Total weighted score

    Raises:
        ValueError: If weights contains negative values
    """
```

## Error Handling

```python
# Good: Specific exceptions
try:
    result = parse_config(path)
except FileNotFoundError:
    log.warning("Config not found, using defaults")
    result = default_config()
except json.JSONDecodeError as e:
    raise ConfigError(f"Invalid JSON in {path}") from e

# Bad: Bare except
try:
    result = parse_config(path)
except:  # Never do this
    pass
```

## Async Guidelines

- Prefer `async def` for I/O-bound operations
- Use `asyncio.gather()` for concurrent operations
- Avoid mixing sync and async code
