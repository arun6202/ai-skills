---
name: idiomatic-swift
description: >-
  Write, refactor, or review idiomatic Swift (.swift, SwiftPM/Xcode projects) —
  even a quick "write this in Swift". Steers toward value-oriented,
  protocol-oriented Swift: structs and enums over classes, enums with associated
  values + exhaustive `switch` over type tags and inheritance, optionals safely
  unwrapped over force-unwrap `!`, protocols + extensions over class hierarchies,
  `Result`/`throws` (typed throws) over swallowed errors, `let` over `var`, and
  safe concurrency with async/await + actors + `Sendable`. Reach for it when
  modeling data, choosing struct vs class, handling optionals or errors, replacing
  inheritance, or adopting Swift 6 strict concurrency. Targets Swift 6 (data-race
  safety) and 6.2 (approachable concurrency). Counters OOP/Objective-C muscle
  memory.
---

# Idiomatic Swift

Swift is a value-oriented, protocol-oriented, type-driven language — structs and
enums with value semantics, enums with associated values (real algebraic data
types), optionals instead of null, exhaustive `switch`, `Result`/`throws`, and
since Swift 6, compile-time data-race safety. Most "bad Swift" is **Objective-C /
Java muscle memory**: reaching for `class` by default, building inheritance
hierarchies, force-unwrapping optionals, and `var` everywhere.

The prime directive: **prefer value types and protocols.** Model data with
`struct`/`enum`, share behavior with protocols + extensions (not inheritance),
make absence explicit with optionals, and let the type system carry the rules.
Reach for a `class` only when you genuinely need reference identity, inheritance,
or Objective-C interop.

> **Part of the `idiomatic-code` family** — the shared cross-language philosophy and the Rosetta Stone (porting + review) live there.
>
> Stack family: Swift sits right beside F#, Rust, and TypeScript — value
> semantics, enums-as-discriminated-unions, optionals-not-null, exhaustive
> matching, and `Result` are the same philosophy. Swift's distinctive
> contribution is **protocol-oriented programming** (composition via protocol
> extensions), and it's gaining Rust-like ownership (`~Copyable`,
> `borrowing`/`consuming`).

## Break the muscle memory (reflex → idiomatic)

When your instinct fires the left column, write the right column instead.

| Reflex (OOP / Java / Objective-C habit)             | Idiomatic Swift                                                      |
|-----------------------------------------------------|---------------------------------------------------------------------|
| `class` for a data model                            | `struct` (value semantics); `class` only for identity/inheritance/interop |
| Force-unwrap `optional!`                            | `if let` / `guard let` / `??` / optional chaining `?.`             |
| Class inheritance hierarchy                          | Protocols + protocol extensions (composition over inheritance)      |
| `var` everywhere                                    | `let` by default; `var` only when it changes                       |
| `NSObject` subclassing, KVO, ObjC-isms              | Swift-native value types + protocols                               |
| Stringly-typed states / boolean flags               | `enum` with associated values                                       |
| `try!` / empty `catch {}`                           | `do/catch`, `try?` *with handling*, typed `throws`                 |
| nil-check then force-unwrap                          | `guard let … else { return }` early exit                           |
| Shared mutable reference state                       | Value types (copies); `inout`/return; an `actor` for shared state  |
| Completion-handler callback pyramids                | `async`/`await` + structured concurrency                           |
| Ignoring data races                                 | `Sendable` + actors (Swift 6 data-race safety)                     |
| Massive view controller / god class                 | Small value types, focused protocols, composition                  |
| `for i in 0..<a.count { a[i] }`                     | `for x in a`, or `map`/`filter`/`reduce`                            |

If you genuinely need reference semantics (shared identity, a class hierarchy
required by a framework, `AnyObject`/ObjC interop), use a `class` — `final` by
default. Make it a decision, not a reflex.

## The creed

1. **Value types by default.** `struct`/`enum` with value semantics; `class` only
   for identity, required inheritance, or interop.
