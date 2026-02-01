#!/usr/bin/env python3
"""Precise mathematical calculations.

Usage via skill tools:
    run_skill_script("math-solver", "scripts/calculate.py",
                     args={"operation": "factorial", "n": "23"})

Direct CLI usage:
    python calculate.py --operation factorial --n 23
    python calculate.py factorial 23  # legacy positional args
"""

import argparse
import math
import sys


def factorial(n: int) -> int:
    """Compute n factorial."""
    return math.factorial(n)


def fibonacci(n: int) -> int:
    """Compute nth Fibonacci number (0-indexed: fib(0)=0, fib(1)=1)."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def add(a: int, b: int) -> int:
    """Addition."""
    return a + b


def subtract(a: int, b: int) -> int:
    """Subtraction."""
    return a - b


def multiply(a: int, b: int) -> int:
    """Precise multiplication."""
    return a * b


def divide(a: int, b: int) -> float:
    """Division."""
    return a / b


def power(a: int, b: int) -> int:
    """Exponentiation."""
    return a ** b


def modexp(base: int, exp: int, mod: int) -> int:
    """Compute base^exp mod m."""
    return pow(base, exp, mod)


def gcd(a: int, b: int) -> int:
    """Greatest common divisor."""
    return math.gcd(a, b)


def lcm(a: int, b: int) -> int:
    """Least common multiple."""
    return abs(a * b) // math.gcd(a, b)


def prime_factors(n: int) -> list[int]:
    """Return prime factorization as list."""
    if n < 2:
        return []
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def is_prime(n: int) -> bool:
    """Check if n is prime."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Precise mathematical calculations")
    parser.add_argument("--operation", "-op", type=str, help="Operation to perform")
    parser.add_argument("--n", type=int, help="First number argument")
    parser.add_argument("--a", type=int, help="First number for two-arg operations")
    parser.add_argument("--b", type=int, help="Second number for two-arg operations")
    parser.add_argument("--base", type=int, help="Base for modexp")
    parser.add_argument("--exp", type=int, help="Exponent for modexp")
    parser.add_argument("--mod", type=int, help="Modulus for modexp")

    # Also support positional args for backward compatibility
    parser.add_argument("positional", nargs="*", help="Positional args: operation [args...]")

    return parser.parse_args()


def main():
    args = parse_args()

    # Determine operation and arguments
    if args.operation:
        op = args.operation.lower()
    elif args.positional:
        op = args.positional[0].lower()
    else:
        print("Usage: calculate.py --operation <op> [--n N] [--a A] [--b B]")
        print("   or: calculate.py <operation> <args...>")
        print("Operations: add, subtract, multiply, divide, power, factorial, fibonacci, modexp, gcd, lcm, prime_factors, is_prime")
        sys.exit(1)

    try:
        if op == "add":
            if args.a is not None and args.b is not None:
                a, b = args.a, args.b
            else:
                a, b = int(args.positional[1]), int(args.positional[2])
            result = add(a, b)
            print(f"{a} + {b} = {result}")

        elif op == "subtract":
            if args.a is not None and args.b is not None:
                a, b = args.a, args.b
            else:
                a, b = int(args.positional[1]), int(args.positional[2])
            result = subtract(a, b)
            print(f"{a} - {b} = {result}")

        elif op == "divide":
            if args.a is not None and args.b is not None:
                a, b = args.a, args.b
            else:
                a, b = int(args.positional[1]), int(args.positional[2])
            result = divide(a, b)
            print(f"{a} / {b} = {result}")

        elif op == "power":
            if args.a is not None and args.b is not None:
                a, b = args.a, args.b
            else:
                a, b = int(args.positional[1]), int(args.positional[2])
            result = power(a, b)
            print(f"{a}^{b} = {result}")

        elif op == "factorial":
            n = args.n if args.n is not None else int(args.positional[1])
            result = factorial(n)
            print(f"{n}! = {result}")

        elif op == "fibonacci":
            n = args.n if args.n is not None else int(args.positional[1])
            result = fibonacci(n)
            print(f"fib({n}) = {result}")

        elif op == "multiply":
            if args.a is not None and args.b is not None:
                a, b = args.a, args.b
            else:
                a, b = int(args.positional[1]), int(args.positional[2])
            result = multiply(a, b)
            print(f"{a} * {b} = {result}")

        elif op == "modexp":
            if args.base is not None and args.exp is not None and args.mod is not None:
                base, exp, mod = args.base, args.exp, args.mod
            else:
                base = int(args.positional[1])
                exp = int(args.positional[2])
                mod = int(args.positional[3])
            result = modexp(base, exp, mod)
            print(f"{base}^{exp} mod {mod} = {result}")

        elif op == "gcd":
            if args.a is not None and args.b is not None:
                a, b = args.a, args.b
            else:
                a, b = int(args.positional[1]), int(args.positional[2])
            result = gcd(a, b)
            print(f"gcd({a}, {b}) = {result}")

        elif op == "lcm":
            if args.a is not None and args.b is not None:
                a, b = args.a, args.b
            else:
                a, b = int(args.positional[1]), int(args.positional[2])
            result = lcm(a, b)
            print(f"lcm({a}, {b}) = {result}")

        elif op == "prime_factors":
            n = args.n if args.n is not None else int(args.positional[1])
            factors = prime_factors(n)
            print(f"prime_factors({n}) = {factors}")

        elif op == "is_prime":
            n = args.n if args.n is not None else int(args.positional[1])
            result = is_prime(n)
            print(f"is_prime({n}) = {result}")

        else:
            print(f"Unknown operation: {op}")
            sys.exit(1)

    except (IndexError, ValueError, TypeError) as e:
        print(f"Error: {e}")
        print(f"Operation '{op}' requires appropriate arguments")
        sys.exit(1)


if __name__ == "__main__":
    main()
