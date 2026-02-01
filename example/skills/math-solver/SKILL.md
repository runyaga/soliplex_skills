---
name: math-solver
description: Precise mathematical calculations using Python - factorials, fibonacci, modular arithmetic, and more
---

# Math Solver

Provides precise mathematical calculations that require exact computation rather than estimation.

## When to Use This Skill

Use this skill when you need **exact** answers for:
- Basic arithmetic (add, subtract, multiply, divide, power)
- Factorials (n!)
- Fibonacci numbers
- Modular exponentiation (a^b mod m)
- Prime factorization
- GCD/LCM calculations

## Important

**DO NOT attempt to calculate these yourself.** Use the `calculate.py` script to get precise answers. Mental math and estimation will produce incorrect results for these operations.

**Return results in plain text, no LaTeX or markup formatting.**

## Scripts

### calculate.py

Performs precise mathematical calculations.

**Usage:**
```
calculate.py <operation> <args...>
```

**Operations:**

| Operation | Args | Example | Description |
|-----------|------|---------|-------------|
| `add` | a b | `add 123 456` | Addition |
| `subtract` | a b | `subtract 100 37` | Subtraction |
| `multiply` | a b | `multiply 8734 9821` | Multiplication |
| `divide` | a b | `divide 100 7` | Division |
| `power` | a b | `power 2 10` | Exponentiation |
| `factorial` | n | `factorial 23` | Compute n! |
| `fibonacci` | n | `fibonacci 47` | Compute nth Fibonacci number |
| `modexp` | base exp mod | `modexp 7 23 13` | Compute base^exp mod m |
| `gcd` | a b | `gcd 48 18` | Greatest common divisor |
| `lcm` | a b | `lcm 12 18` | Least common multiple |
| `prime_factors` | n | `prime_factors 84` | Prime factorization |
| `is_prime` | n | `is_prime 97` | Check if prime |

## Example Workflow

User: "What is 23 factorial?"

1. Load this skill
2. Run: `calculate.py factorial 23`
3. Return the exact result: 25852016738884976640000
