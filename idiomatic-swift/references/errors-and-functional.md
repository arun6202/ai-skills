# Errors & functional style

Swift errors are typed values handled with `do`/`try`/`catch` (or `Result`), not
ignored. And Swift is functional-friendly — `map`/`filter`/`reduce`, closures, and
expression-valued branches keep transforms declarative.

## Throwing & handling errors

Declare what can fail with `throws`; call it with `try` inside a `do/catch`:

```swift
enum ConfigError: Error {
    case fileNotFound(path: String)
    case invalidFormat(reason: String)
}

func load(_ path: String) throws -> Config {
    guard let raw = readFile(path) else {
        throw ConfigError.fileNotFound(path: path)
    }
    return try parse(raw)         // propagate inner throws with `try`
}

do {
    let config = try load("app.toml")
    start(config)
} catch ConfigError.fileNotFound(let path) {
    print("missing: \(path)")     // catch specific cases (with bindings)
} catch {
    print("failed: \(error)")     // `error` is the implicit binding here
}
```

- `throws` marks a function as able to fail; the caller must `try` it.
- `catch` patterns can match specific error cases and bind associated values.
- Errors propagate up automatically through `try` until something catches them —
  the analogue of Rust's `?`.

## Typed throws (Swift 6)

Swift 6 lets you declare the *specific* error type a function throws, so callers
get exhaustive, typed handling (closer to `Result<T, E>`):

```swift
func load(_ path: String) throws(ConfigError) -> Config { … }

do {
    let config = try load(path)
} catch {
    // `error` is typed as ConfigError here — switch it exhaustively
    switch error {
    case .fileNotFound(let p): …
    case .invalidFormat(let r): …
    }
}
```

Use typed throws when a function has a small, known error set the caller should
handle precisely; leave it untyped (`throws`) for open-ended/propagating errors.

## `try?` and `try!`

```swift
let config = try? load(path)     // Config? — nil on any error (you lose the reason)
let config = try! load(path)     // Config — CRASHES on error (avoid outside tests/invariants)
```

- `try?` converts a throwing call to an optional — fine when you don't need the
  error, but **handle the nil**; don't `try?` then force-unwrap.
- `try!` force-unwraps the success and crashes on failure — same caveat as `!`:
  tests, or values you can prove won't throw.
- Never write an empty `catch {}` — that swallows failures silently.

## `Result<Success, Failure>`

When you want to *store* or *pass around* an outcome (callbacks, deferred handling)
rather than throw immediately, use `Result`:

```swift
func fetch(_ url: URL) -> Result<Data, NetworkError> { … }

switch fetch(url) {
case .success(let data): handle(data)
case .failure(let error): report(error)
}

// bridge to/from throwing code:
let result = Result { try load(path) }     // Result<Config, Error>
let config = try result.get()              // throws if .failure
```

`Result` has `map`/`mapError`/`flatMap` for railway-style composition (same idea
as the F#/Rust/TS skills). Prefer `throws` for synchronous call-and-handle; reach
for `Result` when the outcome travels.

## Functional transforms

Operate on collections declaratively instead of index loops:

```swift
let names = users.filter { $0.isActive }.map(\.name)        // keypath shorthand
let total = items.reduce(0) { $0 + $1.price }
let ports = strings.compactMap { Int($0) }                  // map + drop nils
let flat  = nested.flatMap { $0 }                           // flatten one level
let byRole = Dictionary(grouping: users, by: \.role)        // group by key
```

| Want                        | Use                                  |
|-----------------------------|--------------------------------------|
| transform each              | `map` (`.map(\.name)` for a keypath) |
| keep some                   | `filter`                             |
| transform + drop nils       | `compactMap`                         |
| transform + flatten         | `flatMap`                            |
| reduce to one value         | `reduce` (or `sum`-like helpers)     |
| first match                 | `first(where:)`                      |
| any / all                   | `contains(where:)` / `allSatisfy`    |
| group by key                | `Dictionary(grouping:by:)`           |
| count matches (Swift 6)     | `count(where:)`                      |

Prefer the specific operation over a hand-rolled `reduce`. Use **keypath
shorthand** (`\.name`) and **trailing closures** for readability.

## Closures

```swift
let doubled = nums.map { $0 * 2 }                  // trailing closure, $0 shorthand
let sorted = items.sorted { $0.date < $1.date }
let add: (Int, Int) -> Int = { a, b in a + b }     // closure stored in a value

// escaping closures outlive the call (stored, async) — mark them:
func onComplete(_ handler: @escaping (Result<Data, Error>) -> Void) { … }
```

- Use **trailing-closure** syntax (the last closure outside the parens) and `$0`/`$1`
  for short closures; name parameters when it aids clarity.
- Mark a closure **`@escaping`** if it's stored or called after the function
  returns (most async/callback APIs); capture lists `[weak self]` avoid reference
  cycles in class contexts.
- Closures capture by reference by default; use capture lists to control it.

## Rules of thumb

- `throws` (typed where the error set is known) for call-and-handle; `Result` when
  the outcome is stored/passed. Catch specific cases.
- Never `try!`/empty-`catch` in production; handle `try?` nils.
- Transform with `map`/`filter`/`reduce`/`compactMap` and keypaths, not index loops.
