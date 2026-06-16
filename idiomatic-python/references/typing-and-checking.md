# Typing & checking

Python is gradually typed: annotations are optional and not enforced at runtime —
but a **strict static checker** (`pyright`/`mypy --strict`) turns them into real
compile-time safety. This is the signature move of modern Python, the analogue of
TypeScript-for-JS: annotate everything, check strictly, and you recover most of
what a statically typed language gives you.

## Annotate every signature

```python
def parse_port(s: str) -> int | None:
    return int(s) if s.isdigit() else None

names: list[str] = []
config: dict[str, int] = {}
maybe: str | None = None
```

- Type **function parameters and return types** always; annotate variables where
  inference needs help. Local inference usually handles the rest.
- The payoff only materializes under a strict checker — annotations alone don't
  run. Run `pyright`/`mypy --strict` in CI and the editor.

## Modern typing syntax (3.10–3.12)

Use the current spellings; the old `typing.List`/`Optional`/`Union` forms are
legacy:

```python
list[int]            # not typing.List[int]
dict[str, int]
int | None           # not Optional[int]   (3.10+)
int | str            # not Union[int, str] (3.10+)

type Vector = list[float]          # PEP 695 type alias statement (3.12+)

def first[T](xs: list[T]) -> T | None:     # PEP 695 generics syntax (3.12+)
    return xs[0] if xs else None

class Stack[T]:                            # generic class, no TypeVar boilerplate
    def push(self, x: T) -> None: ...
```

(On 3.14, PEP 649 makes annotations lazily evaluated, so forward references mostly
"just work" without `from __future__ import annotations`.)

## Avoid `Any`; reach for `unknown`-style alternatives

`Any` silently disables checking — treat it as a bug. When you don't know a type:

- **A precise type** or a **union** (`int | str`).
- **`object`** when you truly accept anything but will narrow before use (Python's
  honest "top type"; unlike `Any`, it forces an `isinstance`/`match` check).
- **A generic** (`def f[T](x: T) -> T`) to thread the caller's type through.
- **A `Protocol`** to describe the shape you need (below).

Turn on `--strict` (mypy) / `"strict"` mode (pyright), and enable warnings for
implicit `Any`, untyped defs, and unreachable code.

## `Protocol` — structural typing (duck typing, checked)

A `Protocol` describes the *shape* a value must have; any class with matching
members conforms, without inheriting anything. This is composition-friendly
polymorphism — and it makes "duck typing" statically verifiable:

```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> str: ...

def render(item: Drawable) -> None:        # accepts ANY object with draw() -> str
    print(item.draw())

@runtime_checkable                          # only if you need isinstance() at runtime
class Sized(Protocol):
    def __len__(self) -> int: ...
```

Prefer `Protocol`s over abstract base classes when you only need a contract — they
don't force an inheritance relationship and work with types you don't own.

## The precise-typing toolkit

| Tool                          | Use for…                                                  |
|-------------------------------|-----------------------------------------------------------|
| `Literal["r", "w", "a"]`      | a fixed set of literal values (a lightweight enum)        |
| `TypedDict`                   | a dict with known string keys + value types (JSON shapes) |
| `NewType("UserId", str)`      | a distinct type over a primitive (no runtime cost)        |
| `Self`                        | methods returning their own (possibly subclass) type      |
| `Final` / `Final[int]`        | constants the checker forbids reassigning                 |
| `ClassVar[T]`                 | class-level (not per-instance) attributes                 |
| `@override` (3.12)            | assert a method actually overrides a base method          |
| `Callable[[int], str]`        | function-typed parameters                                 |
| `Iterable[T]` / `Sequence[T]` | accept the least specific collection you need             |

```python
from typing import Literal, TypedDict, NewType, Final

Mode = Literal["r", "w", "a"]
UserId = NewType("UserId", str)
MAX_RETRIES: Final = 3

class Movie(TypedDict):
    title: str
    year: int
```

Accept the **most general** type you can (`Iterable`, `Sequence`, `Mapping`) and
return the **most specific** (`list`, `dict`) — the Python version of "be liberal
in what you accept."

## Exhaustiveness with `assert_never`

The Python equivalent of TS's `never` trick. In a `match` (or if/elif) over a
closed union, end with `assert_never` — the checker errors if any case is
unhandled, so adding a variant lights up every switch:

```python
from typing import assert_never

def area(shape: Shape) -> float:
    match shape:
        case Circle(r):       return math.pi * r**2
        case Rectangle(w, h): return w * h
        case _:               assert_never(shape)   # ← static error if a case is missing
```

This gives you exhaustiveness over union-of-dataclasses ADTs (see
`data-modeling.md`) without a true sealed type — as long as the checker runs.

## Rules of thumb

- Annotate all signatures; run `pyright`/`mypy --strict` (and treat `Any` as a bug).
- Use modern syntax (`X | Y`, `list[int]`, `type`, `def f[T]`).
- `Protocol` for contracts; accept general types, return specific ones.
- `assert_never` to make unions exhaustive under the checker.
