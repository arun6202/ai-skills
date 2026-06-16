---
name: idiomatic-kotlin
description: >-
  Write, refactor, or review idiomatic Kotlin (.kt, .kts; JVM, Android, KMP,
  Gradle) — even a quick "write this in Kotlin". Steers toward modern,
  expression-oriented Kotlin: data classes and `val` over Java-style mutable
  POJOs, sealed classes/interfaces + exhaustive `when` over inheritance and type
  tags, null safety (`?.`/`?:`/smart casts) over `!!` and manual null checks,
  extension and top-level functions over utility classes, functional collection
  operations over loops, and structured-concurrency coroutines over callbacks.
  Reach for it when modeling data/state, handling nullability or errors, choosing
  data class vs class, replacing inheritance, or writing coroutines/Flow. Targets
  Kotlin 2.x (K2 compiler). Counters Java-in-Kotlin muscle memory.
---

# Idiomatic Kotlin

Kotlin is a pragmatic, expression-oriented, null-safe language with first-class
algebraic data types (sealed classes/interfaces), value-oriented data classes,
and powerful functional and concurrency features. Most "bad Kotlin" is **Java
written with Kotlin syntax**: mutable POJOs with getters/setters, `null` + `!!`,
inheritance hierarchies, and index loops.

The prime directive: **write Kotlin, not Java-in-Kotlin.** Default to `val` and
data classes, model variants with sealed types + exhaustive `when`, let the type
system track nullability, reach for extension and top-level functions instead of
utility classes, and use coroutines with structured concurrency. Reach for a
mutable, inheritance-heavy, or `!!`-laden approach only with a reason.

> **Part of the `idiomatic-code` family** — the shared cross-language philosophy and the Rosetta Stone (porting + review) live there.
>
> Stack family: Kotlin sits beside F#, Rust, Swift, and TypeScript — sealed
> classes are discriminated unions, `when` is exhaustive matching, `T?` is
> not-null-by-default, data classes are value-ish products, and it's
> expression-oriented and immutable-leaning. Java interop is the main muscle-
> memory source. Distinctive: extension functions, scope functions, and
> coroutines/Flow.

## Break the muscle memory (reflex → idiomatic)

When your instinct fires the left column, write the right column instead.

| Reflex (Java / OOP habit)                           | Idiomatic Kotlin                                                     |
|-----------------------------------------------------|---------------------------------------------------------------------|
| Class with fields + getters/setters                 | `data class` with `val` properties                                  |
| `value!!` not-null assertion                        | `?.` / `?:` (Elvis) / `requireNotNull` / smart cast                 |
| `null` + manual null checks                         | `T?` + safe calls, smart casts, `?.let { }`                        |
| Class inheritance hierarchy for variants            | `sealed class`/`interface` + exhaustive `when`                      |
| `var` everywhere                                    | `val` by default                                                    |
| `for (i in 0 until list.size)` index loop           | `map`/`filter`/`fold`/`forEach`                                     |
| `static` utility class `Utils.foo(x)`               | extension function `x.foo()` or top-level function                 |
| Builder pattern / telescoping constructors          | named + default arguments                                          |
| Exceptions for control flow                         | `Result`/`runCatching` or a sealed error type                      |
| `if (x != null) x else default`                     | `x ?: default` (Elvis)                                              |
| Anonymous inner class / SAM                         | lambda / trailing lambda                                           |
| `Thread` / callback chains                          | coroutines + structured concurrency                                |
| `ArrayList<>()` everywhere                          | `listOf(...)` (read-only) by default; `mutableListOf` only if needed |
| `lateinit` to dodge nullability                     | constructor injection / proper initialization                      |
| `companion object` as a dumping ground              | top-level / extension functions                                    |

If you genuinely need an open class hierarchy (a framework base type), mutable
state, or Java interop, those tools exist. Make it a decision, not a default.

## The creed