2. **No null.** Optionals, unwrapped safely (`if let`/`guard let`/`??`/`?.`).
   Force-unwrap `!` and `try!` are smells outside tests/provable invariants.
3. **Make illegal states unrepresentable.** `enum` with associated values for
   "one of", `struct` for "all of", then `switch` exhaustively.
4. **Protocol-oriented, not inheritance.** Protocols + protocol extensions for
   shared behavior; compose capabilities.
5. **Errors are values, typed and handled.** `throws`/typed `throws`/`Result`;
   never force-try or swallow.
6. **Immutable by default.** `let`; mutate through value semantics and `mutating`
   methods.
7. **Concurrency is safe.** `async`/`await`, `actor`s, `Sendable`; embrace Swift 6
   data-race safety rather than working around it.

## Quick reach-for guide

| You need to…                              | Reach for…                                                       |
|-------------------------------------------|------------------------------------------------------------------|
| A data bundle                             | `struct` (value type)                                            |
| "One of N shapes" / a state              | `enum` with associated values + exhaustive `switch`              |
| Constrain a primitive (Email, UserID)     | A `struct` newtype with a failable/throwing init                |
| "Maybe absent"                            | `Optional<T>` (`T?`) + safe unwrapping                           |
| "Succeeds or fails"                       | `throws` (typed) or `Result<T, E>`                              |
| Share behavior across types               | A `protocol` + `extension` (default impls)                      |
| Early-exit on nil/failure                 | `guard let … else { return }`                                   |
| Polymorphic return, one type              | `some Protocol` (opaque); `any Protocol` for heterogeneous       |
| Concurrent work                           | `async`/`await`, `async let`, task groups, `actor`              |

## Reference files — read on demand

- **`references/value-types-and-modeling.md`** — struct vs class (value vs
  reference semantics), enums with associated values, illegal-states-
  unrepresentable, `let`/`var`, `mutating`, newtypes, when a class is right.
  *Read when modeling data.*
- **`references/optionals.md`** — `Optional`, `if let`/`guard let`/shorthand, `??`,
  optional chaining, avoiding force-unwrap, `map`/`flatMap` on optionals. *Read for
  any "maybe absent" value.*
- **`references/pattern-matching.md`** — `switch` exhaustiveness, associated-value
  binding, `where` clauses, `if case`/`guard case`/`for case`, `switch`/`if`
  expressions. *Read for branching.*
- **`references/protocols-and-generics.md`** — protocol-oriented programming,
  protocol extensions, composition over inheritance, generics + constraints,
  `some` vs `any` (opaque vs existential). *Read for abstraction.*
- **`references/errors-and-functional.md`** — `throws`/`try`/`do-catch`, typed
  throws, `Result`, `try?`/`try!`, plus `map`/`filter`/`reduce`/`compactMap`,
  closures, trailing-closure syntax. *Read for error handling or data transforms.*
- **`references/concurrency-and-tooling.md`** — `async`/`await`, structured
  concurrency, `actor`s, `Sendable`, Swift 6 data-race safety & 6.2 approachable
  concurrency; SwiftPM, Swift Testing, SwiftLint, macros, ownership (`~Copyable`).
  *Read for concurrency or project setup.*

## A taste

```swift
enum Shape {
    case circle(radius: Double)
    case rectangle(width: Double, height: Double)
}

func area(of shape: Shape) -> Double {        // value type in, no class
    switch shape {                             // exhaustive: a new case won't compile until handled
    case let .circle(radius):
        return .pi * radius * radius
    case let .rectangle(width, height):
        return width * height
    }
}

func totalArea(of shapes: [Shape]) -> Double {
    shapes.map(area(of:)).reduce(0, +)         // functional pipeline, value semantics
}
```

No class, no force-unwrap, no inheritance, exhaustive matching, value semantics —
and the `enum` *is* the documentation. That is the target for all Swift here.
