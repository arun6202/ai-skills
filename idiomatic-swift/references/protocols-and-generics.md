# Protocols & generics

Swift's signature philosophy is **protocol-oriented programming (POP)**: define
capabilities as protocols, supply shared behavior through protocol extensions, and
**compose** capabilities onto value types — instead of inheriting from base
classes. This, plus generics, is how you get polymorphism without class hierarchies.

## Protocols define capabilities

```swift
protocol Drawable {
    func draw() -> String
}

protocol Named {
    var name: String { get }
}
```

A type *conforms* to a protocol by implementing its requirements. Value types
(`struct`/`enum`) conform just as classes do — so you get polymorphism without
reference semantics:

```swift
struct Circle: Drawable, Named {
    let name = "circle"
    func draw() -> String { "○" }
}
```

## Protocol extensions — shared behavior without inheritance

This is the heart of POP. A protocol *extension* provides **default
implementations** that every conformer gets for free — the composition-friendly
alternative to a base class's inherited methods:

```swift
extension Drawable {
    func drawTwice() -> String { draw() + draw() }     // free for all conformers
}

extension Collection where Element: Numeric {
    var sum: Element { reduce(0, +) }                  // adds `.sum` to arrays of numbers
}
```

- Default methods let you build behavior once and apply it across unrelated types.
- Constrained extensions (`where …`) add behavior only where it makes sense.
- Compose many small protocols rather than one fat base class — a type opts into
  exactly the capabilities it needs.

## Composition over inheritance

The class-inheritance reflex (a base class with shared state/behavior, subclasses
overriding) is usually better as **protocols + extensions + value types**:

```swift
// ❌ inheritance: rigid single-parent hierarchy, reference semantics
class Animal { func speak() -> String { "" } }
class Dog: Animal { override func speak() -> String { "woof" } }

// ✅ protocol + value types: flexible, composable, value semantics
protocol Animal { func speak() -> String }
struct Dog: Animal { func speak() -> String { "woof" } }
struct Cat: Animal { func speak() -> String { "meow" } }
```

Reserve class inheritance for when a framework requires it (`UIViewController`
subclasses) — see `value-types-and-modeling.md`.

## Generics

Write code once that works over any type, with constraints to keep it safe:

```swift
func first<T>(of array: [T]) -> T? { array.first }

func maxOf<T: Comparable>(_ items: [T]) -> T? { items.max() }

// multiple constraints with `where`
func merge<S>(_ a: S, _ b: S) -> [S.Element] where S: Sequence {
    Array(a) + Array(b)
}
```

Generics are monomorphized — zero-cost, fully type-checked. Constrain type
parameters with protocols (`T: Comparable`, `T: Hashable`) so the body can use
those capabilities.

## `some` vs `any` — opaque vs existential

Swift 5.7+ makes the choice explicit, and it matters for performance and meaning:

```swift
// `some`: opaque type — ONE concrete type, hidden from the caller. Zero-cost.
func makeShape() -> some Drawable { Circle() }     // always returns a Circle, caller just knows it's Drawable

// `any`: existential — a box that can hold ANY conforming type. Heterogeneous, has overhead.
let shapes: [any Drawable] = [Circle(), Square()]  // mixed concrete types
func render(_ shape: any Drawable) { … }
```

- **`some Protocol`** — opaque: the compiler knows the single underlying type;
  cheap, preserves type identity. Prefer it for return types and parameters when
  one concrete type flows through.
- **`any Protocol`** — existential: a runtime box allowing different concrete types
  in the same variable/collection; necessary for heterogeneity, but adds
  indirection. Use when you genuinely need a mixed bag.
- Rule of thumb: reach for **`some`** by default; use **`any`** only when you must
  store/pass differing concrete types together.

## Associated types — generic protocols

A protocol can have a placeholder type its conformers fill in:

```swift
protocol Container {
    associatedtype Item
    var count: Int { get }
    func item(at index: Int) -> Item
}
```

Constrain them in use with `where` or primary associated types
(`some Container<Int>`). This is how `Sequence`/`Collection` work.

## Retroactive conformance & `Equatable`/`Hashable`/`Codable`

- Add a protocol to a type you don't own via an extension (mind warnings about
  retroactive conformance across modules).
- Get value-equality and hashing for free by declaring conformance — the compiler
  synthesizes it for structs/enums whose members are themselves `Equatable`/
  `Hashable`:
  ```swift
  struct Point: Equatable, Hashable { var x: Int; var y: Int }
  ```
- `Codable` similarly synthesizes JSON (de)serialization — declare conformance and
  it's generated.

## Checklist

- [ ] Model capabilities as small protocols; share behavior via protocol extensions.
- [ ] Compose protocols onto value types instead of inheriting from base classes.
- [ ] Generics with protocol constraints for reusable, zero-cost polymorphism.
- [ ] `some` by default; `any` only for heterogeneous storage.
- [ ] Let the compiler synthesize `Equatable`/`Hashable`/`Codable`.
