---
name: idiomatic-code
description: >-
  The shared house style for writing idiomatic, type-driven, frontier-competitive
  code — and the router to the per-language skills. Use this whenever you write,
  refactor, or review code in F#, C#, TypeScript, JavaScript, Python, Rust, Swift,
  Kotlin, or PowerShell; when deciding how to model data/state/errors; when porting code
  between these languages; or when the user asks about clean/idiomatic design
  across languages. It states the cross-language philosophy once
  (illegal-states-unrepresentable, no-null, immutability, match-don't-cast,
  composition-over-inheritance, errors-as-values) and points to the right
  language skill for the concrete idioms. Reach for it as the umbrella; reach for
  the language skill it names for the specifics.
---

# Idiomatic code — the house style

One philosophy, nine languages. These skills all push in the same direction:
**make the compiler (or the structure) carry correctness, and make the elegant
solution the practical one.** This meta-skill states that shared philosophy once,
and routes you to the language skill that turns it into concrete syntax.

Whatever language you're in, apply the creed below by default — then open the
language skill for how that language spells it.

## The creed (apply in every language)

1. **Make illegal states unrepresentable.** Model data so bad combinations can't
   be constructed: *sum types* for "one of N" (a value is exactly one variant),
   *product types* for "all of N", and *constrained primitives* (newtypes) for
   "a string with rules". A wrong program should fail to compile, not at runtime.
2. **No null; absence and failure are values.** Use an *optional* type for "maybe
   absent" and a *result*/typed error for "succeeded or failed with a reason".
   Reserve exceptions for genuine bugs and boundary I/O — convert them to values
   at the edge. Never reach into an optional with a force-unwrap as a habit.
3. **Immutability by default.** Bind once; produce a *new* value instead of
   mutating. Reach for mutation only locally, deliberately, and ideally
   unobservable from outside. The immutability that matters is at the API surface.
4. **Match, don't cast.** Branch and decompose with *exhaustive* pattern matching,
   not type tests, downcasts, or `if`/`else` ladders. Let the compiler prove every
   case is handled, so adding a variant lights up every site that must change.
5. **Composition over inheritance.** Share behavior with interfaces / traits /
   protocols + small functions; avoid deep class hierarchies. Reach for a class
   (or inheritance) only for identity, framework contracts, or interop — never as
   the default unit of code.
6. **Pipelines over loops.** Transform collections with `map`/`filter`/`fold`-style
   operations, kept pure, instead of index loops with mutable accumulators.
7. **Functions are values.** Pass behavior as a function; build features from small
   composable functions rather than god-objects or utility classes.
8. **Expressions over statements.** Let `if`/`match`/`switch`/`try` *return* values;
   assign or return the result instead of mutating a variable across branches.
9. **Structured concurrency.** Async work is owned by a scope that bounds its
   lifetime; propagate cancellation and errors. No leaked tasks, no floating
   promises, no global scopes.
10. **Let the toolchain enforce it.** Turn on the strict compiler settings, run the
    linter and formatter, and check it in CI — so the idioms are enforced, not
    just intended.
11. **Parse, don't validate.** Validate at the system boundaries and immediately
    parse the input into a constrained type (e.g., a newtype, union, or parsed record).
    Avoid passing raw strings or integers deeper into the application if they have rules attached.
12. **Functional core, imperative shell.** Keep your business logic pure, immutable, and side-effect free.
    Push mutation, database calls, I/O, and framework-mandated OOP boilerplate to the outermost edges of the system.
    Be willing to drop functional purity at these boundaries to speak the language of the framework (e.g., ORMs, UI frameworks) rather than building massive adapter layers.
13. **Pragmatism in hot paths.** Immutability is the default for safety, but if a high-frequency hot path is trashing the garbage collector with allocations, local mutation is perfectly acceptable. Just ensure the mutation does not escape the boundary of the function.
14. **Aggregate errors for users, fail fast for systems.** Use standard Results/Optionals to short-circuit system failures immediately. However, when validating user input with multiple independent fields, aggregate the errors into a list so the user receives all feedback at once.

The through-line: **the elegant solution is also the most correct and the most
practical.** Types are the cheapest documentation; matching is the cheapest proof;
immutability is the cheapest concurrency safety.

## Route to the language skill

Apply the creed; open the matching skill for the concrete idioms.

| Language    | Files                          | Skill(s) to use                                                                 |
|-------------|--------------------------------|---------------------------------------------------------------------------------|
| **F#**      | `.fs` `.fsi` `.fsx` `.dib`     | `stylish-fsharp` (write/refactor); `functional-domain-modeling` (architecture/DDD); `fsharp-vs-frontier` (compare/port from Haskell/Rust/etc.) |
| **C#**      | `.cs`                          | `functional-csharp`                                                              |
| **TypeScript** | `.ts` `.tsx` `.mts`         | `idiomatic-typescript`                                                           |
| **JavaScript** | `.js` `.mjs` `.cjs`         | `idiomatic-javascript` (prefer TS if a build step exists)                        |
| **Python**  | `.py` `.pyi` notebooks         | `idiomatic-python`                                                               |
| **Rust**    | `.rs`                          | `idiomatic-rust`                                                                 |
| **Swift**   | `.swift`                       | `idiomatic-swift`                                                                |
| **Kotlin**  | `.kt` `.kts`                   | `idiomatic-kotlin`                                                               |
| **PowerShell** | `.ps1` `.psm1` `.psd1`      | `idiomatic-powershell`                                                           |

Each language skill leads with a **reflex → idiomatic antidote table** (the bad
habit to unlearn → the idiomatic move) and bundles reference files for deeper
topics. Use this meta-skill for the *why* and the cross-language view; use the
language skill for the *how*.

## How the languages relate

- **The type-driven core — F#, C#, TypeScript, Rust, Swift, Kotlin** — all share
  the same spine: algebraic data types + exhaustive matching + optional/result +
  immutability + composition. Code translates between them almost
  mechanically (see `references/concept-map.md`). F# and Rust are the most
  uncompromising; Swift and Kotlin add value-orientation and protocol/extension
  composition; TypeScript brings it to the web; C# is catching up (records,
  patterns, unions on the way).
- **JavaScript & Python** are the **gradually-typed** members — the same
  philosophy you *opt into*. JS: `// @ts-check` + JSDoc + runtime validation
  (graduate to TypeScript when a build step is justified). Python: type hints +
  `pyright`/`mypy --strict`, with union-of-dataclasses + `match` + `assert_never`
  reaching the ADT/exhaustiveness core. Both: the checker isn't on by default —
  turn it on, or the safety isn't there.
- **PowerShell** is the outlier: an automation/shell language built on an *object
  pipeline*. It shares immutability, pipelines, structured output, and
  fail-loudly errors — but not the ADT/type-driven core. Apply the parts that fit.

## References

- **`references/concept-map.md`** — the cross-language **Rosetta Stone**: for each
  core concept (sum type, optional, result, immutability, matching, composition,
  pipeline, concurrency, newtype), the idiomatic construct in every language.
  *Read when porting between languages or picking the construct for a concept.*
- **`references/review-checklist.md`** — a language-agnostic idiom **review
  checklist**: the smells to flag and the idiomatic fix, derived from the creed.
  *Read when reviewing code in any of these languages.*
