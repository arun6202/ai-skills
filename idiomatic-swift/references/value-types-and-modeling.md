# Value types & modeling

Swift's defining choice: prefer **value types** (`struct`, `enum`) with value
semantics over **reference types** (`class`). Values are copied on assignment, so
there's no shared mutable state to reason about — the foundation of safe, local,
predictable code. Reach for a `class` only when you specifically need reference
semantics.

## Struct vs class — value vs reference

```swift
struct Point { var x: Double; var y: Double }   // value type: copied on assignment

var a = Point(x: 1, y: 2)
var b = a            // b is an independent copy
b.x = 99             // a.x is still 1 — no aliasing
```

- **`struct`** (and `enum`) — value semantics, copied, no shared identity, thread-
  friendly. **The default for data.** Stored on the stack / inline where possible.
- **`class`** — reference semantics, shared identity, heap-allocated, ARC-managed.
  Two variables can point at the *same* instance, so a mutation through one is seen
  by the other.

The Objective-C/Java reflex is "everything is a class." In Swift, **start with a
struct** and switch to a class only for a concrete reason (below).

### When a `class` is the right call

- **Reference identity matters** — two things are "the same object", not just equal
  values (a shared cache, a connection, a node others hold a reference to).
- **Inheritance is required** — you must subclass a framework base type
  (`UIViewController`, `NSObject`) or model an open class hierarchy.
- **Objective-C interop** / `AnyObject` constraints / KVO.
- **Identity-based observation** or deinit-driven cleanup (`deinit`).

When you do use a class, mark it **`final`** unless it's designed for subclassing —
it documents intent and lets the compiler devirtualize.

## Enums with associated values — algebraic data types

Swift enums are real sum types: each case can carry its own data. This is the
workhorse for variants, states, and outcomes — and it makes illegal states
impossible.

```swift
enum NetworkState {
    case idle
    case loading
    case loaded(Data)
    case failed(Error)
}
```

Consume with an exhaustive `switch` (see `pattern-matching.md`). Adding a case
forces every switch to handle it — the compiler enforces completeness. This beats
a `class` hierarchy or a `Vec<Box<dyn>>`-style design for a *closed* set of
variants: no allocation, no dynamic dispatch, and exhaustiveness checking.

`Optional<T>` and `Result<Success, Failure>` are themselves enums — the core of
absence and failure modeling.

## Make illegal states unrepresentable

Model so bad combinations can't be constructed, then never re-check them:

```swift
// ❌ illegal states representable: isLoading && error set, loaded with no data…
struct RequestState {
    var isLoading: Bool
    var data: Data?
    var error: Error?
}

// ✅ exactly one state
enum RequestState {
    case loading
    case loaded(Data)
    case failed(Error)
}
```

Same payoff as F# DUs / Rust enums / TS discriminated unions: `data` is reachable
only in `.loaded`.

## Newtypes — constrained values

Wrap a primitive in a small `struct` whose initializer validates, so an
unvalidated value can't masquerade as a valid one ("parse, don't validate"):

```swift
struct Email {
    let value: String
    init?(_ raw: String) {                 // failable init -> Email?
        guard raw.contains("@") else { return nil }
        self.value = raw
    }
}
```

Use a **failable initializer** (`init?`) for "returns nil on bad input", or a
**throwing initializer** (`init throws`) when you want a typed reason. A function
taking `Email` then can't be handed a raw `String`.

## `let` vs `var`, and `mutating`

- Default to **`let`** (immutable binding); use `var` only when the value changes.
- A `let` struct is **deeply immutable** — you can't mutate its `var` properties
  either. (A `let` class reference is constant, but the instance's `var`s can still
  change — another reason to prefer structs.)
- Methods on a struct/enum that change `self` must be marked **`mutating`**:
  ```swift
  struct Counter {
      private(set) var count = 0
      mutating func increment() { count += 1 }
  }
  ```
- Prefer returning a new value over mutating where it reads well; use `mutating`
  for in-place updates on `var` instances.

## Access control & encapsulation

Use `private`/`fileprivate`/`internal`/`public`/`open` to encapsulate. A common
idiom is `private(set)` — readable everywhere, writable only inside the type:

```swift
struct BankAccount {
    private(set) var balance: Decimal
    mutating func deposit(_ amount: Decimal) { balance += amount }
}
```

## Modeling checklist

- [ ] Default to `struct`/`enum`; reach for `class` only for identity/inheritance/interop (and make it `final`).
- [ ] "One of N" → `enum` with associated values; "all of" → `struct`.
- [ ] Can an illegal value be constructed? Push the rule into the type (enum cases, failable init).
- [ ] Constrained primitives are newtype structs with `init?`/`init throws`.
- [ ] `let` by default; `mutating` for in-place struct updates; `private(set)` to encapsulate.
