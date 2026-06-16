---
name: idiomatic-python
description: >-
  Write, refactor, or review idiomatic, modern, typed Python (.py, .pyi,
  notebooks) — even a quick "write a Python script", and especially for AI/ML and
  data work where Python is the lingua franca. Steers toward type hints + a strict
  checker (pyright/mypy --strict), dataclasses/enums + `match` for data and
  ADT-style dispatch, EAFP error handling with specific exceptions and context
  managers, comprehensions/generators over manual loops, composition via
  `Protocol` over inheritance, and modern tooling (uv, ruff). Reach for it when
  modeling data, adding types, handling errors/resources, choosing dict vs
  dataclass, replacing loops or class hierarchies, or setting up a project.
  Targets Python 3.12–3.14. Counters untyped, `Any`-laden, Java-in-Python habits.
---

# Idiomatic Python

Modern Python is a multi-paradigm language that, written well, sits comfortably in
the type-driven family: **type hints + a strict checker** recover most static
safety, **dataclasses + `match`** give you product/sum types with exhaustiveness,
and comprehensions, generators, and `Protocol`s make it expression-oriented and
composable. Like JavaScript, Python doesn't *enforce* this by default — you opt
in — but `pyright`/`mypy --strict` + `ruff` get you most of the way.

The prime directive: **type it, model it, and let the checker and Zen guide you.**
Annotate everything and run a strict type checker; model data with dataclasses,
enums, and unions; handle errors the Pythonic EAFP way; reach for comprehensions,
the stdlib, and `Protocol`s before loops, reinvention, and class hierarchies.

The house style is literally written down — **PEP 20, the Zen of Python**:
*explicit is better than implicit; simple is better than complex; readability
counts; there should be one obvious way to do it.* When in doubt, `import this`.

> **Part of the `idiomatic-code` family** — the shared cross-language philosophy and the Rosetta Stone (porting + review) live there.
>
> Stack family: Python is the **gradually-typed** member, like JavaScript — you
> opt into the safety. With type hints + `pyright --strict` it reaches the
> type-driven core: union-of-dataclasses are sum types, `match` + `assert_never`
> gives exhaustiveness (the analogue of TS `never`), frozen dataclasses give
> immutability.

## Break the muscle memory (reflex → idiomatic)

When your instinct fires the left column, write the right column instead.

| Reflex (untyped / Java / C habit)                   | Idiomatic Python                                                     |
|-----------------------------------------------------|---------------------------------------------------------------------|
| No type hints / `Any` everywhere                    | type hints on all signatures + `pyright`/`mypy --strict`            |
| `dict`/tuple as an ad-hoc record                    | `@dataclass(frozen=True)` / `TypedDict` / pydantic                  |
| Mutable default arg — `def f(x=[])`                 | `def f(x=None): x = x if x is not None else []`                     |
| `for i in range(len(xs)): xs[i]`                    | `for x in xs` / `enumerate(xs)` / a comprehension                   |
| Manual loop building a list                         | list/dict/set **comprehension** or a generator                      |
| `except:` / broad `except Exception`               | catch **specific** exceptions; EAFP                                  |
| `type(x) == Foo`                                    | `isinstance(x, Foo)` — or `match`                                   |
| `"%s" % x` / `"{}".format(x)`                      | f-strings — `f"{x}"`                                                 |
| `os.path.join(...)` string paths                    | `pathlib.Path`                                                       |
| `open(...)` / `close()` by hand                     | `with` context manager                                              |
| Class hierarchy / Java-style OOP                    | functions + dataclasses + `Protocol` (structural typing)            |
| `print()` debugging                                 | `logging`                                                           |
| `from module import *`                              | explicit imports                                                    |
| Reinventing loops/grouping/counting                 | `itertools` / `functools` / `collections`                          |
| if/elif type-dispatch ladder                        | `match` + `assert_never` for exhaustiveness                         |
| pip + venv + setup.py juggling                      | **uv** + `pyproject.toml`                                            |
| Global mutable state                                | pass arguments, return values                                      |

If you genuinely need a class (stateful objects with behavior, framework base
classes, `__enter__`/`__exit__`), use one — `@dataclass` even removes the
boilerplate. Make it a decision, not a default.

## The creed

1. **Type everything; check strictly.** Annotate all signatures; run
   `pyright`/`mypy --strict` in CI. Gradual typing only pays if you're strict;
   treat `Any` as a TODO.
