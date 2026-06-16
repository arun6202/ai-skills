# Data modeling

Model data with dataclasses (products), unions of dataclasses (sums), and enums —
not bare dicts and tuples. Combined with a strict checker and `match`, this gives
Python the same "make illegal states unrepresentable" discipline as the
type-driven languages.

## Dataclasses — products without boilerplate

```python
from dataclasses import dataclass, replace

@dataclass(frozen=True, slots=True)
class Customer:
    name: str
    email: str
    since: date
```

One decorator gives you `__init__`, `__repr__`, `__eq__` (value equality), and
field ordering for pattern matching. Use the options deliberately:

- **`frozen=True`** — immutable instances (can't reassign fields); also makes them
  hashable. The default you want for value objects.
- **`slots=True`** — no per-instance `__dict__`; less memory, faster attribute
  access, and catches typo'd attributes. Good default.
- **"Change" without mutation** — `replace(customer, name="Ada")` returns a new
  instance (the copy-with operation).
- **Defaults** — give field defaults, but for mutable defaults use
  `field(default_factory=list)`, never `= []` (the shared-mutable footgun).

```python
from dataclasses import field

@dataclass(frozen=True)
class Order:
    id: str
    lines: tuple[Line, ...] = field(default_factory=tuple)   # immutable + safe default
```

Prefer a dataclass over a `dict`/`tuple` the moment data has a fixed shape — it's
typed, self-documenting, and tooling-friendly.

## Enums & Literals — closed sets of names

```python
from enum import Enum, auto

class Color(Enum):
    RED = auto()
    GREEN = auto()
    BLUE = auto()
```

- `Enum` for a named, iterable, type-safe set of constants (use `StrEnum`/`IntEnum`
  when the values must *be* strings/ints for serialization).
- `Literal["r", "w", "a"]` for a lightweight closed set inline in a signature, when
  you don't need a full enum class.
- Both are exhaustively matchable (with `assert_never`) — replace magic strings and
  integer flags with one of these.

## Algebraic data types: union of dataclasses + `match`

Python has no native sealed type, but a **union of dataclasses** is the idiomatic
sum type, and `match` + `assert_never` gives exhaustiveness under the checker (see
`match-and-idioms.md` and `typing-and-checking.md`):

```python
@dataclass(frozen=True)
class Loading: ...

@dataclass(frozen=True)
class Loaded:
    data: bytes

@dataclass(frozen=True)
class Failed:
    error: str

type RequestState = Loading | Loaded | Failed     # the sum type (3.12 alias)

def describe(state: RequestState) -> str:
    match state:
        case Loading():       return "loading"
        case Loaded(data):    return f"loaded {len(data)} bytes"
        case Failed(error):   return f"error: {error}"
        case _:               assert_never(state)
```

This is the F#-DU / Rust-enum / TS-discriminated-union equivalent: `data` is only
reachable in the `Loaded` case, and adding a variant breaks every non-exhaustive
`match` at type-check time.

## Make illegal states unrepresentable

```python
# ❌ illegal states representable: is_loading + data + error can all be set
@dataclass
class State:
    is_loading: bool
    data: bytes | None = None
    error: str | None = None

# ✅ exactly one state (the union above)
type State = Loading | Loaded | Failed
```

Same discipline as the rest of the family: model so bad combinations can't be
constructed, then never re-check them.

## NewType — constrained primitives

`NewType` makes a distinct type over a primitive (zero runtime cost) so a raw
`str` can't be passed where a validated id is expected:

```python
from typing import NewType

UserId = NewType("UserId", str)

def make_user_id(raw: str) -> UserId:        # the one validating gateway
    if not raw:
        raise ValueError("user id required")
    return UserId(raw)
```

Pair it with a validating factory ("parse, don't validate"). For richer
constrained values, a `frozen` dataclass with validation in `__post_init__` works
too.

## NamedTuple & TypedDict

- **`NamedTuple`** — an immutable, typed, lightweight record that's also a tuple
  (handy for fixed positional returns); a frozen dataclass is usually clearer for
  domain data.
- **`TypedDict`** — types the *keys and value types of a dict*, ideal for JSON
  payloads and **kwargs shapes where you must stay a dict:
  ```python
  class Movie(TypedDict):
      title: str
      year: int
  ```

## Validation at boundaries: pydantic / attrs

For data crossing a trust boundary (API requests, config, env, untrusted JSON),
reach for **pydantic** (runtime validation + parsing from a model, great error
messages, used across FastAPI etc.) or **attrs** (validators, converters). Use
plain dataclasses for internal domain types; validate-and-parse into them at the
edge. (This is the "parse, don't validate" boundary, like the F#/Rust skills'
constrained types.)

```python
from pydantic import BaseModel

class CreateUser(BaseModel):     # validates on construction from untrusted input
    name: str
    age: int
```

## Checklist

- [ ] Fixed-shape data → `@dataclass(frozen=True, slots=True)`, not dict/tuple.
- [ ] "One of N" → union of dataclasses + `match` + `assert_never`.
- [ ] Fixed name set → `Enum`/`StrEnum` or `Literal`.
- [ ] Constrained primitive → `NewType` (+ validating factory) or a frozen dataclass.
- [ ] Untrusted input → validate/parse with pydantic at the boundary.
- [ ] Mutable defaults → `field(default_factory=...)`, never `= []`/`= {}`.