1. **`val` and immutability by default.** Data classes with `copy`; `var` only
   when it truly changes.
2. **No null.** `T?` + safe calls (`?.`), Elvis (`?:`), smart casts. `!!` is a
   smell outside provable invariants/tests.
3. **Make illegal states unrepresentable.** `sealed class`/`interface` for
   "one of", data classes for "all of", then `when` exhaustively.
4. **Expression-oriented.** `when`, `if`, and `try` return values — assign and
   return them instead of mutating a `var`.
5. **Functions over utility classes.** Extension and top-level functions;
   composition over inheritance.
6. **Functional collections.** `map`/`filter`/`fold`; `asSequence()` for
   large/lazy pipelines.
7. **Structured concurrency.** Coroutines in a scope; never `GlobalScope`.
8. **Scope functions with intent.** `let`/`run`/`with`/`apply`/`also` for their
   specific purpose — not as decoration.

## Quick reach-for guide

| You need to…                              | Reach for…                                                       |
|-------------------------------------------|------------------------------------------------------------------|
| A data bundle                             | `data class` with `val`s                                          |
| "One of N shapes" / a state              | `sealed interface`/`class` + exhaustive `when`                   |
| Constrain a primitive (UserId, Email)     | `@JvmInline value class` (+ validating factory)                 |
| "Maybe absent"                            | `T?` + `?.`/`?:`/`?.let`                                         |
| "Succeeds or fails"                       | `Result`/`runCatching`, or a sealed error type                  |
| Add behavior to a type you don't own      | extension function                                              |
| Configure an object                       | `apply { }`; transform with `let`/`run`                         |
| Transform a collection                    | `map`/`filter`/`fold`/`groupBy`/`mapNotNull`                    |
| Concurrent work                           | `coroutineScope { async { } }`; `Flow` for streams             |

## Reference files — read on demand

- **`references/data-and-modeling.md`** — data classes, `value class`, enums,
  **sealed classes/interfaces**, illegal-states-unrepresentable, `val`/`var`,
  `copy`, destructuring. *Read when modeling data.*
- **`references/null-safety.md`** — `T?` vs `T`, `?.`, `?:`, `!!` (avoid), smart
  casts, `?.let`, `lateinit`, Java platform types. *Read for any nullable value.*
- **`references/when-and-control-flow.md`** — `when` (expression + exhaustive over
  sealed/enum), guard conditions (2.1), smart casts, `if`/`when`/`try` as
  expressions, ranges. *Read for branching.*
- **`references/functions-and-extensions.md`** — extension functions, higher-order
  functions, lambdas + trailing lambda, named/default args, the five scope
  functions, `inline`, `infix`. *Read for API design and Kotlin idioms.*
- **`references/collections-and-errors.md`** — collection operations, sequences
  (lazy), read-only vs mutable collections, error handling (`Result`,
  `runCatching`, sealed errors, no checked exceptions). *Read for data processing
  or errors.*
- **`references/coroutines-and-tooling.md`** — coroutines, `suspend`, structured
  concurrency, `Flow`/`StateFlow`, dispatchers; KMP, Gradle, ktlint/detekt, the
  K2 compiler. *Read for concurrency or project setup.*

## A taste

```kotlin
sealed interface Shape {
    data class Circle(val radius: Double) : Shape
    data class Rectangle(val width: Double, val height: Double) : Shape
}

fun area(shape: Shape): Double = when (shape) {        // exhaustive over a sealed type
    is Shape.Circle    -> Math.PI * shape.radius * shape.radius   // smart cast
    is Shape.Rectangle -> shape.width * shape.height
}                                                       // no `else` needed; a new case won't compile until handled

fun totalArea(shapes: List<Shape>): Double =
    shapes.sumOf(::area)                                // functional, expression-bodied
```

No `!!`, no `var`, no inheritance, no getters/setters, exhaustive matching, value
data — and the sealed hierarchy *is* the documentation. That is the target for all
Kotlin here.
