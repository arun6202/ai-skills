---
name: idiomatic-rust
description: >-
  Write, refactor, or review idiomatic Rust (.rs, Cargo crates) — even a quick
  "write this in Rust". Steers toward working WITH the borrow checker rather than
  against it: ownership and borrowing over reflexive `.clone()`, `Result` + `?`
  over `.unwrap()`/`panic!`, enums + exhaustive `match` over type tags and
  inheritance, iterators over index loops, traits + composition over OOP
  hierarchies, and newtypes/typestate to make illegal states unrepresentable.
  Reach for it when modeling data, handling errors, fighting lifetimes or the
  borrow checker, choosing `&str` vs `String` or `enum` vs `Box<dyn Trait>`, or
  deciding whether you really need `Rc<RefCell<_>>` or `unsafe`. Targets the Rust
  2024 edition. Counters habits carried from GC/OOP languages.
---

# Idiomatic Rust

Rust is already a frontier, functional-leaning, type-driven language by design —
algebraic enums, exhaustive `match`, `Result`/`Option`, no null, immutability by
default, traits, and zero-cost iterators. Most "bad Rust" isn't wrong idioms so
much as **fighting the language**: cloning to silence the borrow checker,
`.unwrap()`-ing every `Result`, wrapping everything in `Rc<RefCell<_>>`, or trying
to recreate class inheritance.

So the prime directive: **work with the grain.** Model ownership deliberately,
borrow by default, let errors be values, make the type system carry the rules,
and lean on iterators and traits. The borrow checker is a design tool, not an
obstacle — when it complains, it's usually telling you the *ownership model* is
wrong, not that you need another `.clone()`.

> **Part of the `idiomatic-code` family** — the shared cross-language philosophy and the Rosetta Stone (porting + review) live there.
>
> Stack family: this is the language the `fsharp-vs-frontier` skill names for
> ownership/no-GC/performance. The shared ideas — illegal states unrepresentable,
> exhaustive matching, `Result`-based errors — are identical to the F#, C#, and
> TS skills; Rust adds the ownership discipline that makes them zero-cost.

## Break the muscle memory (reflex → idiomatic)

When your instinct fires the left column, write the right column instead.

| Reflex (GC / OOP / C++ habit)                       | Idiomatic Rust                                                       |
|-----------------------------------------------------|---------------------------------------------------------------------|
| `.clone()` to make a borrow error go away           | Borrow (`&`/`&mut`); restructure ownership; clone only when you mean to|
| `.unwrap()` / `.expect()` in real code              | Propagate with `?` + `Result`; `match`/`if let`; unwrap only in tests/invariants |
| `Rc<RefCell<T>>` to share mutable state             | Rethink ownership; pass `&mut`; use an `enum`, channels, or an index/arena — reach for `Rc<RefCell>` only with a real reason |
| Class inheritance                                   | Traits for shared behavior + composition (Rust has no inheritance)  |
| `Vec<Box<dyn Trait>>` for a closed set of variants  | An `enum` + `match` (no allocation, no dynamic dispatch, exhaustive) |
| `for i in 0..v.len() { v[i] }`                      | Iterators: `for x in &v`, `v.iter().map(...)`                       |
| `String` for every parameter                        | Take `&str` (or `impl AsRef<str>`); return owned `String`          |
| `null` / sentinel values                            | `Option<T>`                                                        |
| `panic!` / exceptions for error flow                | `Result<T, E>` + `?`; typed error enums                            |
| Mutable global state                                | Pass state explicitly; `const`/`static`/`OnceLock` for true constants |
| `unsafe` to get around the checker                  | A safe abstraction; `unsafe` only for FFI / proven invariants, documented |
| Getters/setters on every field                      | Public fields or a constructor; encapsulate only when an invariant needs it |
| One giant `impl` god-struct                         | Small types, focused traits, free functions                        |

If you genuinely need shared ownership (a graph, a cache) or interior mutability,
`Rc`/`Arc` + `RefCell`/`Mutex` are correct tools — use them deliberately, not as a
reflex to dodge the borrow checker.

## The creed

