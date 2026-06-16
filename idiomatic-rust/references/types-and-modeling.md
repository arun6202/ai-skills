# Types & modeling

Rust's type system is built for making illegal states unrepresentable — the same
discipline as the F#/TS skills, with zero runtime cost. Model with `enum`s (sum
types) and `struct`s (product types), wrap constrained primitives in newtypes, and
derive the traits you need.

## Enums — "one of these"

An `enum` is an algebraic sum type: a value is exactly one variant, each carrying
its own data. This is Rust's workhorse for variants, states, and outcomes.

```rust
enum Shape {
    Circle { radius: f64 },                 // struct-like variant (named fields)
    Rectangle { width: f64, height: f64 },
    Point,                                   // unit variant
}
```

Consume with `match` — exhaustive, so adding a variant forces every site to
update (see `pattern-matching.md`). This is why an `enum` + `match` beats a
`Vec<Box<dyn Trait>>` for a *closed* set of variants: no heap, no dynamic
dispatch, and the compiler proves completeness.

`Option<T>` and `Result<T, E>` are just enums (`Some`/`None`, `Ok`/`Err`) — the
core of absence and failure modeling.

## Structs — "all of these"

```rust
#[derive(Debug, Clone, PartialEq)]
struct Customer {
    id: CustomerId,
    name: String,
    email: Email,
}
```

Three flavors: named-field structs (the default), tuple structs
(`struct Point(f64, f64)`), and unit structs (`struct Marker;`). Prefer named
fields for clarity.

## Make illegal states unrepresentable

Model so that bad combinations can't be constructed — then you never re-check them.

```rust
// ❌ illegal states representable: loading && error, success with no data…
struct Request {
    is_loading: bool,
    data: Option<Response>,
    error: Option<String>,
}

// ✅ exactly one state
enum Request {
    Loading,
    Success(Response),
    Error(String),
}
```

A `match` over the enum then handles precisely the real states, and `data` is
reachable only in `Success`. Same payoff as F# DUs / TS discriminated unions.

## Newtype pattern — constrained primitives

A bare `String` for an email invites mixing it up and skipping validation. Wrap it
in a one-field tuple struct whose only constructor validates ("parse, don't
validate"):

```rust
#[derive(Debug, Clone, PartialEq)]
pub struct Email(String);          // field is private to the module

impl Email {
    pub fn parse(s: String) -> Result<Self, EmailError> {
        if s.contains('@') { Ok(Email(s)) } else { Err(EmailError::Invalid(s)) }
    }
    pub fn as_str(&self) -> &str { &self.0 }
}
```

Now a function taking `Email` can't be handed an unvalidated `String`, and the
type documents the rule. Newtypes also let you implement traits you don't own on
types you don't own (the orphan-rule workaround), and add zero runtime cost.

## Typestate — encode lifecycle in types

Push a state machine into the type system so invalid transitions don't compile.
Each state is a distinct type; a transition consumes one and returns the next:

```rust
struct Draft { content: String }
struct Published { content: String }

impl Draft {
    fn publish(self) -> Published { Published { content: self.content } }
}
// Only a Draft has `.publish()`; only a Published has `.url()`.
// You cannot publish twice or read a URL before publishing — it won't compile.
```

This is the Rust expression of the F# "states as types" pattern — use it for
builders, connections (open/closed), and protocols.

## Deriving traits

Let `#[derive(...)]` generate the boilerplate. Common set:

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct Point { x: i32, y: i32 }

#[derive(Debug, Clone, Copy, PartialEq)]   // Copy only for small value types
struct Rgb(u8, u8, u8);

#[derive(Debug, Default)]                    // Default for a sensible zero value
struct Config { retries: u32, verbose: bool }
```

- `Debug` — almost always (for `{:?}` and errors). `Clone` — when copies are
  needed. `PartialEq`/`Eq` — for comparison/keys. `Hash` — for `HashMap`/`HashSet`
  keys. `Default` — for a zero/empty value. `Copy` — only small, plain value types.
- For ordering, derive `PartialOrd`/`Ord`. For serialization, `serde`'s
  `Serialize`/`Deserialize`.

## `#[non_exhaustive]` for public enums/structs

In a library's public API, mark types that may gain variants/fields later so
downstream `match`es must keep a `_` arm and can't break on additions:

```rust
#[non_exhaustive]
pub enum ApiError { NotFound, RateLimited, /* future variants */ }
```

## Modeling checklist

- [ ] "One of N" → `enum`; "all of" → `struct`.
- [ ] Can an illegal value be constructed? Push the rule into the type.
- [ ] Constrained primitives are newtypes with validating constructors.
- [ ] Lifecycle/protocol → consider typestate.
- [ ] Derive `Debug` (+ `Clone`/`PartialEq`/…) rather than hand-writing.
- [ ] Public enums that may grow → `#[non_exhaustive]`.
