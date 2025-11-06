"""
This module provides Pipe-definitions (of the pipe package for infix programming by Julien Palard) for usage with SymPy (the symbolic computation library).

As is the nature of pipes, this is mainly aimed on working with iterables of Sympy expressions.
"""

__all__ = ["subs"]

import sympy as sp
from sympy import Basic, Expr, Symbol
from pipe import Pipe
from typing import Mapping, Iterable, Any, Literal


@Pipe
def subs(
    input: Iterable[Basic] | Basic,
    arg1: Mapping[Basic | complex, Basic | complex]
    | Iterable[tuple[Basic | complex, Basic | complex]]
    | Basic
    | complex,
    arg2: Basic | complex | None = None,
    **kwargs: Any,
) -> Iterable[Basic] | Basic:
    """Substitute in an expression or iterable of expressions. If an iterable is piped in, a generator is returned."""
    if isinstance(input, Basic):
        return input.subs(arg1, arg2, **kwargs)

    return (expr.subs(arg1, arg2, **kwargs) for expr in input)


@Pipe
def simplify(
    input: Iterable[Basic] | Basic,
    **kwargs: Any,
) -> Iterable[Basic] | Basic:
    """Simplify an expression or iterable of expressions. If an iterable is piped in, a generator is returned."""
    if isinstance(input, Basic):
        return input.simplify(**kwargs)

    return (expr.simplify(**kwargs) for expr in input)


@Pipe
def limit(
    input: Iterable[Expr] | Expr,
    x: Symbol,
    xlim: Expr | complex,
    dir: Literal["+", "-"] = "+",
) -> Iterable[Basic] | Basic:
    """Compute limits of an expression or iterable of expressions. If an iterable is piped in, a generator is returned."""
    if isinstance(input, Expr):
        return input.limit(x, xlim, dir)

    return (expr.limit(x, xlim, dir) for expr in input)


@Pipe
def diff(
    input: Iterable[Expr] | Expr,
    *symbols: Symbol,
    **kwargs: Any,
) -> Iterable[Basic] | Basic:
    """Differentiate an expression or iterable of expressions. If an iterable is piped in, a generator is returned."""
    if isinstance(input, Expr):
        return sp.diff(input, *symbols, **kwargs)

    return (sp.diff(item, *symbols, **kwargs) for item in input)


@Pipe
def integrate(
    input: Iterable[Expr] | Expr,
    *symbols: Symbol | tuple[Symbol, Expr] | tuple[Symbol, Expr, Expr],
    **kwargs: Any,
) -> Iterable[Basic] | Basic:
    """Integrate an expression or iterable of expressions. If an iterable is piped in, a generator is returned."""
    if isinstance(input, Expr):
        return sp.integrate(input, *symbols, **kwargs)

    return (sp.integrate(item, *symbols, **kwargs) for item in input)


@Pipe
def display(
    input: Iterable[Basic] | Basic,
) -> Iterable[Basic] | Basic:
    """Display an expression or iterable of expressions.
    This functions returns or yields the original provided input to allow for chaining (displaying intermediate results)."""
    import IPython.display

    if isinstance(input, Basic):
        IPython.display.display(input)
        return input

    def _gen():
        for item in input:
            IPython.display.display(item)
            yield item

    return _gen()
