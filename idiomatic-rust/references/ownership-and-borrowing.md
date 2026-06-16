# Ownership & borrowing

The defining feature of Rust, and the source of almost every "I'm fighting the
language" moment. The fix is rarely another `.clone()` — it's modeling *who owns
what* deliberately. Read a borrow error as feedback on your ownership design.

## The rules, briefly

- Every value has exactly one **owner**; when the owner goes out of scope, the
  value is dropped (freed). No GC, deterministic cleanup.
- You can **move** ownership (the default for non-`Copy` types on assignment/pass),
  or **borrow** it:
  - any number of **shared** borrows `&T` (read-only), **or**
  - exactly one **mutable** borrow `&mut T` (read-write),
  - never both at once. This is what prevents data races at compile time.

```rust
let s = String::from("hi");
let r1 = &s;          // shared borrow
let r2 = &s;          // another shared borrow — fine
println!("{r1} {r2}");
let m = &mut s;       // ❌ can't borrow mutably while shared borrows are live
```

## Borrow by default; clone with intent

Coming from a GC language, the reflex is to pass owned values everywhere and
`.clone()` when the compiler complains. Idiomatic Rust **borrows**:

```rust
// ❌ takes ownership (caller loses the Vec) or forces a clone at the call site
fn total(items: Vec<Item>) -> u64 { items.iter().map(|i| i.price).sum() }

// ✅ borrows — caller keeps ownership, no allocation
fn total(items: &[Item]) -> u64 { items.iter().map(|i| i.price).sum() }
```

`.clone()` is a legitimate tool — for genuinely needing a second owned copy, for
cheap-to-clone types, or to break a borrow knot in a cold path. But a `.clone()`
added *only to make an error go away* is a smell: it usually means a function
should take `&T` instead of `T`, or that two pieces of code are sharing ownership
they shouldn't.

## Function signatures: take the least you need

| Want                          | Take…                          | Notes                                  |
|-------------------------------|--------------------------------|----------------------------------------|
| Read a string                 | `&str`                         | accepts `&String` and string literals  |
| Read a list                   | `&[T]`                         | accepts `&Vec<T>` and arrays           |
| Read any owned value          | `&T`                           | shared, read-only                      |
| Mutate in place               | `&mut T`                       | exclusive                              |
| Consume / store the value     | `T`                            | take ownership only when you keep it   |
| Accept "string-like"          | `impl AsRef<str>` / `Into<String>` | flexible APIs                      |

Return **owned** values (`String`, `Vec<T>`) from functions that produce data;
take **borrows** in functions that only read. `&str` in, `String` out is the
canonical shape.

## `String` vs `&str` (and `Vec<T>` vs `&[T]`)

- `&str` / `&[T]` are **borrowed views** — use for parameters and any read-only
  access. No allocation.
- `String` / `Vec<T>` are **owned, growable** — use when you create, store, or
  return data.
- Convert when needed: `&s[..]` / `s.as_str()` to borrow; `.to_string()` /
  `.to_owned()` / `.to_vec()` to own (these allocate — do it once, at the edge).

## Lifetimes: usually elided, occasionally explicit

Most borrows need no annotation — the compiler infers them. You write lifetimes
only when returning a borrow whose origin is ambiguous:

```rust
// "the returned &str lives as long as both inputs"
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

If lifetimes get hairy, that's often a signal to **return an owned value** instead
of a borrow, or to restructure so the data outlives its uses. Don't reach for
complex lifetime gymnastics before considering ownership.

## Interior mutability & shared ownership — deliberately, not reflexively

`Rc<RefCell<T>>` (single-thread) / `Arc<Mutex<T>>` (multi-thread) let multiple
owners share mutable state. They're the right tool for genuine shared graphs,
caches, or observer setups — but they move borrow checking to **runtime** (a
`RefCell` borrow panics on violation) and add overhead. Before reaching for them:

- Can one part **own** the data and others **borrow** it (`&`/`&mut`)?
- Can you pass `&mut` down instead of sharing?
- Would an **index/arena** (store nodes in a `Vec`, refer to them by `usize`)
  model your graph without `Rc`?
- Would **message passing** (channels) avoid shared mutable state entirely?

Reach for `Rc<RefCell>` when those genuinely don't fit — not as the first move to
silence the checker.

## `Copy` vs move

Small, plain types (`i32`, `bool`, `char`, `f64`, small tuples/arrays of `Copy`)
are `Copy` — assigning/passing duplicates them, no move. Everything else moves.
Derive `Copy` (with `Clone`) only for small value types where bit-copy is correct;
don't derive it on types holding heap data (`String`, `Vec`).

## `Cow` — borrow until you must own

`Cow<str>` ("clone on write") lets a function return a borrow in the common case
and only allocate when it actually modifies — the idiomatic way to avoid
needless `String` allocation in transform functions:

```rust
use std::borrow::Cow;
fn normalize(input: &str) -> Cow<str> {
    if input.contains(' ') { Cow::Owned(input.replace(' ', "_")) }
    else { Cow::Borrowed(input) }      // no allocation when already clean
}
```

## The mindset

When the borrow checker rejects code, ask **"what's the ownership story?"** — who
should own this, who merely reads it, who needs to mutate it — and adjust
signatures and structure. The clone-and-unwrap path compiles but throws away the
guarantees you came to Rust for.
