---
name: fsharp-vs-frontier
description: >-
  Position and translate F# against the frontier functional languages — Haskell,
  Erlang/Elixir, OCaml, Scala, Clojure, and Rust. Use this whenever the user
  compares F# to one of those ("is F# as good as Haskell for X", "F# vs Scala"),
  asks how to express a concept from them in F# ("how do I do type classes /
  actors / do-notation / the borrow checker in F#"), ports or rewrites code from
  one of those languages into F#, weighs whether F# can match a specific
  functional feature, or wants an honest take on F#'s strengths and gaps versus
  them. Part of the `idiomatic-code` family; pair with `stylish-fsharp` for the actual idiomatic F# you should emit.
  Reach for this even on a bare "translate this Haskell/Elixir/Rust snippet to
  F#" — the right answer is idiomatic F#, not a literal transliteration.
---

# F# vs the frontier

F#'s pitch among functional languages: a lean, **functional-first** ML on .NET
that buys most of the elegance of the frontier languages while staying
pragmatic, fast to write, and plugged into a vast ecosystem with first-class
tooling. It is not the most type-theoretically powerful (no higher-kinded types),
nor the most concurrent (not the BEAM), nor the fastest (it's GC'd) — but it sits
at a sweet spot where **the elegant solution is also the practical one.**

When asked to compare or translate: give the **idiomatic F# equivalent**, not a
transliteration, and be **honest** about where the other language genuinely wins.
Emit real F# using `stylish-fsharp` idioms — and `functional-domain-modeling` for
domain-, workflow-, or architecture-level questions.

## Concept-translation matrix

| Frontier concept                     | Idiomatic F# equivalent                                                  | Parity        |
|--------------------------------------|--------------------------------------------------------------------------|---------------|
| Algebraic data types (sum types)     | Discriminated unions                                                      | ✅ equal       |
| Product types / records              | Records, anonymous records, tuples                                       | ✅ equal       |
| `Maybe` / `Option`                   | `Option<'T>` (`Some`/`None`)                                              | ✅ equal       |
| `Either` / error values              | `Result<'T,'TError>` (`Ok`/`Error`) + railway-oriented programming        | ✅ equal       |
| Exhaustive pattern matching          | `match` + **active patterns** (extensible matching)                       | 🟢 F# ahead    |
| Currying / partial application       | Native; design "config first, data last"                                 | ✅ equal       |
| Function composition / point-free    | `>>`, `<<`, `|>`                                                          | ✅ equal       |
| `do`-notation / for-comprehensions   | **Computation expressions** (`seq`/`async`/`task`/`result`/custom)        | 🟡 per-type    |
| Type classes / traits / given        | Interfaces; `inline` + SRTP member constraints for numeric/generic code   | 🟠 F# weaker   |
| Higher-kinded types (Functor/Monad)  | *Not supported* — no generic `Monad`; CEs cover the common cases          | 🔴 gap         |
| Laziness / infinite structures       | `seq { }` (lazy), `lazy`/`Lazy<'T>`; strict by default                    | 🟢 F# clearer  |
| Enforced purity                      | Pure by convention, not by the compiler                                   | 🟠 F# weaker   |
| Actors / processes / message passing | `MailboxProcessor` (Agent); Akka.NET / Orleans / Proto.Actor for scale    | 🟡 see below   |
| Supervision / "let it crash" / OTP   | Not built-in; .NET hosting + actor libs (no BEAM hot-reload/distribution) | 🔴 BEAM ahead  |
| Macros / metaprogramming             | Quotations, **type providers**, CEs — no general macros                   | 🟠 F# narrower |
| Ownership / borrow checker / no-GC   | Not applicable — F# is garbage-collected                                  | 🔴 Rust ahead  |
| Dimensional safety                   | **Units of measure** (compile-time, zero-cost)                            | 🟢 F# ahead    |
| External schema → types              | **Type providers** (SQL/JSON/CSV/OData generated at compile time)         | 🟢 F# rare     |
| REPL-driven development              | F# Interactive (`dotnet fsi`), `.fsx` scripts, .NET notebooks            | ✅ equal       |

Legend: ✅ on par · 🟢 F# advantage · 🟡 partial/qualified · 🟠 F# weaker · 🔴 real gap.

## F#'s distinctive wins (lead with these)

- **Active patterns** — pattern matching you can *extend* with your own
  domain-named matchers; cleaner than Haskell view patterns / Scala extractors.
- **Computation expressions** — one syntax (`let!`/`do!`/`return!`) that powers
  async, sequences, queries, error pipelines, and any custom "wrap-and-chain"
  type you define. The ergonomic answer to monadic `do`-notation.
- **Units of measure** — compile-time dimensional analysis with no runtime cost.
  Most frontier languages need a library and runtime wrappers.
- **Type providers** — types materialized at compile time from live external
  schemas (databases, JSON/CSV, web services). Almost unique to F#.
- **Pragmatism** — type-safe `printf`, trivial .NET interop, a controlled
  `mutable`/array escape hatch, gentle learning curve, and best-in-class IDE
  tooling (Rider, Visual Studio, Ionide).

## Honest gaps (don't oversell)

- **No higher-kinded types**: you cannot write code generic over "any monad/
  functor". Computation expressions give per-type ergonomics instead; `FSharpPlus`
  emulates more but fights the language. If a problem demands HKT abstraction,
  Haskell/Scala fit better.
- **No real type classes**: SRTP + `inline` covers generic numerics but is more
  awkward than Haskell classes or Scala givens, and doesn't scale to large
  hierarchies.
- **Purity is a discipline**, not a guarantee — no `IO` type fences off effects.
- **Concurrency isn't the BEAM**: `MailboxProcessor` matches the actor *model*,
  but Erlang/Elixir win decisively on massive lightweight concurrency, built-in
  supervision, distribution, and hot code reload.
- **GC'd**: for no-GC / manual-memory / borrow-checked domains, Rust is the tool.

## Deeper, per-language guidance

Read **`references/translation-guide.md`** for side-by-side idiom translations and
a "where each wins" verdict per language: Haskell, Erlang/Elixir, OCaml, Scala,
Clojure, Rust. Open it when porting code or making a detailed comparison; the
matrix above is enough for a quick answer.

## How to answer comparison/translation requests

1. **Translate to idiomatic F#**, not a transliteration — reach for DUs, `match`/
   active patterns, `Option`/`Result`, pipelines, CEs (use `stylish-fsharp`).
2. **Name the parity** from the matrix so the user knows if it's a clean win, a
   workaround, or a genuine gap.
3. **Be honest about the gap** when there is one, and say what the other language
   would do better — credibility matters more than boosterism.
4. **Show the F#-native angle** when relevant (active patterns, CEs, units of
   measure, type providers) — that's where F# turns a tie into a lead.
