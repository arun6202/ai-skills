# Functions, comprehensions & generators

Transform data with comprehensions and generators instead of manual loops, lean on
the standard library (`itertools`/`functools`/`collections`) before hand-rolling,
and design functions with clear, typed, well-defaulted parameters.

## Comprehensions over manual loops

Most "build a list/dict/set in a loop" is a comprehension — shorter, clearer, and
often faster:

```python
# imperative
names = []
for u in users:
    if u.active:
        names.append(u.name)

# idiomatic
names = [u.name for u in users if u.active]

squares = {x: x * x for x in range(10)}        # dict comprehension
unique = {p.country for p in people}            # set comprehension
```

- Keep comprehensions to **one transform + optional filter**. If it needs nesting,
  multiple conditions, or a side effect, use a `for` loop — readability wins.
- Don't use a comprehension purely for side effects (`[print(x) for x in xs]`) —
  use a plain `for` loop.

## Generators — lazy sequences

A **generator expression** (parentheses instead of brackets) or a `yield` function
produces values lazily — no intermediate list, works on infinite/huge streams,
and is memory-light:

```python
total = sum(item.price for item in items)       # gen expr: no temporary list
first_big = next((x for x in stream if x > 1000), None)

def read_lines(path: Path) -> Iterator[str]:    # generator function
    with path.open() as f:
        for line in f:
            yield line.rstrip("\n")
```

Prefer a generator when you only iterate once, the data is large, or you want
streaming/short-circuiting (`any`, `next`, `sum`). Materialize with `list(...)`
only when you need to index or reuse it.

## The standard-library toolkit

Reach for these before writing loops by hand:

| Need                              | Use                                                    |
|-----------------------------------|--------------------------------------------------------|
| count occurrences                 | `collections.Counter`                                  |
| group / multimap                  | `collections.defaultdict(list)`                        |
| group consecutive / by key        | `itertools.groupby` (sort first)                       |
| flatten / chain                   | `itertools.chain.from_iterable`                        |
| running pairs / windows           | `itertools.pairwise`                                   |
| cartesian / combinations          | `itertools.product` / `combinations`                   |
| take / slice an iterator          | `itertools.islice`                                     |
| memoize                           | `functools.cache` / `lru_cache`                        |
| reduce                            | `functools.reduce` (sparingly; prefer `sum`/loops)     |
| partial application               | `functools.partial`                                    |
| fixed-size immutable record       | `collections.namedtuple` (or a dataclass)              |
| double-ended queue                | `collections.deque`                                    |

```python
from collections import Counter, defaultdict
word_counts = Counter(text.split())
by_role: dict[str, list[User]] = defaultdict(list)
for u in users:
    by_role[u.role].append(u)
```

`map`/`filter` exist but a comprehension or generator expression is usually more
readable; reserve `map` for passing an existing named function
(`map(str.strip, lines)`).

## Function design

```python
def connect(
    host: str,
    port: int = 443,
    *,                          # everything after * is keyword-only
    timeout: float = 30.0,
    retries: int = 3,
) -> Connection: ...

connect("example.com", timeout=60)     # callers must name timeout/retries
```

- **Type every parameter and the return.**
- **Keyword-only args** (after `*`) for options/booleans — callers read clearly and
  you can reorder safely. **Positional-only** (`/`) for obvious leading args.
- Prefer **named/default arguments** over overloads or builder objects.
- Keep functions small and single-purpose; return values rather than mutating
  arguments.

## The mutable-default footgun

A default argument is evaluated **once**, at definition — a mutable default is
shared across all calls:

```python
def add(item, items=[]):        # ❌ the same list is reused every call!
    items.append(item)
    return items

def add(item, items=None):      # ✅ idiomatic fix
    items = [] if items is None else items
    items.append(item)
    return items
```

Always use `None` as the sentinel for mutable defaults (and `field(default_factory=...)`
in dataclasses).

## Closures & higher-order functions

```python
def make_adder(n: int) -> Callable[[int], int]:
    def add(x: int) -> int:
        return x + n            # captures n
    return add

add5 = make_adder(5)
```

Functions are first-class — pass them as arguments, return them, store them. Use
closures for small stateful behavior; `functools.partial` to pre-bind arguments.

## Decorators

```python
import functools

def timed[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(fn)                       # preserve name/docstring/signature
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        ...
        return fn(*args, **kwargs)
    return wrapper
```

Use decorators for cross-cutting concerns (caching, timing, registration,
validation). Always `@functools.wraps` the inner function; type with `ParamSpec`
(`[**P, R]`) so the wrapped signature is preserved. Use existing decorators
(`@cache`, `@dataclass`, `@property`, `@contextmanager`) liberally; write your own
sparingly.

## Rules of thumb

- Comprehension/generator over manual list-building; generator when lazy/large.
- `itertools`/`functools`/`collections` before hand-rolled loops.
- Type params; keyword-only options; never a mutable default (`=[]`/`={}`).
- `@functools.wraps` + `ParamSpec` on decorators.
