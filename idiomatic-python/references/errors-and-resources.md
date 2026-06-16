# Errors & resources

Python error handling is exception-based and **EAFP** — try the operation, catch
the *specific* exception. The cardinal sins are the bare `except:` and the
swallowed error. Resources (files, locks, connections) are managed with context
managers (`with`), never by hand.

## Catch specific exceptions — never bare `except`

```python
try:
    data = json.loads(text)
except json.JSONDecodeError as exc:
    logger.warning("bad JSON: %s", exc)
    raise ConfigError("config is not valid JSON") from exc
```

- **Catch the narrowest exception** that can actually occur (`KeyError`,
  `ValueError`, `FileNotFoundError`), not `Exception` and never bare `except:`
  (which also swallows `KeyboardInterrupt`/`SystemExit`).
- **Never swallow silently.** An empty `except: pass` hides bugs. If an error is
  genuinely ignorable, say so explicitly with `contextlib.suppress`:
  ```python
  from contextlib import suppress
  with suppress(FileNotFoundError):
      path.unlink()
  ```
- Keep the `try` block **small** — wrap only the line(s) that can raise, so you
  don't accidentally catch errors from unrelated code.

## Custom exceptions & chaining

Define a small exception hierarchy for your domain so callers can catch at the
right granularity:

```python
class AppError(Exception):
    """Base for all application errors."""

class ConfigError(AppError): ...
class ValidationError(AppError):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"{field}: {message}")
        self.field = field
```

- Subclass `Exception` (not `BaseException`); give a common base so callers can
  `except AppError`.
- **Preserve the cause** with `raise NewError(...) from original` — the traceback
  shows the chain. Use `from None` only to deliberately suppress a noisy cause.
- Raise exceptions with **informative messages**; attach structured data as
  attributes when callers need it.

## EAFP, and when to prefer a built-in

```python
# EAFP
try:
    return cache[key]
except KeyError:
    value = cache[key] = compute(key)
    return value

# but prefer the built-in when one exists:
value = config.get("timeout", DEFAULT)        # cleaner than try/except KeyError
value = getattr(obj, "name", "anonymous")
```

EAFP is the default; reach for `.get()`/`getattr()`/`in` when the built-in
expresses the intent more directly.

## `ExceptionGroup` / `except*` (3.11+)

When multiple errors can happen together (concurrent tasks, batch operations),
raise an `ExceptionGroup` and handle members with `except*`:

```python
try:
    async with asyncio.TaskGroup() as tg:    # collects child exceptions into a group
        tg.create_task(a())
        tg.create_task(b())
except* ValueError as eg:
    for exc in eg.exceptions:
        handle(exc)
except* ConnectionError as eg:
    ...
```

`except*` matches each exception type *within* the group, so you handle several
failure kinds from concurrent work cleanly (see `async-and-tooling.md`).

## "Errors as values" when it fits

EAFP/exceptions are Pythonic and the default. But for *expected* domain outcomes a
caller must branch on, a `Result`-style union of dataclasses + `match` (see
`data-modeling.md`) can be clearer than control-flow-by-exception — useful for
validation pipelines and at API boundaries. Don't force it everywhere; reserve it
for where the failure is a normal, branchable result rather than an exceptional
condition.

## Resources: always `with`

A context manager guarantees cleanup (close/release/rollback) even on exception —
never open a resource without one:

```python
with path.open(encoding="utf-8") as f:        # closed automatically
    text = f.read()

with open(a) as fa, open(b) as fb:            # multiple resources
    ...

with sqlite3.connect(db) as conn:             # commits/rolls back per the CM
    conn.execute(...)
```

Write your own context managers with `contextlib.contextmanager` (a generator that
`yield`s once) or `__enter__`/`__exit__`:

```python
from contextlib import contextmanager

@contextmanager
def timer(label: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        logger.info("%s took %.3fs", label, time.perf_counter() - start)

with timer("load"):
    load_everything()
```

Use `try/finally` directly only when no context manager fits; `contextlib.ExitStack`
manages a dynamic number of resources.

## Logging, not `print`

```python
import logging
logger = logging.getLogger(__name__)          # module-level, named by module

logger.info("loaded %d rows from %s", count, path)   # lazy %-args, not f-string
logger.exception("failed to process")                 # inside except: logs traceback
```

- Use the `logging` module for anything beyond a throwaway script — it has levels,
  handlers, and structured output `print` lacks.
- Pass `%`-style args (`logger.info("x=%s", x)`) so the string is only formatted if
  the level is enabled.
- `logger.exception(...)` inside an `except` block records the full traceback.

## Rules of thumb

- Catch specific exceptions; never bare `except` or silent `except: pass`
  (use `suppress` to ignore intentionally).
- Small `try` blocks; chain causes with `raise … from`.
- Manage every resource with `with`; write CMs via `@contextmanager`.
- `logging`, not `print`, for real programs.
