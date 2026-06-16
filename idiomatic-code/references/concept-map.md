# Cross-language Rosetta Stone

For each core concept of the shared house style, the idiomatic construct in every
language. Use it to port code between these languages (the mapping is nearly
mechanical for the type-driven six) or to pick the right construct for a concept.

PowerShell is included where it fits and marked **(N/A — different paradigm)** for
the type-driven concepts it doesn't share.

## Contents

- [Sum type — "one of N"](#sum-type--one-of-n)
- [Product type — "all of N"](#product-type--all-of-n)
- [Optional — "maybe absent"](#optional--maybe-absent)
- [Result — "succeeds or fails"](#result--succeeds-or-fails)
- [Exhaustive matching](#exhaustive-matching)
- [Immutability & update](#immutability--update)
- [Constrained primitive (newtype)](#constrained-primitive-newtype)
- [Composition over inheritance](#composition-over-inheritance)
- [Data pipeline](#data-pipeline)
- [Concurrency / async](#concurrency--async)
- [Exhaustiveness enforced by the compiler?](#exhaustiveness-enforced-by-the-compiler)

---

## Sum type — "one of N"

A value that is exactly one of a fixed set of shapes, each carrying its own data.

| Language    | Idiomatic construct                                                        |
|-------------|---------------------------------------------------------------------------|
| F#          | discriminated union — `type Shape = Circle of float \| Rect of float*float` |
| Rust        | `enum Shape { Circle(f64), Rect(f64, f64) }`                              |
| Swift       | `enum Shape { case circle(Double); case rect(Double, Double) }`           |
| Kotlin      | `sealed interface Shape { data class Circle(...) : Shape; ... }`           |
| TypeScript  | discriminated union — `{ kind: 'circle'; r: number } \| { kind: 'rect'; ... }` |
| C#          | `abstract record Shape;` + `sealed record Circle(double R): Shape;` (+ `switch`); native `union` keyword in preview |
| C++         | `std::variant<Circle, Rect>` + `std::visit`                               |
| JavaScript  | tagged objects `{ kind: 'circle', r }` + `switch` (+ JSDoc union)         |
| PowerShell  | (N/A — different paradigm; an `enum` for tagless cases)                    |

## Product type — "all of N"

A bundle of named values.

| Language    | Idiomatic construct                                               |
|-------------|------------------------------------------------------------------|
| F#          | record — `type P = { X: int; Y: int }`                          |
| Rust        | `struct P { x: i32, y: i32 }`                                    |
| Swift       | `struct P { let x: Int; let y: Int }`                            |
| Kotlin      | `data class P(val x: Int, val y: Int)`                          |
| TypeScript  | `type P = { readonly x: number; readonly y: number }`           |
| C#          | `record P(int X, int Y)`                                         |
| C++         | `struct P { int x; int y; };`                                    |
| JavaScript  | plain object `{ x, y }` (+ JSDoc `@typedef`)                    |
| PowerShell  | `[pscustomobject]@{ X = 1; Y = 2 }`                             |

## Optional — "maybe absent"

| Language    | Idiomatic construct                                               |
|-------------|------------------------------------------------------------------|
| F#          | `Option<'T>` (`Some` / `None`)                                   |
| Rust        | `Option<T>` (`Some` / `None`)                                    |
| Swift       | `Optional<T>` (`T?`); unwrap with `if let`/`guard let`/`??`      |
| Kotlin      | nullable type `T?`; `?.` / `?:` / smart casts                   |
| TypeScript  | `T \| undefined` under `strictNullChecks`; `?.` / `??`          |
| C#          | nullable reference types `T?` (NRT); `Option<T>` via a library   |
| C++         | `std::optional<T>`; test with `if (opt)` or `.has_value()`       |
| JavaScript  | `T \| undefined`; `?.` / `??` (+ `@ts-check`)                   |
| PowerShell  | `$null`; test `if ($null -eq $x)` (null on the left)            |

**Avoid everywhere:** the unchecked escape — `!!` (Kotlin), `!`/`as!` (Swift),
`x!`/`!` (TS), `.unwrap()` (Rust), `.Value` on a `None` (F#).

## Result — "succeeds or fails"

| Language    | Idiomatic construct                                                       |
|-------------|--------------------------------------------------------------------------|
| F#          | `Result<'T,'TError>` + railway (`bind`/`map`/`mapError`)                  |
| Rust        | `Result<T, E>` + `?`; `thiserror` (libs) / `anyhow` (apps)               |
| Swift       | `throws` (typed `throws(E)` in Swift 6) / `Result<Success, Failure>`      |
| Kotlin      | `Result<T>` / `runCatching` / a sealed error type                        |
| TypeScript  | `Result` discriminated union / `neverthrow`; exceptions at the edge       |
| C#          | `Result`/`ErrorOr`/`CSharpFunctionalExtensions`; exceptions at the edge   |
| C++         | `std::expected<T, E>` (C++23) / exceptions at the edge           |
| JavaScript  | `{ ok: true, value } \| { ok: false, error }`; `throw new Error(msg,{cause})` |
| PowerShell  | terminating errors + `try/catch` + `-ErrorAction Stop`                    |

**Shared rule:** model the error as a *type* (a DU/enum/union), not a bare string;
keep domain errors distinct from infrastructure errors.

## Exhaustive matching

| Language    | Idiomatic construct                                               |
|-------------|------------------------------------------------------------------|
| F#          | `match … with` + active patterns                                 |
| Rust        | `match` (compiler-exhaustive)                                    |
| Swift       | `switch` (compiler-exhaustive) + `if case`/`guard case`         |
| Kotlin      | `when` (exhaustive over sealed/enum) + guard conditions          |
| TypeScript  | `switch` on the discriminant + `never` exhaustiveness check      |
| C#          | `switch` expression + patterns (+ `_ => throw UnreachableException()`) |
| C++         | `std::visit` + overloaded lambda struct (compiler-exhaustive)    |
| JavaScript  | `switch` on the tag (+ `@ts-check` `never` for the check)         |
| PowerShell  | `switch` statement (value / `-Wildcard` / `-Regex`)             |

## Immutability & update

| Language    | Bind                  | "Change" (produce a new value)                     |
|-------------|-----------------------|----------------------------------------------------|
| F#          | `let` (immutable)     | copy-and-update — `{ rec with X = 1 }`            |
| Rust        | `let` (vs `let mut`)  | construct anew; ownership moves                     |
| Swift       | `let`                 | value semantics (structs copy); build a new value |
| Kotlin      | `val`                 | `data class` `copy(x = 1)`                          |
| TypeScript  | `const` + `readonly`  | spread — `{ ...obj, x: 1 }`; `as const`            |
| C#          | `readonly`/`init`     | `record` `with { X = 1 }`                          |
| C++         | `const auto`          | construct anew; copy/move semantics                 |
| JavaScript  | `const`               | spread — `{ ...obj, x: 1 }`; `structuredClone`     |
| PowerShell  | (immutable-leaning)   | emit new objects; avoid `$global:` mutation        |

## Constrained primitive (newtype)

"A string/number with rules" as its own type, validated at construction.

| Language    | Idiomatic construct                                                  |
|-------------|---------------------------------------------------------------------|
| F#          | single-case DU with a `private` ctor + smart `create` → `Result`    |
| Rust        | newtype tuple struct `struct Email(String)` + validating `parse`     |
| Swift       | `struct Email` with a failable/throwing `init?`                     |
| Kotlin      | `@JvmInline value class Email` + validating factory                 |
| TypeScript  | branded type `string & { readonly __brand: 'Email' }` + parser       |
| C#          | `readonly record struct Email` / value object + factory             |
| C++         | single-field `class` with private constructor + static `parse` factory  |
| JavaScript  | factory function + runtime validation (no static brand)             |
| PowerShell  | class with a validating constructor / `[ValidateScript()]`           |

## Composition over inheritance

| Language    | Share behavior with…                                              |
|-------------|------------------------------------------------------------------|
| F#          | modules of functions + interfaces; object expressions            |
| Rust        | **traits** + generics (no inheritance at all)                    |
| Swift       | **protocols + protocol extensions** (protocol-oriented programming)|
| Kotlin      | interfaces + delegation (`by`) + extension functions             |
| TypeScript  | interfaces/`type`s + structural typing; composition              |
| C#          | interfaces + composition; records (avoid deep inheritance)        |
| C++         | Concepts (C++20) + templates + composition (avoid deep virtual chains) |
| JavaScript  | composition + closures (avoid prototype-chain inheritance)        |
| PowerShell  | functions + modules                                              |

## Data pipeline

| Language    | Idiomatic construct                                               |
|-------------|------------------------------------------------------------------|
| F#          | `\|>` + `Seq/List/Array.map/filter/fold`                         |
| Rust        | iterators — `.iter().map().filter().collect()` (lazy, zero-cost) |
| Swift       | `map`/`filter`/`reduce`/`compactMap` (+ keypaths `\.name`)       |
| Kotlin      | collection ops; `asSequence()` for lazy                          |
| TypeScript  | array methods — `map`/`filter`/`reduce`/`flatMap`               |
| JavaScript  | array methods (+ a `pipe` helper for `\|>`-style)               |
| C#          | LINQ — `Select`/`Where`/`Aggregate`                             |
| C++         | `std::views::transform`/`filter` (C++20 ranges)                  |
| PowerShell  | the object pipeline — `… \| Where-Object \| ForEach-Object`      |

## Concurrency / async

| Language    | Idiomatic construct                                                       |
|-------------|--------------------------------------------------------------------------|
| F#          | `async`/`task` computation expressions; `MailboxProcessor` (actor)        |
| Rust        | `async`/`await` + tokio; threads; channels (`Send`/`Sync` enforced)       |
| Swift       | `async`/`await` + **structured concurrency** + `actor` + `Sendable`       |
| Kotlin      | **coroutines** + structured concurrency (`coroutineScope`) + `Flow`       |
| TypeScript  | `async`/`await` over Promises; `Promise.all`/`allSettled`                |
| JavaScript  | `async`/`await` over Promises; no floating promises                      |
| C#          | `async`/`await` Tasks; channels; `Task.WhenAll`                          |
| C++         | `std::async`, `std::future`, `co_await` (C++20 coroutines)       |
| PowerShell  | `ForEach-Object -Parallel` (PS7) + `-ThrottleLimit`; `Start-ThreadJob`    |

**Shared rule:** bound async work to a scope; don't leak tasks; parallelize
independent work, await dependent work.

## Exhaustiveness enforced by the compiler?

How much the compiler proves you handled every case of a sum type:

| Language    | Enforced?                                                          |
|-------------|-------------------------------------------------------------------|
| Rust        | ✅ error — `match` must cover all variants                         |
| Swift       | ✅ error — `switch` over an enum must be exhaustive               |
| Kotlin      | ✅ error — `when` over sealed/enum (used as an expression)        |
| F#          | ✅ warning — missing union cases warn (treat warnings as errors)  |
| TypeScript  | ✅ via `never` — assign the residual to `never` to force it       |
| C#          | 🟡 partial — no closed-hierarchy check today; `_ => throw`; native `union` (preview) adds it |
| C++         | ✅ error — missing case in `std::visit` fails to compile          |
| JavaScript  | ❌ runtime — use `@ts-check` + `never` to recover it              |
| PowerShell  | ❌ none                                                            |

---

## Porting tip

When moving code between the type-driven six, translate **concept by concept**:
a sum type becomes that language's sum type, an optional becomes its optional, a
`match`/`when`/`switch` stays an exhaustive match. The *shape* of idiomatic code
is the same; only the keywords change. The two places to watch: **null/optionality
spelling** (and the force-unwrap to avoid), and **exhaustiveness** (free in
Rust/Swift/Kotlin, a `never` trick in TS, a discard-throw in C#). For the concrete
idioms and the bad-habit antidotes, open the target language's skill.
