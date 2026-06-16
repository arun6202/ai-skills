# Collections & error handling

Transform data with collection operations instead of index loops, prefer
read-only collections, and reach for sequences when laziness pays. Handle errors
with `Result`/`runCatching` or sealed error types — Kotlin has no checked
exceptions, so failures must be modeled deliberately.

## Read-only by default

```kotlin
val nums = listOf(1, 2, 3)            // read-only List
val set  = setOf("a", "b")
val map  = mapOf("k" to 1)

val mutable = mutableListOf<Int>()    // only when you must mutate
```

- `listOf`/`setOf`/`mapOf` give **read-only** interfaces (`List`, `Set`, `Map`) —
  the default. `mutableListOf`/etc. give `MutableList`/… — use only when you
  genuinely need to add/remove in place.
- Read-only ≠ deeply immutable (the underlying instance could be mutable, and
  elements may be mutable), but exposing `List` rather than `MutableList` documents
  intent and prevents accidental mutation. For true immutability use
  `kotlinx.collections.immutable` (`persistentListOf`).
- Build new collections functionally rather than mutating in a loop.

## Collection operations over loops

Most loops are a `map`/`filter`/`fold`. Name the operation:

```kotlin
// imperative
val names = mutableListOf<String>()
for (u in users) if (u.active) names.add(u.name)

// idiomatic
val names = users.filter { it.active }.map { it.name }
```

| Want                          | Operation                                   |
|-------------------------------|---------------------------------------------|
| transform each                | `map`                                       |
| keep some                     | `filter` (`filterNot`, `filterIsInstance`)  |
| transform + drop nulls        | `mapNotNull`                                |
| transform + flatten           | `flatMap`                                    |
| reduce to one value           | `fold` / `reduce` (or `sumOf`, `maxOfOrNull`)|
| first match                   | `firstOrNull { }` / `find { }`              |
| any / all / none              | `any` / `all` / `none`                      |
| group by key                  | `groupBy { }`                               |
| build a map                   | `associate` / `associateBy` / `associateWith` |
| partition yes/no              | `partition { }`                             |
| de-dupe                       | `distinct` / `distinctBy`                    |

```kotlin
val byRole   = users.groupBy { it.role }
val lookup   = users.associateBy { it.id }       // Map<Id, User>
val total    = items.sumOf { it.price }
val ports    = lines.mapNotNull { it.toIntOrNull() }
```

Prefer the specific operation over a hand-rolled `fold`. Return read-only
collections from functions.

## Sequences for large/lazy pipelines

Eager collection operations create an intermediate list per step. For large
inputs or long chains, `asSequence()` evaluates lazily and element-by-element
(like Java streams / Rust iterators):

```kotlin
val firstMatch = hugeList
    .asSequence()
    .map { transform(it) }
    .filter { it.isValid }
    .first()                      // stops as soon as it finds one; no intermediates
```

Use sequences for big data, expensive steps, or when you only need part of the
result (`first`, `take`). For small lists, eager operations are simpler and fine.

## Error handling — no checked exceptions

Kotlin has exceptions but **no checked exceptions** — nothing forces a caller to
handle them, so model failures you care about explicitly.

### Exceptions for the exceptional

```kotlin
fun load(path: String): Config {
    require(path.isNotBlank()) { "path required" }   // IllegalArgumentException
    val file = File(path)
    check(file.exists()) { "not found: $path" }      // IllegalStateException
    return parse(file.readText())
}
```

- `require(...)` for argument preconditions, `check(...)` for state invariants,
  `error(...)` to throw with a message. These read better than manual `throw`.
- Throw for genuine bugs / unrecoverable situations; don't use exceptions for
  ordinary control flow.

### `Result` and `runCatching`

For "this can fail and the caller should decide", return `Result<T>` or wrap with
`runCatching`:

```kotlin
val result: Result<Int> = runCatching { input.toInt() }

val n = result.getOrElse { 0 }                    // default on failure
result.fold(
    onSuccess = { use(it) },
    onFailure = { log(it) },
)
result.map { it * 2 }.getOrNull()                 // chain transforms
```

`runCatching` catches exceptions into a `Result`; `getOrElse`/`getOrNull`/`fold`/
`map`/`recover` consume it. Good for boundaries (parsing, I/O) where you convert an
exception-throwing API into a value.

### Sealed error types — when callers must branch

When the *kind* of failure matters and you want exhaustive handling (no exceptions
at all), model outcomes as a sealed type — the same approach as the F#/Rust/Swift
skills:

```kotlin
sealed interface ParseResult {
    data class Ok(val value: Int) : ParseResult
    data object Empty : ParseResult
    data class Invalid(val input: String) : ParseResult
}

when (val r = parse(s)) {
    is ParseResult.Ok      -> use(r.value)
    ParseResult.Empty      -> useDefault()
    is ParseResult.Invalid -> report(r.input)
}
```

Choose: `require`/`check`/throw for bugs & preconditions; `Result`/`runCatching`
at boundaries; a sealed result type when callers must branch on the failure kind.

## Rules of thumb

- `listOf`/`mapOf` (read-only) by default; `mutable*` only when needed.
- Transform with `map`/`filter`/`fold`/`groupBy`/`associate`, not index loops.
- `asSequence()` for large/lazy/short-circuiting pipelines.
- Model expected failures (`Result`/sealed types); reserve exceptions for
  preconditions and the truly exceptional.
