# Error handling

Rust has no exceptions for ordinary failure — errors are **values** of type
`Result<T, E>`, propagated with `?`. `panic!` is for bugs and the truly
unrecoverable. The reflex to fix: replace `.unwrap()`/`.expect()` everywhere with
proper propagation.

## `Result` + `?`

`Result<T, E>` is `Ok(T) | Err(E)`. The `?` operator unwraps `Ok`, or returns the
`Err` early from the current function — turning what would be nested matches into a
straight line:

```rust
fn load_config(path: &Path) -> Result<Config, ConfigError> {
    let text = std::fs::read_to_string(path)?;   // returns Err on failure
    let config: Config = toml::from_str(&text)?; // ? converts the error type via From
    Ok(config)
}
```

`?` also works on `Option` (returns `None` early), and the two compose with
`.ok_or(...)` / `.ok_or_else(...)` to convert `Option` → `Result`.

## When `panic!` / `unwrap` / `expect` are OK

Panicking aborts the thread (and usually the program). Acceptable for:

- **Genuine bugs / broken invariants** — a state that "can't happen"; crash loudly.
- **Tests and examples** — `unwrap()`/`expect()` are fine there.
- **Prototypes / `main` glue** — early on, before you wire real error types.
- **Unrecoverable startup** — e.g. a missing required config at boot, with
  `.expect("CONFIG_PATH must be set")` giving a clear message.

Not OK: `unwrap()` on anything that can fail in normal operation (I/O, parsing,
user input, network). Prefer `?`. If you must extract, use `expect("why this is
safe")` with a reason, never a bare `unwrap()`.

```rust
let port: u16 = env::var("PORT")?.parse()?;          // ✅ propagate
let port = env::var("PORT").unwrap().parse().unwrap(); // ❌ two panics waiting to happen
```

## Custom error types with `thiserror` (libraries)

For a **library**, define a precise error `enum` so callers can match on causes.
The `thiserror` crate derives `std::error::Error`, `Display`, and `From`
conversions with almost no boilerplate — the standard choice:

```rust
#[derive(Debug, thiserror::Error)]
pub enum ConfigError {
    #[error("could not read config file")]
    Io(#[from] std::io::Error),          // #[from] auto-converts io::Error via ?

    #[error("invalid TOML: {0}")]
    Parse(#[from] toml::de::Error),

    #[error("missing required field: {field}")]
    MissingField { field: String },
}
```

- `#[error("…")]` provides the `Display` message.
- `#[from]` generates a `From` impl so `?` converts that source error
  automatically; `#[source]` records an underlying cause without auto-conversion.
- Always derive `Debug`; preserve the cause with `#[from]`/`#[source]`.

## Application errors with `anyhow`

For **application / binary** code where you mostly bubble errors up to be logged
or shown — and don't need callers to match on the exact type — `anyhow::Result`
erases the error type and lets you attach context:

```rust
use anyhow::{Context, Result};

fn run() -> Result<()> {
    let config = load_config(&path)
        .with_context(|| format!("loading config from {}", path.display()))?;
    start_server(config).context("starting server")?;
    Ok(())
}

fn main() -> Result<()> {
    run()   // anyhow prints the full context chain on exit
}
```

**Rule of thumb:** `thiserror` for libraries (callers need typed errors), `anyhow`
for applications (you need context and convenience). They compose — an app using
`anyhow` happily consumes a library's `thiserror` enums via `?`.

## Adding context without anyhow

In library code, convert and annotate with `map_err`:

```rust
let text = std::fs::read_to_string(path)
    .map_err(|e| ConfigError::Io(e))?;     // or rely on #[from]
```

## Error trait objects

For quick code or simple boundaries, `Box<dyn std::error::Error>` (or
`anyhow::Error`) accepts any error via `?`:

```rust
fn quick() -> Result<(), Box<dyn std::error::Error>> {
    let n: i32 = "42".parse()?;            // any error type flows in
    Ok(())
}
```

Fine for `main`, scripts, and prototypes; prefer a typed `enum` for library APIs.

## Result combinators (avoid match where a combinator is clearer)

```rust
let n = s.parse::<i32>().unwrap_or(0);                 // default on error
let n = s.parse::<i32>().unwrap_or_else(|_| compute()); // lazy default
let doubled = parse(s).map(|n| n * 2)?;                 // transform Ok
let v = maybe.ok_or(MyError::Missing)?;                 // Option -> Result
config.get("k").map(|s| s.parse()).transpose()?;        // Option<Result> -> Result<Option>
```

## Rules of thumb

- Return `Result`; propagate with `?`. Reserve `panic!`/`unwrap`/`expect` for bugs,
  tests, and unrecoverable startup — and give `expect` a reason.
- `thiserror` for libraries, `anyhow` for applications.
- Preserve causes (`#[from]`/`#[source]`, `.context()`); always derive `Debug`.
- Model expected failures as typed `enum` variants the caller can match.
