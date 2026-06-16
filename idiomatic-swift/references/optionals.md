# Optionals

Swift has no `null` — absence is modeled by `Optional<T>` (written `T?`), an enum
of `.some(T)` or `.none`. The compiler forces you to deal with the absent case, so
"unexpectedly nil" crashes are largely designed out — *unless* you force-unwrap.
The whole game is **unwrap safely**; `!` is the smell to avoid.

## What an optional is

```swift
var name: String?          // String or nil
name = "Ada"
name = nil

func find(id: Int) -> User?    // "maybe a user"
```

`T?` is sugar for `Optional<T>`; `nil` is `Optional.none`. You can't use a `T?`
where a `T` is expected — you must unwrap first.

## Safe unwrapping

### `if let` (and shorthand)

```swift
if let user = find(id: 42) {
    greet(user)            // `user` is non-optional User in here
}

// Swift 5.7+ shorthand when names match:
if let user { use(user) }

// bind several; all must be non-nil:
if let user, let email = user.email { send(to: email) }
```

### `guard let` — early exit, keep the happy path flat

Prefer `guard` when nil means "can't continue" — it unwraps for the *rest of the
scope* and forces you to bail in the `else`:

```swift
func process(_ input: String) -> Int? {
    guard let n = Int(input) else { return nil }
    return n * 2           // `n` is in scope, non-optional, for the whole function
}
```

`guard let … else { return / throw / break / continue }` avoids the "pyramid of
`if let`" and keeps the main logic unindented.

### `??` nil-coalescing

Supply a default for nil:

```swift
let display = name ?? "Anonymous"
let port = Int(envPort ?? "") ?? 8080      // chain defaults
```

### Optional chaining `?.`

Reach through optionals; the whole expression becomes nil if any link is nil:

```swift
let city = user?.address?.city          // String?
let count = user?.friends?.count ?? 0
user?.save()                            // call only if non-nil
```

## Avoid force-unwrap `!`

`value!` crashes if `value` is nil. It throws away exactly the safety optionals
give you. Avoid it in real code:

```swift
let n = Int(input)!          // ❌ crashes on bad input
guard let n = Int(input) else { … }   // ✅
```

Acceptable uses of `!` are narrow: tests, `@IBOutlet`s, or a value you can *prove*
is non-nil (e.g. a hardcoded `URL(string: "https://…")!` literal) — and even then
prefer a safe path. Implicitly-unwrapped optionals (`T!`) have the same caveat: use
only for two-phase init (outlets), never as a convenience to skip unwrapping.

## Transform optionals functionally

Operate on the wrapped value without unwrapping:

```swift
let length = name.map { $0.count }            // String? -> Int?
let parsed = text.flatMap { Int($0) }         // avoid Int?? — flatMap flattens
let trimmed = name.map { $0.trimmingCharacters(in: .whitespaces) }
```

- `map` applies a function if present, returns `nil` otherwise.
- `flatMap` is `map` for functions that themselves return an optional (flattens
  `T??` → `T?`).

## Optionals in `switch` / patterns

```swift
switch find(id: id) {
case .some(let user): greet(user)
case .none: showLogin()
}

// or with `?` sugar and where clauses:
switch result {
case let user? where user.isAdmin: …
case let user?: …
case nil: …
}
```

`if case .some(let x)` and `for case let x?` let you pattern-match optionals in
conditions and loops (see `pattern-matching.md`):

```swift
for case let name? in [Optional("a"), nil, Optional("b")] { print(name) }  // a, b
```

## Rules of thumb

- Model "maybe absent" as `T?`; never invent sentinels (`-1`, `""`).
- Unwrap with `if let` / `guard let` / `??` / `?.` — `guard` for early exit.
- Don't force-unwrap (`!`) or force-cast (`as!`) in production; reserve for tests
  or provable invariants.
- Use `map`/`flatMap` to transform without unwrapping; `compactMap` to drop nils
  from a collection (see `errors-and-functional.md`).