2. **Make illegal states unrepresentable.** `@dataclass(frozen=True)` for "all of",
   `Enum`/`Literal` and union-of-dataclasses for "one of", `NewType` for
   constrained primitives — then `match` with `assert_never`.
3. **EAFP, with specific exceptions.** "Easier to ask forgiveness than permission":
   try the operation, catch the precise exception. Never bare-`except`; manage
   resources with `with`.
4. **Immutable where practical.** Frozen dataclasses, tuples, `dataclasses.replace`;
   don't mutate arguments or shared state.
5. **Comprehensions & the stdlib over loops.** List/dict/set comprehensions and
   generators; reach for `itertools`/`functools`/`collections` before hand-rolling.
6. **Composition over inheritance.** `Protocol`s (structural typing) and small
   functions; shallow class trees.
7. **Readable and obvious.** Follow PEP 8 / the Zen; let `ruff` format and lint so
   style is automatic.

## Quick reach-for guide

| You need to…                              | Reach for…                                                       |
|-------------------------------------------|------------------------------------------------------------------|
| A data bundle                             | `@dataclass(frozen=True, slots=True)`                           |
| "One of N shapes" / a state              | union of dataclasses (`type S = A | B`) + `match` + `assert_never` |
| A fixed set of names                      | `Enum`, or `Literal["a", "b"]`                                   |
| Constrain a primitive (UserId)            | `NewType("UserId", str)` (+ a validating factory)              |
| Structured dict from JSON                 | `TypedDict`, or **pydantic** for validation                     |
| "Maybe absent"                            | `T | None` + a strict checker (handle the `None`)              |
| "Succeeds or fails"                       | raise a specific exception (EAFP); or a `Result`-style union    |
| Transform a collection                    | comprehension / generator / `map`+`filter` sparingly            |
| Add behavior to a contract               | a `Protocol` (structural), not a base class                     |
| Manage a resource                         | `with` / `@contextmanager`                                       |
| Concurrent I/O                            | `asyncio` + `TaskGroup` (structured concurrency)               |

## Reference files — read on demand

- **`references/typing-and-checking.md`** — type hints (modern `X | Y`, `list[int]`,
  `def f[T]()`, `type` aliases), `Any` avoidance, `pyright`/`mypy --strict`,
  `Protocol` (structural typing), `Literal`/`TypedDict`/`NewType`/`Self`/`Final`,
  and `assert_never` for exhaustiveness. *Read for any typed code — the signature
  move.*
- **`references/data-modeling.md`** — dataclasses (frozen/slots), `Enum`/`Literal`,
  union-of-dataclasses as ADTs, `NamedTuple`/`TypedDict`, pydantic/attrs,
  `NewType`, make-illegal-states-unrepresentable. *Read when modeling data.*
- **`references/match-and-idioms.md`** — structural pattern matching (`match`),
  exhaustiveness with `assert_never`, EAFP vs LBYL, `isinstance`, and the Pythonic
  baseline (f-strings, `pathlib`, `enumerate`/`zip`, truthiness, `is`/`==`). *Read
  for branching and everyday idioms.*
- **`references/functions-comprehensions-generators.md`** — comprehensions,
  generators (lazy), `itertools`/`functools`/`collections`, decorators, closures,
  keyword-only/positional-only args, the mutable-default footgun. *Read for data
  processing and function design.*
- **`references/errors-and-resources.md`** — exceptions (specific, custom classes,
  chaining `raise … from`, `ExceptionGroup`/`except*`), EAFP, context managers,
  `logging`. *Read for error handling and resources.*
- **`references/async-and-tooling.md`** — `asyncio`/`async`/`await`, `TaskGroup`
  (structured concurrency), no blocking in async; uv, ruff, pyright/mypy, pytest,
  `pyproject.toml`, and Python 3.13/3.14 (free-threading, JIT, t-strings). *Read
  for concurrency or project setup.*

## A taste

```python
import math
from dataclasses import dataclass
from typing import assert_never

@dataclass(frozen=True, slots=True)
class Circle:
    radius: float

@dataclass(frozen=True, slots=True)
class Rectangle:
    width: float
    height: float

type Shape = Circle | Rectangle          # PEP 695 type alias (3.12+)

def area(shape: Shape) -> float:
    match shape:
        case Circle(radius):
            return math.pi * radius**2
        case Rectangle(width, height):
            return width * height
        case _:
            assert_never(shape)          # pyright/mypy error if a case is missed
```

Typed, immutable, modeled as a sum type, matched exhaustively (the checker
proves it), no `Any`, no class hierarchy — and the union *is* the documentation.
That is the target for all Python here.
