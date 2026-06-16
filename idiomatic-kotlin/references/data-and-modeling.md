# Data & modeling

Model data with `data class` (products) and `sealed` types (sums), keep it
immutable with `val`, and make illegal states impossible. This replaces Java's
POJOs-with-getters-and-setters and inheritance hierarchies.

## Data classes — products without boilerplate

```kotlin
data class Customer(
    val name: String,
    val email: Email,
    val since: LocalDate,
)
```

One line gives you a constructor, `val` properties (read via `customer.name`),
`equals`/`hashCode` (value equality), `toString`, `componentN` (destructuring),
and **`copy`**. Never hand-write a POJO with getters/setters again.

- **`copy` is your "change" operation** — produce a new value, don't mutate:
  ```kotlin
  val renamed = customer.copy(name = "Ada")
  ```
- **Destructuring** falls out of `componentN`:
  ```kotlin
  val (name, email) = customer
  ```
- Use **`val`** properties so instances are immutable. A `data class` with `var`s
  is a mutable value object — usually a smell; prefer `val` + `copy`.
- Keep data classes as pure data; put behavior in functions/extensions, not a pile
  of methods.

## `val` vs `var` and immutability

- Default to **`val`** (read-only binding); use `var` only when the value really
  changes. Most Kotlin code is `val`-heavy.
- Prefer immutable structures and `copy` over in-place mutation — easier to reason
  about and concurrency-friendly.
- Note: a `val` of a mutable type (e.g. `val list = mutableListOf<…>()`) still lets
  you mutate the *contents*; reach for read-only collections (`listOf`) by default
  (see `collections-and-errors.md`).

## Sealed classes / interfaces — sum types (ADTs)

A `sealed` type has a fixed, compiler-known set of subtypes — Kotlin's algebraic
sum type, ideal for state machines, API responses, and any "one of these":

```kotlin
sealed interface NetworkState {
    data object Idle : NetworkState
    data object Loading : NetworkState
    data class Loaded(val data: Data) : NetworkState
    data class Failed(val error: Throwable) : NetworkState
}
```

Consume with an **exhaustive `when`** — because the set is closed, no `else` is
needed, and adding a case turns every `when` into a compile error until handled
(see `when-and-control-flow.md`):

```kotlin
fun describe(state: NetworkState): String = when (state) {
    NetworkState.Idle      -> "idle"
    NetworkState.Loading   -> "loading"
    is NetworkState.Loaded -> "loaded ${state.data}"   // smart cast
    is NetworkState.Failed -> "error: ${state.error.message}"
}
```

- Prefer **`sealed interface`** over `sealed class` when you don't need shared
  state — it allows a type to participate in multiple hierarchies.
- Use **`data object`** for stateless cases (singletons with a nice `toString`).
- This beats an inheritance hierarchy or `enum`-plus-payload-maps for closed
  variants: exhaustiveness, associated data per case, no `else` escape hatch.

### Enums for simple closed sets

When cases carry no per-case data, an `enum class` is enough (and can hold shared
properties/methods):

```kotlin
enum class Direction(val degrees: Int) { NORTH(0), EAST(90), SOUTH(180), WEST(270) }
```

`when` over an enum is also exhaustive. Reach for a sealed type the moment cases
need different associated data.

## Make illegal states unrepresentable

Model so bad combinations can't be built, then never re-check them:

```kotlin
// ❌ illegal states representable: loading && error, loaded with null data…
data class State(val isLoading: Boolean, val data: Data?, val error: String?)

// ✅ exactly one state
sealed interface State {
    data object Loading : State
    data class Loaded(val data: Data) : State
    data class Failed(val error: String) : State
}
```

Same discipline as the F#/Rust/Swift/TS skills: `data` is reachable only in
`Loaded`.

## Value classes — zero-cost newtypes

Wrap a primitive to give it a distinct type (and prevent mixups) with no runtime
allocation via `@JvmInline value class`:

```kotlin
@JvmInline value class UserId(val value: String)
@JvmInline value class Email private constructor(val value: String) {
    companion object {
        fun parse(raw: String): Email? = if ("@" in raw) Email(raw) else null
    }
}
```

A function taking `UserId` then can't be handed an arbitrary `String`. Add a
validating factory (a `companion object` function or top-level `fun`) for "parse,
don't validate".

## Classes & interfaces (when you need them)

Regular `class` for types with identity/behavior/mutable state; `interface` for
contracts (with optional default implementations — favor composition). Mark
classes `final` (the Kotlin default) unless designed for inheritance with `open`.
Prefer **composition and delegation** (`by`) over inheritance:

```kotlin
class Logger(out: Appendable) : Appendable by out   // delegation, no inheritance
```

## Modeling checklist

- [ ] Data bundles are `data class`es with `val`s; "change" via `copy`.
- [ ] "One of N" → `sealed interface`/`class` (+ `data object` for stateless cases).
- [ ] Can an illegal value be constructed? Push the rule into the type.
- [ ] Constrained primitives are `value class`es with validating factories.
- [ ] Prefer composition/delegation (`by`) to `open` inheritance.
