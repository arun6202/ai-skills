# Async & tooling

Async Python is `asyncio` with `async`/`await` and **structured concurrency**
(`TaskGroup`). Plus the modern toolchain — which in 2026 has consolidated around a
small, fast, well-integrated set: **uv**, **ruff**, a strict type checker, and
`pytest`, all configured in `pyproject.toml`.

## async / await

```python
import asyncio

async def fetch_user(client: Client, id: int) -> User:
    resp = await client.get(f"/users/{id}")    # await suspends without blocking
    return User(**resp.json())
```

- `async def` defines a coroutine; `await` suspends until the awaitable completes.
  A coroutine does nothing until awaited or scheduled on the event loop
  (`asyncio.run(main())` at the top level).
- `asyncio` is for **I/O-bound concurrency** (network, disk, many connections). For
  CPU-bound work use processes (`ProcessPoolExecutor`) or threads — or free-threaded
  Python (below).

## Structured concurrency: `TaskGroup` (3.11+)

`asyncio.TaskGroup` runs child tasks concurrently and **owns their lifetime**: it
awaits all of them, cancels siblings if one fails, and collects failures into an
`ExceptionGroup`. Prefer it to bare `create_task` / `gather`:

```python
async def load_dashboard() -> Dashboard:
    async with asyncio.TaskGroup() as tg:        # all tasks awaited at block exit
        user = tg.create_task(fetch_user())
        orders = tg.create_task(fetch_orders())
    return Dashboard(user.result(), orders.result())   # both done here
```

- A failing child cancels the others and raises an `ExceptionGroup` — handle with
  `except*` (see `errors-and-resources.md`).
- `asyncio.gather(...)` still works for simple fan-out, but `TaskGroup` gives proper
  cancellation/error semantics — make it the default.
- Don't fire-and-forget a bare `create_task` and drop the reference; let a
  `TaskGroup` own it (the analogue of "no floating promises").

## Don't block the event loop

Inside async code, never call a blocking function (`time.sleep`, sync I/O, heavy
CPU) — it freezes the whole loop. Use the async equivalent (`await asyncio.sleep`,
an async client) or offload:

```python
result = await asyncio.to_thread(blocking_cpu_work, data)   # run in a thread
```

## Python 3.13 / 3.14 — what changed

- **Free-threading (no-GIL)** — officially supported in 3.14 (PEP 779); a *separate*
  build (`python3.14t`), while the default still ships with the GIL. It enables
  true multi-core threading for CPU-bound work; the single-thread overhead is down
  to ~5–10%. Treat it as production-viable-but-opt-in; check that your C-extension
  deps support it before relying on it.
- **Experimental JIT** (PEP 744) — copy-and-patch JIT, 10–30% on compute-heavy code;
  off by default, opt-in build flag.
- **t-strings** (PEP 750, 3.14) — `t"..."` returns a `Template` for *safe*
  interpolation (escape SQL/HTML/shell before building the final string); prefer
  over f-strings when the output needs escaping.
- **Deferred annotations** (PEP 649, 3.14) — annotations evaluate lazily, so forward
  references generally work without `from __future__ import annotations`.
- Better interactive REPL, clearer error messages, `tomllib` (3.11) for reading
  TOML in the stdlib.

## The 2026 toolchain

A small, fast, integrated stack (three of these are from Astral and share
`pyproject.toml`):

| Tool                | Role                                                         |
|---------------------|--------------------------------------------------------------|
| **uv**              | Python install + venv + dependency management + lockfile + `uv run`; replaces pip/venv/virtualenv/poetry (Rust, very fast) |
| **ruff**            | linter **and** formatter; replaces flake8/black/isort/pyupgrade (one binary, ms-fast) |
| **mypy --strict** / **pyright** | static type checking (the production baseline); ty (Astral) is the fast newcomer |
| **pytest**          | testing — fixtures, parametrize, plain `assert`               |
| **pydantic**        | runtime validation / settings at boundaries                  |

```bash
uv init myproj && cd myproj      # new project with pyproject.toml
uv add httpx                     # add a dependency (updates lockfile)
uv add --dev ruff mypy pytest    # dev tools
uv run pytest                    # run in the managed environment
ruff check . && ruff format .    # lint + format
uv run mypy --strict src         # type-check
```

- **`pyproject.toml`** is the single config file for uv, ruff, mypy/pyright,
  pytest, coverage, and build settings. Prefer a `src/` layout for packages.
- Pin a Python version (`uv python pin 3.13`) and commit the lockfile
  (`uv.lock`) for reproducible installs.
- Make CI run `ruff check`, `ruff format --check`, the type checker in strict
  mode, and `pytest` — so style, types, and tests are all enforced.

## Testing with pytest

```python
import pytest

def test_parse_port_rejects_junk() -> None:
    assert parse_port("x") is None

@pytest.mark.parametrize("raw,expected", [("80", 80), ("443", 443)])
def test_parse_port(raw: str, expected: int) -> None:
    assert parse_port(raw) == expected

def test_raises() -> None:
    with pytest.raises(ConfigError):
        load_config("/nope")
```

Use plain `assert`, fixtures for setup, `parametrize` for table-driven tests, and
`pytest.raises` for expected exceptions. For async tests use `pytest-asyncio`.

## Checklist

- [ ] `async`/`await` for I/O concurrency; **`TaskGroup`** for structured fan-out;
      never block the loop (`asyncio.to_thread` to offload).
- [ ] Project managed by **uv** with `pyproject.toml` + committed `uv.lock`.
- [ ] **ruff** (lint + format) and a **strict type checker** in CI.
- [ ] **pytest** with parametrize/fixtures; pin the Python version.
- [ ] Consider 3.14 free-threading for CPU-bound work (deps permitting).
