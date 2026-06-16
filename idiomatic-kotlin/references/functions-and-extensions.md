# Functions, extensions & scope functions

Kotlin's functional toolkit: top-level and extension functions instead of utility
classes, lambdas and higher-order functions, named/default arguments instead of
builders and overloads, and the five scope functions used with intent.

## Top-level & extension functions — no utility classes

Functions don't need a class. Put them at the top level of a file, or **extend an
existing type** so the call reads naturally — Kotlin's signature feature:

```kotlin
// top-level function — no `Utils` class needed
fun slugify(s: String): String = s.lowercase().replace(Regex("\\s+"), "-")

// extension function — adds `truncate` to String without subclassing
fun String.truncate(max: Int): String =
    if (length <= max) this else take(max) + "…"

"Hello World".truncate(5)        // reads like a member; resolved statically
```

Extensions are resolved statically (no real method added to the type) and respect
visibility — great for adapting types you don't own and for readable, chainable
APIs. Prefer them over `StringUtils.truncate(s, 5)`-style helpers.

## Named & default arguments — not builders

Default values + named arguments replace telescoping constructors, the builder
pattern, and most overloads:

```kotlin
fun connect(
    host: String,
    port: Int = 443,
    timeoutMs: Int = 30_000,
    retries: Int = 3,
) { … }

connect("example.com")                       // uses defaults
connect("example.com", timeoutMs = 60_000)   // name the one you change
```

Use **named arguments** at call sites with multiple/boolean params for readability
(`copy(active = true)`), and default values to collapse overloads.

## Lambdas & higher-order functions

Functions are values; pass behavior directly:

```kotlin
fun <T> List<T>.firstOr(default: T, pred: (T) -> Boolean): T =
    firstOrNull(pred) ?: default

// trailing-lambda syntax: a final lambda param goes outside the parens
val evens = numbers.filter { it % 2 == 0 }        // `it` = single implicit param
items.forEach { item -> process(item) }
val sum = numbers.fold(0) { acc, n -> acc + n }
```

- **Trailing lambda**: when the last parameter is a function, write it outside the
  call's parentheses (`list.map { }`). If it's the only argument, drop the parens.
- **`it`** is the implicit name for a single lambda parameter; name it when it aids
  clarity or when nesting.
- **Function references**: `numbers.map(::area)`, `list.map(String::trim)`.

## `inline` and reified types

Mark higher-order functions `inline` to eliminate lambda allocation and enable
`reified` type parameters (access a generic type at runtime):

```kotlin
inline fun <reified T> Gson.fromJson(json: String): T =
    fromJson(json, T::class.java)        // T is available because of `reified`
```

Use `inline` for small higher-order functions in hot paths and where you need
`reified`; don't inline large bodies.

## The five scope functions — use with intent

`let`, `run`, `with`, `apply`, `also` all execute a block on an object; they
differ in (a) how the object is referenced (`it` vs `this`) and (b) what they
return (the block's result vs the object). Pick by **purpose**:

| Function | Object as | Returns        | Use for…                                    |
|----------|-----------|----------------|---------------------------------------------|
| `let`    | `it`      | block result   | null-checks (`?.let`), transform a value    |
| `run`    | `this`    | block result   | compute a result from an object / scoping   |
| `with`   | `this`    | block result   | operate on an object (non-extension `run`)  |
| `apply`  | `this`    | the object     | configure/initialize an object              |
| `also`   | `it`      | the object     | side effects (logging, validation) in a chain |

```kotlin
// let: null-check + transform
val len = name?.let { it.trim().length } ?: 0

// apply: configure and return the object
val request = Request().apply {
    method = "POST"
    headers["Accept"] = "application/json"
}

// also: a side effect mid-chain, returns the receiver
val user = loadUser(id).also { log.info("loaded $it") }

// run: scope a computation, return its result
val area = with(rectangle) { width * height }
```

Choose by intent: **`apply`** to configure (returns receiver), **`also`** for side
effects (returns receiver), **`let`** for null-safe transforms (returns result),
**`run`/`with`** to compute from an object (returns result). Don't nest or chain
scope functions into puzzles — if it's not instantly readable, use a plain `val`.

## `infix`, operator functions, and `companion object`

```kotlin
infix fun Int.clampedTo(max: Int) = minOf(this, max)   // `5 clampedTo 3`
operator fun Vec.plus(o: Vec) = Vec(x + o.x, y + o.y)   // enables `a + b`

class User private constructor(val name: String) {
    companion object {                                   // factory home
        fun of(name: String): User = User(name.trim())
    }
}
```

Use `infix`/`operator` sparingly for genuinely natural notation. Keep
`companion object` for factories and constants — don't let it become a static
dumping ground; prefer top-level/extension functions for free-standing helpers.
