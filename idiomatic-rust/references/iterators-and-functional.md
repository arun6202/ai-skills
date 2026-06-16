# Iterators & functional style

Rust's iterators are lazy, composable, and **zero-cost** — a chain of adapters
compiles down to roughly the same machine code as a hand-written loop, with none
of the index bugs. Prefer them to manual indexing, and lean on closures.

## Iterate, don't index

```rust
// ❌ index loop — bounds-check noise, off-by-one risk
let mut sum = 0;
for i in 0..v.len() { sum += v[i]; }

// ✅ iterator
let sum: i32 = v.iter().sum();

// transform + filter
let names: Vec<&str> = users.iter()
    .filter(|u| u.active)
    .map(|u| u.name.as_str())
    .collect();
```

To loop for side effects, iterate the values directly:

```rust
for user in &users { notify(user); }     // borrows each; `&mut users` to mutate
```

## `iter` vs `iter_mut` vs `into_iter`

Choose by what you need from the collection:

- **`.iter()`** → yields `&T` (read; collection unchanged).
- **`.iter_mut()`** → yields `&mut T` (mutate in place).
- **`.into_iter()`** → yields `T`, consuming the collection (when you own and want
  to move the elements out). `for x in v` uses `into_iter` (moves); `for x in &v`
  uses `iter` (borrows).

## The adapter toolbox

Adapters are lazy (they build a new iterator); **consumers** drive the work.

| Adapter / consumer        | Does                                        |
|---------------------------|---------------------------------------------|
| `map(f)`                  | transform each item                         |
| `filter(pred)`            | keep matching items                         |
| `filter_map(f)`           | map + drop `None`s in one pass              |
| `flat_map(f)` / `flatten` | map + flatten nested iterators              |
| `fold(init, f)`           | reduce to a single value                    |
| `sum` / `product` / `count` / `min` / `max` | specialized reductions    |
| `find(pred)` / `position(pred)` | first match / its index               |
| `any(pred)` / `all(pred)` | boolean tests (short-circuit)               |
| `take(n)` / `skip(n)` / `step_by(k)` | slice the stream                |
| `enumerate()`             | pair each item with its index               |
| `zip(other)`              | pair two iterators                          |
| `rev()` / `chain(other)`  | reverse / concatenate                       |
| `collect()`               | materialize into a `Vec`/`String`/`Map`/…   |

```rust
let lookup: std::collections::HashMap<u32, &User> =
    users.iter().map(|u| (u.id, u)).collect();

let first_even = nums.iter().copied().find(|n| n % 2 == 0);   // Option<i32>
```

Prefer the specialized consumer (`sum`, `any`, `find`) over a `fold` that
re-implements it.

## `collect` is powerful — and turns errors inside-out

`collect()` is generic over the target type (annotate it or use the turbofish).
The killer trick: collecting an iterator of `Result`s into a single
`Result<Vec<_>, E>` that fails on the first error:

```rust
// Vec<&str> -> Result<Vec<i32>, ParseIntError>  (stops at first bad parse)
let nums: Result<Vec<i32>, _> = lines.iter().map(|l| l.parse::<i32>()).collect();
let nums = nums?;     // propagate

// same trick with Option -> Option<Vec<_>>
let all: Option<Vec<_>> = items.iter().map(try_convert).collect();
```

## Closures: `Fn` / `FnMut` / `FnOnce`

Closures capture their environment; the trait reflects how:

- **`Fn`** — captures by shared ref; callable many times (`map`, `filter`).
- **`FnMut`** — captures by mutable ref; mutates captured state across calls.
- **`FnOnce`** — consumes captures; callable once (e.g. moves a value out).

```rust
let factor = 3;
let scale = |x: i32| x * factor;            // Fn: borrows `factor`
let mut total = 0;
let mut add = |x: i32| total += x;          // FnMut: mutates `total`
let s = String::from("hi");
let consume = move || drop(s);              // FnOnce: `move` takes ownership
```

Use `move` to force a closure to take ownership of its captures (essential for
threads/async that outlive the current scope). Accept closures in your APIs via
generics (`f: impl Fn(i32) -> i32`) for zero-cost, or `Box<dyn Fn…>` when you need
to store heterogeneous ones.

## `Option` / `Result` are functional too

Both have rich combinator APIs — chain them instead of matching:

```rust
let city = user.and_then(|u| u.address).map(|a| a.city).unwrap_or_default();
let len  = maybe_name.as_deref().map(str::len);          // Option<usize>
let val  = result.map_err(MyError::from)?;               // convert + propagate
```

`map`, `and_then` (flatMap/bind), `or_else`, `unwrap_or(_else/_default)`,
`ok_or`, `filter`, `as_deref`, `transpose` — the same railway vocabulary as the
F#/TS skills.

## Performance note

Iterator chains are zero-cost — they don't allocate intermediate collections (only
`collect()` does). So the functional form is usually as fast as the loop; write it
for clarity. For genuinely parallel data work, swap `.iter()` for **`rayon`**'s
`.par_iter()` and the same chain runs across threads.
