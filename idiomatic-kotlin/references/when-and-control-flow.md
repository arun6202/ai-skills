# `when` & control flow

Kotlin is expression-oriented: `when`, `if`, and `try` all return values. `when`
is the workhorse — exhaustive over sealed types and enums, with smart casts and
(since 2.1) guard conditions. Use it instead of `if`/`else if` ladders and
Java-style `switch`.

## `when` as an expression

```kotlin
val label = when {
    n < 0  -> "negative"
    n == 0 -> "zero"
    else   -> "positive"
}
```

Two forms:
- **With a subject** — `when (x) { … }`: matches `x` against values, ranges, types.
- **Without a subject** — `when { cond -> … }`: a clean replacement for an
  `if`/`else if` chain.

Each branch is `condition -> expression`. As an expression, `when` must be
exhaustive (covers all cases or has `else`).

## Matching a subject

```kotlin
when (x) {
    0, 1        -> "small"          // multiple values
    in 2..9     -> "single digit"   // range
    in special  -> "special"        // membership (collection)
    is String   -> "text: ${x.length}"   // type test + smart cast
    else        -> "other"
}
```

- Comma-separated values, `in range`/`in collection`, `is Type` (with smart cast),
  and `else`. Conditions are checked top to bottom; first match wins.

## Exhaustiveness over sealed types & enums

The big payoff: `when` over a `sealed` type or `enum` needs **no `else`** when all
cases are covered, and adding a case becomes a **compile error** at every `when`
until handled (see `data-and-modeling.md`):

```kotlin
fun area(shape: Shape): Double = when (shape) {
    is Shape.Circle    -> Math.PI * shape.radius * shape.radius   // smart cast to Circle
    is Shape.Rectangle -> shape.width * shape.height
}   // exhaustive: no else, and a new Shape subtype won't compile until added here
```

For an `enum`:

```kotlin
val degrees = when (direction) {
    Direction.NORTH -> 0
    Direction.EAST  -> 90
    Direction.SOUTH -> 180
    Direction.WEST  -> 270
}
```

**Avoid an `else` branch on a sealed/enum `when`** — it silences the exhaustiveness
check that protects you when the type grows. Use `else` only for genuinely open
subjects (ints, strings).

## Guard conditions (Kotlin 2.1+)

A subject `when` branch can carry an extra boolean condition with `if`, so you can
combine a pattern with a test without nesting:

```kotlin
when (response) {
    is Response.Error if response.code >= 500 -> retry()
    is Response.Error -> showError(response.message)
    is Response.Ok    -> render(response.body)
}
```

(Before 2.1, fall back to a subjectless `when` with explicit conditions.)

## `if` and `try` as expressions

```kotlin
val max = if (a > b) a else b          // if returns a value (no ternary needed)

val n = try {
    input.toInt()
} catch (e: NumberFormatException) {
    0                                   // try returns a value
}
```

Because `if`/`when`/`try` are expressions, you assign or return them directly
instead of mutating a `var` across branches — favor that. (There's no `?:`
ternary because `if` already is one.)

## Ranges and loops

```kotlin
for (i in 1..10) { }          // inclusive
for (i in 0 until n) { }       // exclusive upper (or 0..<n)
for (i in 10 downTo 1 step 2) { }
for ((index, value) in list.withIndex()) { }   // destructure
for ((key, value) in map) { }
```

But prefer collection operations (`map`/`filter`/`forEach`) over manual loops when
producing or transforming data (see `collections-and-errors.md`); reach for a
`for` loop for side effects or when you need `break`/`continue`.

## Destructuring

```kotlin
val (name, age) = person            // data class componentN
val (key, value) = entry
list.map { (a, b) -> a + b }        // destructure in a lambda
```

## Anti-patterns

- Don't add `else` to a sealed/enum `when` just to compile — list the cases so
  additions force a decision.
- Don't write `if/else if` ladders that a subjectless `when` would express more
  clearly.
- Don't fill a `var` across `if`/`when` branches when the expression form returns
  the value directly.
