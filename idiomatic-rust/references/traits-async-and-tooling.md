# Traits, async & tooling

Traits are Rust's answer to type classes and interfaces — shared behavior without
inheritance. Plus the async model and the tooling that keeps code idiomatic.

## Traits — shared behavior, no inheritance

Rust has **no class inheritance**. You share behavior with traits and reuse code
with composition (embed types as fields), not by extending base classes.

```rust
trait Area {
    fn area(&self) -> f64;
    fn describe(&self) -> String {                 // default method
        format!("area = {:.2}", self.area())
    }
}

impl Area for Circle {
    fn area(&self) -> f64 { std::f64::consts::PI * self.radius * self.radius }
}
```

Traits can have default methods, associated types, and associated constants. You
can implement your own traits for foreign types, or foreign traits for your types
(but not both — the orphan rule; newtype around it if needed).

## Generics (static) vs trait objects (dynamic)

Two ways to be polymorphic over a trait — pick by whether you need a *homogeneous,
zero-cost* abstraction or a *heterogeneous, runtime* one:

```rust
// Generic: monomorphized per type, zero-cost, inlinable. Default choice.
fn total_area<T: Area>(items: &[T]) -> f64 {
    items.iter().map(Area::area).sum()
}

// impl Trait: terser generics in arg/return position
fn make_shape() -> impl Area { Circle { radius: 1.0 } }

// Trait object: one type erased behind a pointer + vtable; for mixed types
fn total_area_dyn(items: &[Box<dyn Area>]) -> f64 {
    items.iter().map(|s| s.area()).sum()
}
```

- **Generics / `impl Trait`** — when the concrete type is known at each call site;
  monomorphized, inlined, no runtime cost. Prefer this.
- **`dyn Trait`** (behind `&`/`Box`/`Rc`) — when you need a collection of *different*
  concrete types, or to break compile-time coupling. One vtable indirection.
- For a **closed** set of variants, prefer an `enum` + `match` over
  `Box<dyn Trait>` (no allocation, exhaustive — see `types-and-modeling.md`).

## Common standard traits

Implement (usually via `#[derive]`) the traits that make your type cooperate with
the ecosystem: `Debug`, `Clone`, `PartialEq`/`Eq`, `Hash`, `PartialOrd`/`Ord`,
`Default`, `From`/`Into` (conversions — implement `From`, get `Into` free),
`Iterator`, `Display` (hand-written, for user-facing text), `Error` (via
`thiserror`). Prefer implementing `From` for conversions so `?` and `.into()` work.

## Async/await

`async fn` returns a `Future` that does nothing until `.await`ed by a runtime
(`tokio` is the de-facto choice; `async-std`/`smol` exist). The 2024 edition adds
**async closures** (`AsyncFn`).

```rust
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let body = reqwest::get("https://example.com").await?.text().await?;
    println!("{body}");
    Ok(())
}

// run independent futures concurrently:
let (a, b) = tokio::join!(fetch_a(), fetch_b());

// race / many:
let first = tokio::select! { v = fetch_a() => v, v = fetch_b() => v };
let all   = futures::future::try_join_all(ids.into_iter().map(fetch)).await?;
```

- **`async fn` in traits** is stable (since 1.75) for static dispatch. For
  `dyn`-dispatched async trait methods, you still typically reach for the
  `async-trait` crate or return `Pin<Box<dyn Future>>` — a known rough edge.
- Don't block in async code (`std::thread::sleep`, heavy CPU) — use the runtime's
  async equivalents (`tokio::time::sleep`) or `spawn_blocking`.
- `.await` points are where tasks yield; a `Future` not `.await`ed does nothing
  (the analogue of a floating promise).

## `unsafe` — last resort, documented

`unsafe` doesn't disable the borrow checker; it lets you do five extra things
(deref raw pointers, call `unsafe` fns/FFI, access `static mut`/unions, implement
`unsafe` traits). Avoid it in application code. When unavoidable (FFI, a proven
performance-critical invariant):

- Keep the `unsafe` block minimal and wrap it in a **safe abstraction**.
- Document the invariant with a `// SAFETY:` comment explaining why it's sound.
- Prefer a vetted crate over hand-rolled `unsafe`.

## Tooling — let it enforce idiom

- **`cargo clippy`** — the lint suite; it teaches idiomatic Rust (flags needless
  clones, `unwrap`, manual loops, etc.). Run `cargo clippy -- -D warnings` in CI.
- **`cargo fmt`** (rustfmt) — canonical formatting; non-negotiable, run it.
- **`cargo test`** — unit tests in `#[cfg(test)] mod tests`, integration tests in
  `tests/`, doc-tests in `///` examples (they compile and run).
- **`cargo check`** — fast type-check without codegen during development.
- **Cargo.toml** — pin the edition (`edition = "2024"`); add `thiserror`/`anyhow`,
  `serde`, `tokio` as needed; prefer well-maintained crates over reinvention.

## The 2024 edition

Set `edition = "2024"` for new crates (stable since Rust 1.85, Feb 2025). It
brings let chains, async closures, refined `impl Trait` lifetime capture, and
`unsafe_op_in_unsafe_fn` warnings by default. Editions are opt-in and per-crate —
they don't split the ecosystem; you can use a 2024 crate from a 2021 one and vice
versa. Update with `cargo fix --edition`.

## Checklist

- [ ] Share behavior via traits + composition; never reach for inheritance.
- [ ] Generics/`impl Trait` by default; `dyn` only for heterogeneous/dynamic needs;
      `enum` for closed variant sets.
- [ ] Derive the standard traits; implement `From` for conversions.
- [ ] Async: use a runtime, don't block, don't drop un-`await`ed futures.
- [ ] `unsafe` only with a safe wrapper + `// SAFETY:` note.
- [ ] `cargo clippy -D warnings` + `cargo fmt` + tests in CI; `edition = "2024"`.
