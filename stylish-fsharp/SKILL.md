---
name: stylish-fsharp
description: >-
  Write, refactor, or review idiomatic, elegant F#. Use this whenever you touch
  F# code (.fs, .fsi, .fsx, .dib files, dotnet/F# projects), design a domain
  model or types in F#, port code into F#, or the user asks for "functional",
  "idiomatic", "clean", or "elegant" F#. Reach for this even when the user only
  says "F#" without saying "idiomatic" — the default in F# should always be the
  stylish, functional-first form, not C#-transliterated-into-F#. Covers domain
  modeling with discriminated unions and records, immutable pipelines, pattern
  matching and active patterns, Option/Result and railway-oriented error
  handling, function composition, and the rare cases where objects, async, or
  performance tuning are warranted.
---

# Stylish F#

Write F# that a fluent F# reader would call elegant: expression-oriented,
immutable by default, with types that make illegal states unrepresentable and
data flowing through small composable functions. The distilled style of Kit
Eason's *Stylish F# 6*, part of the `idiomatic-code` family (shared cross-language
philosophy + Rosetta Stone). Two companion F# skills extend it: `functional-domain-modeling`
for designing whole domains, workflows, and application structure (type-driven
DDD), and `fsharp-vs-frontier` for how these idioms compare to Haskell, Erlang,
and the other frontier functional languages.

The goal is not "functional purity for its own sake." It is **clarity**: the
shortest code whose correctness is obvious. F# gives you sharp tools for that —
use them, and don't reach for C#-shaped mutable scaffolding out of habit.

## The creed (apply by default, everywhere)

1. **Expressions, not statements.** Everything returns a value — `if`, `match`,
   `try`, even loops produce `unit`. Bind results with `let`; avoid `mutable`
   accumulators and early `return`. If you wrote a `for` loop that fills a
   collection, a pipeline almost certainly says it better.
2. **Make illegal states unrepresentable.** Encode the rules in the *type* so
   bad data can't be constructed. A wrong program should fail to compile, not
   fail at runtime. Single-case DUs, required fields, and DU cases beat
   stringly-typed flags and "valid-only-if" comments.
3. **Total functions over partial ones.** A function should return something
   sensible for every input it accepts. Prefer `tryX` returning `Option`/`Result`
   over throwing; reserve exceptions for genuinely exceptional, boundary
   conditions.
4. **Immutability by default.** Reach for `let`, copy-and-update (`{ x with … }`),
   and persistent collections first. Introduce `mutable`/arrays only locally and
   only when measured performance demands it.
5. **Compose small functions.** Build behavior by piping data (`|>`) through and
   composing functions (`>>`). Name intermediate steps when it aids reading;
   stay point-free when it doesn't.
6. **Let types speak; annotate sparingly.** Inference is strong — add type
   annotations at public boundaries and where they document intent or guide
   inference, not on every `let`.
7. **Functional-first, not OO-by-reflex.** Modules of functions over records/DUs
   are the default unit of code. Classes, interfaces, and inheritance are tools
   for .NET interop and specific patterns — not the starting point.

## Quick reach-for guide

| You need to…                              | Reach for…                                                        |
|-------------------------------------------|-------------------------------------------------------------------|
| Model "one of N shapes"                   | Discriminated union; match to consume                             |
| Model a bundle of named values            | Record (or anonymous record `{| … |}` for throwaway shapes)       |
| A primitive with rules (e.g. `Email`)     | Single-case DU with a `private` constructor + smart `create`      |
| "Maybe absent"                            | `Option<'T>` — never `null` in your own types                     |
| "Succeeds or fails with a reason"         | `Result<'T,'TError>` + a domain error DU; compose with railway    |
| Transform/filter/aggregate a collection   | `Seq`/`List`/`Array` functions in a `|>` pipeline, never a loop   |
| Decompose/branch on data                  | `match` + active patterns                                         |
| Build behavior from parts                 | Partial application + composition (`>>`)                          |
| Talk to .NET / need identity or disposal  | Classes, interfaces, object expressions, `use` (see reference)    |

## Reference files — read on demand

Keep this file in head; open a reference when the task lands in its area.

- **`references/domain-modeling.md`** — DUs, records, anonymous records,
  single-case DUs with validation and hidden constructors, units of measure,
  "make illegal states unrepresentable", pairing a module with its type.
  *Read when designing or refactoring types.*
- **`references/flow-and-collections.md`** — replacing loops/mutation with
  pipelines, the `map`/`filter`/`choose`/`fold`/`scan`/`partition`/`groupBy`
  toolbox, `tryX`→`Option`, recursion and tail calls, `seq` generators, and
  choosing `seq` vs `list` vs `array`. *Read for any data-processing logic.*
- **`references/pattern-matching.md`** — `match`, `when` guards, exhaustiveness,
  decomposing tuples/records/DUs/lists, and active patterns (single, multi,
  partial `|_|`, parameterized, `&`). F#'s sharpest tool. *Read for branching.*
- **`references/errors-and-effects.md`** — `Option` vs `Result`, railway-oriented
  programming (`bind`/`map`/`mapError`), error DUs, exceptions at boundaries,
  and computation expressions for `option`/`result`/`async`/`task`.
  *Read for validation, error handling, or effectful pipelines.*
- **`references/functions.md`** — partial application, currying vs tupling,
  composition, point-free/eta reduction (and when to stop), closures, `inline`,
  custom operators, and writing your own computation expressions.
  *Read when shaping functions or APIs.*
- **`references/objects-async-perf.md`** — when (and how) to use classes,
  interfaces, object expressions, equality/comparison, `IDisposable`/`use`;
  `async`/`task` and parallelism; `MailboxProcessor` actors; and performance
  (collection choice, structs, `inline`, allocations). *Read for interop,
  concurrency, or measured hot paths.*

## Layout & naming (cross-cutting)

- Indent with **4 spaces**; F# is whitespace-significant — never tabs.
- `camelCase` for values/functions/parameters; `PascalCase` for types, DU cases,
  modules, members. Acronyms read as words (`HtmlParser`, not `HTMLParser`).
- Pipe chains read top-to-bottom: put each `|>` on its own line.
- Open a function with the data, end with the result; keep the "happy path"
  flat and push edge cases into the type system, not nested `if`s.
- Prefer F# 6 indexing `arr[i]` over the legacy `arr.[i]` when targeting ≥ 6.0.

## A taste

```fsharp
// Illegal states unrepresentable + total parsing + railway composition.
type Customer = { Name : string; Email : Email }   // Email is a validated single-case DU

let private parseRow (line : string) : Result<Customer, string> =
    match line.Split('\t') with
    | [| name; email |] ->
        email
        |> Email.tryCreate                          // string -> Result<Email,string>
        |> Result.map (fun e -> { Name = name; Email = e })
    | cols ->
        Error $"expected 2 columns, got {cols.Length}"

let loadCustomers (lines : string seq) =
    lines
    |> Seq.map parseRow
    |> Seq.toList                                    // List<Result<Customer,string>>
```

No nulls, no exceptions for control flow, no mutation, every case handled, and
the shape of the data is the documentation. That is the target for all F# here.
