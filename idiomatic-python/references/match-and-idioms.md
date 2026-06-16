# `match` & everyday idioms

Structural pattern matching (`match`, Python 3.10+) decomposes and branches on
data; combined with `assert_never` it gives exhaustiveness. Plus the Pythonic
baseline — the small idioms that separate readable Python from transliterated
Java/C.

## `match` — structural pattern matching

```python
match command.split():
    case ["go", direction]:
        move(direction)
    case ["drop", *items]:                 # capture the rest
        drop(items)
    case ["quit"]:
        quit()
    case _:
        print("unknown")
```

Patterns include:

- **Sequence patterns** — `[a, b]`, `[first, *rest]`.
- **Mapping patterns** — `{"type": "circle", "radius": r}` (matches dict keys).
- **Class patterns** — `Circle(radius)` (positional, via `__match_args__` —
  dataclasses provide it) or `Circle(radius=r)` (by keyword).
- **Capture / wildcard** — bind a name, or `_` to ignore.
- **OR patterns** — `case 1 | 2 | 3:`.
- **Guards** — `case Point(x, y) if x == y:`.
- **Literal / value** — `case 200:`, `case Color.RED:`.

```python
def area(shape: Shape) -> float:
    match shape:
        case Circle(radius):          return math.pi * radius**2
        case Rectangle(width, height): return width * height
        case _:                       assert_never(shape)   # exhaustiveness
```

Use `match` for multi-case dispatch over unions/shapes; it beats `if/elif/isinstance`
ladders. Keep `assert_never` on the wildcard so missing a case is a type error (see
`typing-and-checking.md`).

## EAFP over LBYL

Pythonic error handling is **EAFP** — "easier to ask forgiveness than permission":
attempt the operation and catch the specific exception, rather than pre-checking
("look before you leap"). It's clearer and avoids time-of-check/time-of-use races:

```python
# ✅ EAFP
try:
    value = config["timeout"]
except KeyError:
    value = DEFAULT_TIMEOUT

# ❌ LBYL — racy and noisier
if "timeout" in config:
    value = config["timeout"]
else:
    value = DEFAULT_TIMEOUT
```

(For dicts specifically, `config.get("timeout", DEFAULT)` is even cleaner — prefer
the built-in when it exists.) See `errors-and-resources.md` for the full error
story.

## `isinstance`, not `type(x) ==`

```python
if isinstance(x, str): ...            # ✅ respects subclasses
if isinstance(x, (int, float)): ...   # ✅ multiple types
if type(x) == str: ...                # ❌ brittle, ignores subclassing
```

For dispatch over several types, prefer `match` with class patterns over
`isinstance` chains.

## `is` vs `==`

- `==` compares **value**; `is` compares **identity** (same object).
- Use `is` only for singletons: `x is None`, `x is True`/`x is False` (but usually
  just `if x:`), sentinels. Never `== None`.

## Truthiness

Lean on truthiness instead of explicit comparisons:

```python
if items:            # ✅ empty list/dict/str/None are all falsy
if not name:         # ✅
if len(items) > 0:   # ❌ unnecessary
if items != []:      # ❌
```

Caveat: when `0` / `""` / `False` are *valid* values you must distinguish from
"absent", check `is None` explicitly rather than truthiness.

## f-strings for formatting

```python
msg = f"Hello {name}, you have {count} item{'s' if count != 1 else ''}"
f"{value:.2f}"           # format spec
f"{x=}"                  # debug: prints "x=<value>"
```

Use f-strings, not `%` or `str.format()`. (On 3.14, **t-strings** `t"..."` return a
`Template` for *safe* interpolation into SQL/HTML/shell — reach for those when
building strings that need escaping.)

## `pathlib`, not `os.path`

```python
from pathlib import Path

config = Path("config") / "app.toml"      # / operator joins
text = config.read_text(encoding="utf-8")
for py in Path("src").rglob("*.py"): ...
if config.exists(): ...
```

`pathlib.Path` replaces `os.path.join`/`os.listdir`/`open` string-munging with a
clean object API.

## Iterate Pythonically

```python
for x in items: ...                       # not range(len(items))
for i, x in enumerate(items): ...         # index + value
for a, b in zip(xs, ys, strict=True): ... # parallel (strict= catches length bugs)
for key, value in d.items(): ...          # dict pairs
```

Never `for i in range(len(items)): items[i]` — iterate the object directly; use
`enumerate`/`zip`/`.items()` when you need indices/pairs.

## Other baseline idioms

```python
a, b = b, a                       # swap (tuple packing)
first, *rest = sequence           # unpacking
x = a or default                  # fall back on falsy (careful with valid 0/"")
value = d.get(key, fallback)      # dict default
text = ", ".join(parts)           # join, don't += in a loop
with suppress(FileNotFoundError): # contextlib: ignore a specific exception
    path.unlink()
```

## Rules of thumb

- `match` + `assert_never` for multi-case dispatch; `isinstance` (not `type==`) for
  single checks.
- EAFP with specific exceptions; `is None` for None; truthiness for emptiness.
- f-strings, `pathlib`, `enumerate`/`zip`/`.items()` — the everyday baseline.
