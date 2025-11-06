# SymPy Pipe

This package provides a subset of the [SymPy](https://www.sympy.org/) expression manipulation functionality as pipes (using the [Pipe package](https://github.com/JulienPalard/Pipe)).
This facilitates their usage (especially when doing interactive manipulation in Jupyter).
They all act on single expressions or, most useful, on iterables of expressions (returning a respective generator).

The pipes have the same interface as the original SymPy functions/methods, with the exception of the first parameter being the expression or expression iterable to work on (filled by the `|` operator).

## Examples

All examples depend on the following initialization code:

```python
from sympy import Symbol
x = Symbol("x")
y = Symbol("y")
```

### `simplify`

```python
from sympy_pipes import simplify
x + x | simplify
[x + x, 2 * x + x] | simplify
```

### `subs`

```python
from sympy_pipes import subs
x | subs(x, y)
[x, 2 * x] | subs({x: y})
```

### `limit`

```python
from sympy_pipes import limit
x**2 | limit(x, 1)
[x**2, 2 * x] | limit(x, y)
```

### `diff`

```python
from sympy_pipes import diff
x**2 | diff(x)
[x**2, 2 * x] | diff(x, 2)
```

### `integrate`

```python
from sympy_pipes import integrate
x | integrate(x)
[x, 2 * x] | integrate((x, 1, 2))
```

### `display`

To pretty print iterables of expressions in Jupyter environments. **This function is only available, if IPython is installed in the environment!**
The `display` pipe returns its input, so  it can be used to output intermediate results.

```python
from sympy_pipes import display, subs
x | display | subs(x, y) | display
[x, 2 * x] | display | subs(x, y) | display
```

## License

The code is published under the terms of the [MIT License](LICENSE).
