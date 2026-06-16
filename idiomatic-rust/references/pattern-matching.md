# Pattern matching

`match` is Rust's primary control-flow and decomposition tool — exhaustive,
expression-valued, and the natural consumer of every `enum`, `Option`, and
`Result`. Lean on it instead of chains of `if`/downcasts.

## `match` is an expression

It returns a value, so it assigns and composes directly:

```rust
let label = match n {
    0 => "zero",
    1..=9 => "small",         // inclusive range
    _ if n < 0 => "negative", // guard
    _ => "large",
};
```

- Every arm is `pattern => expression`. Arms must be **exhaustive** — the compiler
  errors if you miss a case. That's the feature: adding an `enum` variant lights up
  every `match` that must change.
- `_` is the catch-all; use it sparingly — for a closed `enum` you control, prefer
  listing variants so additions surface, rather than silently hitting `_`.

## The pattern toolbox

```rust
match value {
    // Enum variants, destructured
    Shape::Circle { radius } => …,
    Shape::Rectangle { width, height } => …,

    // Tuples / structs
    (0, y) => …,
    Point { x, y } => …,

    // Literals, ranges, or-patterns
    1 | 2 | 3 => …,
    'a'..='z' => …,

    // Bindings with @  (capture while testing)
    n @ 1..=100 => println!("in range: {n}"),

    // Guards
    p if p.is_valid() => …,

    // Wildcards / ignore
    Some(_) => …,
    _ => …,
}
```

- **Or-patterns** `A | B`, **ranges** `1..=9`, **bindings** `name @ pattern`.
- **Guards** (`if cond`) for conditions a pattern can't express; keep them cheap.
- Destructure structs/enums/tuples/slices directly in the pattern — no accessors.

## Slice patterns

```rust
match arr {
    [] => "empty",
    [only] => "one",
    [first, .., last] => "ends",     // .. = rest
    [a, b, rest @ ..] => …,           // bind the tail
    _ => "other",
}
```

## `Option` / `Result` matching

```rust
match find_user(id) {
    Some(user) => greet(user),
    None => default_greeting(),
}

match parse(input) {
    Ok(value) => use_it(value),
    Err(e) => report(e),
}
```

But for the common cases, the combinators and `?` are terser than `match` (see
`error-handling.md` and `iterators-and-functional.md`) — reach for `match` when
you genuinely branch on multiple variants.

## `if let` / `while let` — match one shape

When you only care about one pattern, `if let` avoids a full `match`:

```rust
if let Some(user) = find_user(id) {
    greet(user);
}

while let Some(item) = queue.pop() {     // loop until None
    process(item);
}

if let Ok(n) = s.parse::<i32>() { … } else { … }
```

## `let … else` — bind or diverge

When a binding *must* succeed or you bail out, `let-else` keeps the happy path
unindented (no `if let` pyramid):

```rust
fn process(input: &str) -> Result<i32, MyError> {
    let Ok(n) = input.parse::<i32>() else {
        return Err(MyError::NotANumber);
    };
    // `n` is in scope and bound for the rest of the function
    Ok(n * 2)
}
```

The `else` block must diverge (`return`, `break`, `continue`, `panic!`).

## Let chains (Rust 2024 edition)

Chain `let` bindings and boolean tests with `&&` in `if`/`while`, flattening
nested `if let`s:

```rust
if let Some(user) = session.user()
    && user.is_admin()
    && let Some(token) = user.token()
{
    grant_access(token);
}
```

(Available in the 2024 edition; on older editions, nest `if let` + `if`.)

## `matches!` — a boolean test

For a quick "does this match?" without a full `match`:

```rust
if matches!(status, Status::Active | Status::Pending) { … }
```

## Avoid the anti-patterns

- Don't `unwrap()`/`expect()` to dodge handling a `None`/`Err` — `match`, `if let`,
  `let-else`, or `?` instead (see `error-handling.md`).
- Don't downcast with `as`/`Any` where an `enum` + `match` models the variants.
- Don't reach for a `_` arm on an `enum` you own just to quiet the compiler — list
  the variants so new ones force a decision.
