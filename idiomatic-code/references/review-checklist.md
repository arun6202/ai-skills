# Idiom review checklist

A language-agnostic checklist for reviewing code in any of these languages. Each
item is a **smell to flag** → the **idiomatic fix**, grouped by the creed. Scan
for these; for the exact construct in the target language, see `concept-map.md`
and the language skill.

## 1. Illegal states unrepresentable

- [ ] **Boolean flags / optional fields with illegal combinations**
  (`isLoading` + `data?` + `error?`) → a **sum type** whose cases are the legal
  states.
- [ ] **Stringly-typed states** (`status: string`, magic strings) → an enum / union
  of literals.
- [ ] **Primitives with rules passed raw** (a bare `string` email, `int` age) →
  a **newtype** validated at construction ("parse, don't validate").
- [ ] **Validation repeated at every use** → validate once at the boundary, then
  carry a type that can't be invalid.

## 2. No null; errors as values

- [ ] **Force-unwrap / not-null assertion** (`!!`, `!`, `.unwrap()`, `x!`, `.Value`)
  used as a habit → safe unwrap (`if let`/`guard`/`?.`/`??`/`match`) or restructure
  to a non-optional type.
- [ ] **Sentinels** (`-1`, `""`, `null`, `Guid.Empty`) standing in for "absent" →
  an **optional** type.
- [ ] **Exceptions for expected outcomes** (not-found, validation failed, parse
  error) → a **result**/optional return.
- [ ] **Swallowed errors** (empty `catch {}`, blanket `SilentlyContinue`, `try?`
  then ignore) → handle, wrap-and-rethrow with cause, or propagate.
- [ ] **Error as a bare string** → a typed error (enum/union); domain vs infra
  errors kept distinct.
- [ ] **Thrown non-error** (`throw "msg"`) → throw a real error/exception type.
- [ ] **Short-circuiting on multiple independent validation errors** (e.g., user forms) → aggregate the errors into a list so the user gets all feedback at once.

## 3. Immutability

- [ ] **`var`/`let mut`/mutable field as the default** → immutable binding
  (`val`/`let`/`const`/`readonly`); reassign only when it truly changes.
- [ ] **In-place mutation of shared data** (`push`, set a field, mutate an argument)
  → produce a **new value** (copy-and-update / spread / `with`/`copy`).
- [ ] **Mutable collection exposed in a public type** → a read-only / immutable
  collection type.
- [ ] **Deep-clone hack** (`JSON.parse(JSON.stringify(x))`) → the real deep-copy
  (`structuredClone`, value semantics).
- [ ] **Dogmatic immutability in a hot loop** (trashing the garbage collector) → use local, unobservable mutation for performance.

## 4. Match, don't cast

- [ ] **`if`/`else if` ladder returning a value** → an exhaustive
  `match`/`switch`/`when` expression.
- [ ] **Type test + downcast** (`is X` then cast, `as!`, `as X`) → pattern match
  that binds, or model the variants as a sum type.
- [ ] **`default`/`else`/`_` arm on a sum type you own** → list the cases so adding
  one is a compile error (keep the exhaustiveness check).
- [ ] **Missing exhaustiveness guard** where the language doesn't enforce it (C#
  `_ => throw Unreachable`, TS/JS `never`) → add it.

## 5. Composition over inheritance

- [ ] **Class inheritance for data/variants** → a sum type + functions, or
  interface/trait/protocol composition.
- [ ] **Deep inheritance chain / god base class** → small composable pieces;
  delegation.
- [ ] **One-method interface injected only to mock** → pass a function.
- [ ] **Utility class of statics** (`StringUtils.foo(x)`) → top-level / extension
  functions.
- [ ] **Class used as a plain data bag** (getters/setters, no behavior) → a
  record / data class / struct.

## 6. Pipelines & expressions

- [ ] **Index loop building a collection** (`for i in 0..n { out.push(...) }`) →
  `map`/`filter`/`fold`-style pipeline.
- [ ] **`map` + `filter` + unwrap** where one pass would do → `choose`/`compactMap`/
  `mapNotNull`/`filterMap`.
- [ ] **Accumulating with `+=` into an array in a loop** → emit-and-collect or a
  fold (and in JS/PS, avoid the O(n²) re-allocation).
- [ ] **Mutable var filled across `if`/`switch` branches** → assign the
  expression's result directly.
- [ ] **Long/nested lambda** → a named function referenced point-free.

## 7. Concurrency

- [ ] **Unscoped/leaked async work** (`GlobalScope`, detached task, fire-and-forget)
  → structured concurrency in an owned scope.
- [ ] **Floating promise / un-awaited future** → `await` it, return it, or handle
  rejection.
- [ ] **`await` inside `forEach` / sequential awaits for independent work** →
  parallelize (`Promise.all`/`Task.WhenAll`/`async let`/`async {}`).
- [ ] **Blocking call inside async** (`Thread.sleep`, sync I/O) → the async
  equivalent / offload.
- [ ] **Shared mutable state across tasks without protection** → an actor / message
  passing / `Sendable`-safe value / lock.

## 8. Toolchain & hygiene

- [ ] **Strict mode off** (no `strict`/`#nullable enable`/`Set-StrictMode`/strict
  tsconfig, missing `noUncheckedIndexedAccess`) → turn it on.
- [ ] **`any` / untyped escape** (`any`, `dynamic`, platform-type NPE risk) →
  `unknown` + narrowing, a real type, or boundary validation.
- [ ] **Aliases / abbreviations in committed code** (PowerShell `?`/`%`/`gci`) →
  full names.
- [ ] **No linter/formatter in CI** (clippy, ESLint, ktlint/detekt, SwiftLint,
  PSScriptAnalyzer, Fantomas/rustfmt) → add it, warnings-as-errors.
- [ ] **`unsafe`/`@unchecked`/`as unknown as` without justification** → remove, or
  document the invariant.

## 9. Architecture & Boundaries

- [ ] **Business logic mixed with I/O or mutation** → separate into a pure function (Functional core) and a coordinating side-effect (Imperative shell).
- [ ] **Validating the same data deeply in the system** → validate once at the system boundary and immediately convert to a constrained type ("Parse, don't validate").
- [ ] **Forcing functional purity onto an OOP framework** (e.g., massive adapter layers for ORMs) → drop purity at the boundary and speak the framework's native language.

## Fast-path review

If you only have a minute, scan for these five highest-signal smells:

1. **Force-unwrap** (`!!`/`!`/`.unwrap()`/`x!`) used routinely.
2. **A class hierarchy** where a **sum type + match** belongs.
3. **Mutation** where a new value would do.
4. **`any`/cast/`default`-arm** defeating the type checker.
5. **A leaked or floating** async task.

Each maps to a creed item; the fix is in the language skill named by
`idiomatic-code`.
