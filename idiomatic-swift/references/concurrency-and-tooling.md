# Concurrency & tooling

Modern Swift concurrency is `async`/`await` + structured concurrency + `actor`s,
and since **Swift 6** the compiler enforces **data-race safety** at compile time.
Embrace it rather than working around it. Plus the project tooling that keeps code
idiomatic.

## async/await

A function that suspends is `async`; you call it with `await`. This replaces
completion-handler callback pyramids with straight-line code:

```swift
func fetchUser(_ id: Int) async throws -> User {
    let (data, _) = try await URLSession.shared.data(from: url(id))
    return try JSONDecoder().decode(User.self, from: data)
}

let user = try await fetchUser(42)     // reads sequentially, runs asynchronously
```

`await` marks a suspension point (where the task may yield). `async` composes with
`throws`: `async throws`, called as `try await`.

## Structured concurrency

Run child tasks concurrently and have the compiler manage their lifetimes —
children can't outlive the parent scope, and errors/cancellation propagate.

```swift
// run two in parallel, await both:
async let a = fetchA()
async let b = fetchB()
let (x, y) = try await (a, b)

// dynamic fan-out with a task group:
let results = try await withThrowingTaskGroup(of: Data.self) { group in
    for url in urls { group.addTask { try await fetch(url) } }
    var all: [Data] = []
    for try await data in group { all.append(data) }
    return all
}
```

- `async let` for a fixed number of concurrent children.
- task groups for a dynamic number.
- Prefer structured concurrency to detached `Task { }` — it gives automatic
  cancellation and error propagation. Use `Task { }` only to bridge from
  synchronous contexts; check `Task.isCancelled`/`try Task.checkCancellation()`.

## Actors — safe shared mutable state

An `actor` protects its mutable state by serializing access; you `await` its
methods from outside (only one runs at a time), so there are no data races:

```swift
actor Counter {
    private var value = 0
    func increment() { value += 1 }     // isolated; safe
    func get() -> Int { value }
}

let counter = Counter()
await counter.increment()               // await: cross-actor hop
let n = await counter.get()
```

`@MainActor` pins code to the main thread — use it for UI types:

```swift
@MainActor
final class ViewModel { var items: [Item] = [] }   // all access on the main actor
```

## Swift 6 data-race safety & `Sendable`

The Swift 6 language mode makes the compiler **prove** your concurrent code is
race-free. The key concept is **`Sendable`** — a type that's safe to pass across
concurrency boundaries:

- Value types of `Sendable` members are automatically `Sendable`.
- Mark your own safe types `Sendable` (often automatic for `struct`/`enum`); the
  compiler errors if you try to send something unsafe (e.g. a mutable class).
- Immutable data (`let` value types) and actors are the easy path to `Sendable`.

```swift
struct Message: Sendable { let text: String }       // safe to cross boundaries
```

When the compiler flags a data race, fix the *design* (make it a value type,
isolate it to an actor, mark it `Sendable`) rather than reaching for `@unchecked
Sendable` — that's an unsafe escape hatch, used only with a proven invariant.

## Swift 6.2 — approachable concurrency

Swift 6.2 makes concurrency easier to adopt, including an opt-in mode where code
is **isolated to the main actor by default** — so ordinary app code is single-
threaded-and-safe without annotation ceremony, and you opt *out* (with `nonisolated`
or by moving work to a background actor/`Task`) when you need parallelism. For new
app targets, enabling approachable concurrency from the start means the defaults do
the safe thing with less boilerplate. (Library code still annotates isolation
explicitly.)

## Ownership: noncopyable types (advanced, opt-in)

Swift has Rust-like ownership tools for performance-critical / resource types:

- **`~Copyable`** structs/enums can't be implicitly copied — enforcing single
  ownership (e.g. a file handle that must be closed exactly once).
- Parameter ownership modifiers: **`borrowing`** (temporary read access, the
  default for methods), **`consuming`** (takes ownership; the original becomes
  invalid), **`inout`** (temporary write access).

```swift
struct FileHandle: ~Copyable {
    consuming func close() { /* … */ }    // consumes self; can't be used after
}
```

Reach for these only when you need move-only semantics or to avoid copies in a hot
path — ordinary Swift stays `Copyable` with value semantics.

## Tooling

- **Swift Package Manager** — `Package.swift` manifest; `swift build` / `swift test`
  / `swift run`. The standard for dependencies and cross-platform (macOS, Linux,
  Windows) projects. Manage toolchains with **swiftly**.
- **Swift Testing** — the modern test framework (`@Test` functions, `#expect(...)`
  / `#require(...)` macros, parameterized tests), alongside or replacing XCTest:
  ```swift
  import Testing
  @Test func parsesPort() {
      #expect(parsePort("8080") == 8080)
  }
  ```
- **Macros** (Swift 5.9+) — compile-time code generation (`@Observable`,
  `#Predicate`, your own `@attached`/`#freestanding` macros). Powerful; use
  existing ones freely, write your own sparingly.
- **SwiftLint** / **swift-format** — linting and canonical formatting; run in CI.
- **`if`/`switch` expressions**, **parameter packs**, and **`Codable`** synthesis
  (Swift 5.9+) reduce boilerplate — prefer them.

## Checklist

- [ ] `async`/`await` + structured concurrency (`async let`, task groups) over
      callbacks and bare `Task { }`.
- [ ] Shared mutable state lives in an `actor`; UI types are `@MainActor`.
- [ ] Adopt Swift 6 data-race safety; make types `Sendable` by design, not
      `@unchecked`.
- [ ] New app targets: consider 6.2 approachable (main-actor-default) concurrency.
- [ ] SwiftPM + Swift Testing + SwiftLint/swift-format in CI.
