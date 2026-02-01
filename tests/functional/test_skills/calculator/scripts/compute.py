"""Simple compute script for testing.

pydantic-ai-skills expects a 'run' function that returns a string.
"""

import math


def run(ctx=None, args=None):
    """Execute a mathematical expression.

    Args:
        ctx: RunContext (optional)
        args: Dictionary with 'expression' key containing the math expression

    Returns:
        String result of the computation
    """
    if args is None:
        return "Error: No arguments provided"

    expression = args.get("expression", "")
    if not expression:
        return "Error: No expression provided"

    # Safe evaluation with math functions
    allowed_names = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "pi": math.pi,
        "e": math.e,
    }

    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)
    except Exception as e:
        return f"Error: {e}"
    else:
        return f"Result: {result}"
