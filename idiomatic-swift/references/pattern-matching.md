# Pattern matching

`switch` is Swift's primary branching and decomposition tool — exhaustive, and
able to bind associated values, match ranges/tuples, and guard with `where`. Use
it to consume enums and to replace `if`/`else if` ladders.

## `switch` is exhaustive

```swift
enum Direction { case north, south, east, west }

func describe(_ d: Direction) -> String {
    switch d {
    case .north: "going up"
    case .south: "going down"
    case .east:  "going right"
    case .west:  "going left"
    }   // no `default` needed — all cases covered; adding a case forces an update
}
```

- The compiler requires every case be handled. For an `enum` you own, **avoid
  `default`** so a new case surfaces as an error rather than silently hitting the
  catch-all.
- Cases don't fall through (no implicit C-style fallthrough); use `fallthrough`
  explicitly in the rare case you want it. Combine cases with commas:
  `case .east, .west:`.

## Binding associated values

The main reason enums + switch are so powerful — destructure the payload:

```swift
enum Shape {
    case circle(radius: Double)
    case rectangle(width: Double, height: Double)
}

switch shape {
case let .circle(radius):
    return .pi * radius * radius
case let .rectangle(width, height):
    return width * height
}
```

`case let .circle(radius)` binds the associated value. (`let` can go inside —
`case .circle(let radius)` — or outside the case as shown.)

## `where` clauses, ranges, tuples

```swift
switch (point.x, point.y) {
case (0, 0):              "origin"
case let (x, 0):          "on x-axis at \(x)"
case let (x, y) where x == y: "on diagonal"
case (-10...10, -10...10): "near origin"
default:                  "elsewhere"
}

switch score {
case ..<0:      "invalid"
case 0..<60:    "fail"
case 60...100:  "pass"
default:        "out of range"
}
```

- **`where`** adds a condition a pattern can't express.
- **Ranges** (`0..<60`, `60...100`, `..<0`) match numeric/comparable values.
- **Tuples** let you switch on several values at once (a tidy decision table /
  state machine).
- Bind with `let`/`var`; use `_` to ignore parts.

## `if case` / `guard case` — match one pattern

When you care about a single case, `if case`/`guard case` avoid a full `switch`:

```swift
if case .loaded(let data) = state {
    render(data)
}

guard case .success(let value) = result else { return }
use(value)               // bound for the rest of the scope
```

## `for case` — filter while iterating

```swift
// only the .loaded cases, with their data:
for case let .loaded(data) in states { process(data) }

// only non-nil (optional pattern):
for case let name? in optionalNames { print(name) }
```

## `switch` and `if` as expressions (Swift 5.9+)

Branches can produce a value directly, assigned or returned:

```swift
let label = switch score {
    case ..<60: "fail"
    default:    "pass"
}

let icon = if isActive { "●" } else { "○" }
```

Each branch must be a single expression of the same type. This makes total
functions read cleanly — no mutable `var` filled in across branches.

## `is` / `as?` type patterns (use sparingly)

```swift
switch value {
case let s as String: …
case let n as Int:    …
default:              …
}
```

Type-casting patterns are for genuine heterogeneous/`Any` situations and interop.
Inside your own code, model the variants as an `enum` and match cases instead of
downcasting.

## Anti-patterns

- Don't add `default` to a `switch` over your own `enum` just to silence the
  compiler — list the cases so additions force a decision.
- Don't reach for `if let x = opt { } else { }` chains where a `switch` or
  `guard` reads better.
- Don't downcast with `as?`/`as!` where an `enum` + associated values models the
  variants.