1. **Work with the borrow checker.** Decide who *owns* each value; borrow by
   default, clone with intent, and let a borrow error prompt an ownership rethink.
2. **Make illegal states unrepresentable.** `enum`s for "one of", structs for "all
   of", newtypes for constrained primitives, typestate for lifecycle — then
   `match` exhaustively.
3. **Errors are values.** `Result` + `?`; `panic!`/`unwrap` only for genuine bugs
   and truly unrecoverable situations.
4. **Iterate, don't index.** Lazy, zero-cost iterator chains over manual loops and
   indexing.
5. **Composition over inheritance.** Traits (Rust's type classes) for shared
   behavior; generics with bounds, or trait objects when you need dynamic dispatch.
6. **Safe by default.** `unsafe` is a last resort with documented invariants, not a
   shortcut.
7. **Let the tools enforce it.** `cargo clippy`, `cargo fmt`, `cargo test`.

## Quick reach-for guide

| You need to…                              | Reach for…                                                       |
|-------------------------------------------|------------------------------------------------------------------|
| "One of N shapes" / a state              | `enum` + exhaustive `match`                                       |
| A data bundle                             | `struct` (with `#[derive(Debug, Clone, PartialEq)]`)            |
| Constrain a primitive (Email, UserId)     | Newtype `struct Email(String)` + a `parse` constructor          |
| "Maybe absent"                            | `Option<T>` + combinators / `?`                                 |
| "Succeeds or fails"                       | `Result<T, E>` + `?`; `thiserror` (lib) / `anyhow` (app)        |
| Transform a collection                    | `.iter().map()/.filter()/.collect()`                            |
| Share behavior across types               | A `trait` + `impl`; generics `<T: Trait>` or `dyn Trait`        |
| Read-only borrow of a `String`/`Vec`      | `&str` / `&[T]` parameters                                       |
| Early-return on `None`/`Err`              | `let … else { return … }`; the `?` operator                     |

## Reference files — read on demand

- **`references/ownership-and-borrowing.md`** — ownership, moves, `&`/`&mut`,
  lifetimes, working *with* the borrow checker, when to clone, `String` vs `&str`,
  `Vec` vs slices, `Cow`, and avoiding `Rc<RefCell>` reflexes. *Read first; read
  when the borrow checker fights you.*
- **`references/types-and-modeling.md`** — `enum`s and structs, illegal-states-
  unrepresentable, the newtype and typestate patterns, `Option`/`Result`, deriving
  traits, `#[non_exhaustive]`. *Read when modeling data.*
- **`references/pattern-matching.md`** — `match`, exhaustiveness, guards, bindings,
  `if let`/`while let`/`let-else`, let chains, destructuring, or-patterns. *Read
  for branching.*
- **`references/error-handling.md`** — `Result`/`Option` + `?`, when `panic!` is
  ok, custom error enums, `thiserror` vs `anyhow`, `From`/`?` conversion, adding
  context. *Read for error handling.*
- **`references/iterators-and-functional.md`** — iterators (lazy, zero-cost),
  adapters, closures (`Fn`/`FnMut`/`FnOnce`), `collect` into `Result`,
  `Option`/`Result` combinators. *Read for data processing.*
- **`references/traits-async-and-tooling.md`** — traits as type classes, generics
  vs `dyn`, `impl Trait`, no-inheritance/composition, async/await + tokio,
  `unsafe` discipline, clippy/rustfmt, the 2024 edition. *Read for abstraction,
  async, or setup.*

## A taste

```rust
use std::f64::consts::PI;

#[derive(Debug, Clone, PartialEq)]
enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

fn area(shape: &Shape) -> f64 {           // borrow, don't take ownership
    match shape {                          // exhaustive: adding a variant won't compile until handled
        Shape::Circle { radius } => PI * radius * radius,
        Shape::Rectangle { width, height } => width * height,
    }
}

fn total_area(shapes: &[Shape]) -> f64 {   // slice, not Vec; no clone
    shapes.iter().map(area).sum()          // iterator pipeline, zero-cost
}
```

No clone, no unwrap, no inheritance, exhaustive matching, ownership borrowed not
taken — and the `enum` *is* the documentation. That is the target for all Rust
here.
