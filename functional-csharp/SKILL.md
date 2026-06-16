---
name: functional-csharp
description: >-
  Write modern, functional-leaning C# (C# 14 / .NET 10): records over mutable
  classes, pattern matching and switch expressions over if/else and visitor,
  immutability (init/required/readonly/with), LINQ pipelines over loops, nullable
  reference types and Result/Option over null and exceptions, and discriminated
  unions (today's stop-gaps plus the upcoming `union` keyword). Use this whenever
  you write, refactor, or review C# — even a plain "write this in C#" — to steer
  away from reflexive OOP boilerplate toward concise, expression-oriented code.
  Reach for it especially when modeling data/outcomes, choosing between a class
  and a record, replacing inheritance hierarchies or the visitor/strategy
  patterns, handling errors, or asking "how do I get F#-style unions / ROP /
  immutability in C#". Counters deeply ingrained OOP muscle memory.
---

# Functional C#

C# in .NET 10 is a genuinely capable functional-first language — records,
exhaustive pattern matching, immutability, expression bodies, LINQ, and nullable
reference types are all first-class. The obstacle isn't the language; it's
**muscle memory.** Decades of "everything is a class, mutate fields, loop, throw,
use inheritance" are baked into most C# instincts.

So the prime directive of this skill: **default to the functional form, and reach
for classic OOP only with a stated reason.** Write expressions, not statements;
immutable data, not mutable objects; total functions over patterns, not virtual
dispatch and null. The result is shorter, safer code that reads like F# wearing
C# syntax.

> **Part of the `idiomatic-code` family** — the shared cross-language philosophy and the Rosetta Stone (porting + review) live there.
>
> This is the C# member of a family. `stylish-fsharp` and
> `functional-domain-modeling` cover the same ideas in F#; the *concepts*
> (make illegal states unrepresentable, parse-don't-validate, railway-oriented
> errors, states-as-types) transfer directly — only the syntax changes.

## Break the muscle memory (reflex → reach-for)

When your instinct fires the left column, write the right column instead.

| OOP reflex (muscle memory)                          | Functional C# instead                                                    |
|-----------------------------------------------------|--------------------------------------------------------------------------|
| `class` with get/set properties                     | `record` with `init`/`required`; mutate via `with`                       |
| Mutating fields in place                            | Return a new value (`with`-expression / new record)                      |
| `null` + null checks everywhere                     | Nullable reference types (`#nullable enable`, `T?`) or `Option<T>`        |
| Throwing exceptions for expected failure            | `Result<T,E>` / `ErrorOr<T>` and railway composition                     |
| Inheritance hierarchy + virtual methods             | Closed DU (abstract record + sealed cases) + `switch` expression         |
| Visitor pattern                                     | `switch` expression over patterns                                        |
| Strategy / Command pattern (a class with one method)| A `Func<>`/`delegate` passed as a parameter                              |
| Builder pattern                                     | `record` + object initializer + `with`                                   |
| `for`/`foreach` accumulating into a list            | LINQ (`Select`/`Where`/`Aggregate`) → `ToList()`/collection expression   |
| `void` method that mutates state                    | Pure function returning the new state                                    |
| Interface with one method, injected for mocking     | Pass the function in; reserve interfaces for real polymorphism           |
| `if`/`else if` chains returning a value             | `switch` expression with patterns                                        |
| Sentinel values (`-1`, `""`, `Guid.Empty`)          | `Option<T>` / nullable / a DU case                                       |

If you genuinely need identity, mutable encapsulated state, framework base
classes, or runtime-extensible polymorphism — use a class. Just make it a
*decision*, not a default.

## The creed

1. **Expressions over statements.** Prefer `switch` expressions, expression-bodied
   members, ternaries, and LINQ to statement blocks that mutate locals.
2. **Immutable by default.** `record`, `init`, `required`, `readonly`,
   `with`-expressions, and immutable/`ToImmutable*` collections. New value, not
   mutation.
3. **Make illegal states unrepresentable.** Model data so bad combinations can't
   compile — DUs for "one of", records with `required` for "all of", validated
   wrapper types for constrained primitives.
4. **Total functions.** A `switch` should cover every case; return `Option`/
   `Result` instead of throwing or returning sentinels. Push exceptions to the
   boundary.
5. **Pattern matching is the control flow.** Decompose and branch with patterns,
   not type checks, casts, and `if`.
6. **Functions are values.** Pass `Func`/`Action`/delegates; a one-method
   interface is usually just a function.
7. **Pipelines over loops.** Transform data with LINQ method chains; keep
   intermediate steps immutable.

## Quick reach-for guide

| You need to…                              | Reach for…                                                       |
|-------------------------------------------|------------------------------------------------------------------|
| A data bundle ("all of")                  | `record` (positional) with `init`/`required`                     |
| "One of N shapes" / closed outcomes       | DU stop-gap: abstract record + sealed cases + `switch` (or OneOf)|
| "Maybe absent"                            | `T?` (nullable) for simple cases, else `Option<T>`               |
| "Succeeds or fails with a reason"         | `Result<T,E>` / `ErrorOr<T>` + `Map`/`Bind`/`Match`              |
| Branch/decompose a value                  | `switch` expression with type/property/list patterns            |
| Transform/filter/aggregate a collection   | LINQ pipeline → `ToList()`/`[..]`                               |
| Add behavior to a type you don't own      | C# 14 extension members (`extension` block)                      |
| Parameterize behavior                     | A `Func<>` parameter, not a strategy class                       |

## Reference files — read on demand

- **`references/records-and-immutability.md`** — record class/struct, positional
  records, `init`/`required`, `with`-expressions, value equality, `readonly`, and
  immutable collections. *Read when modeling data or choosing class vs record.*
- **`references/pattern-matching.md`** — `switch` expressions and every pattern
  (type, property, positional, relational, logical `and`/`or`/`not`, list, `var`),
  exhaustiveness, and replacing if-chains and the visitor pattern. *Read for any
  branching/decomposition.*
- **`references/discriminated-unions.md`** — the heart of this skill: today's
  DU **stop-gaps** (abstract record + sealed cases; OneOf; dunet) with the
  exhaustiveness caveat, plus the upcoming **`union` keyword** (C# 15/.NET 11
  preview). *Read when modeling closed sets of types/outcomes.*
- **`references/errors-and-nullability.md`** — nullable reference types as
  `Option`, hand-rolled `Option<T>`/`Result<T,E>`, railway-oriented programming in
  C#, the main libraries, and exceptions-at-the-edge. *Read for error handling.*
- **`references/pipelines-and-expressions.md`** — LINQ as the pipeline, deferred
  execution, expression-bodied members, local/static functions, higher-order
  functions, composition, and collection expressions. *Read for data processing
  or removing loops/mutation.*
- **`references/csharp14-features.md`** — the new C# 14 features mapped to
  functional style: extension members, the `field` keyword, null-conditional
  assignment, primary constructors, collection expressions, `params` collections.
  *Read to use the latest syntax idiomatically.*

## A taste

```csharp
// Closed model + total function + immutability + no null, no exceptions.
public abstract record PaymentResult;
public sealed record Approved(decimal Amount, string AuthCode) : PaymentResult;
public sealed record Declined(string Reason) : PaymentResult;
public sealed record Failed(Exception Cause) : PaymentResult;

static string Describe(PaymentResult result) => result switch
{
    Approved(var amt, var code) => $"Approved {amt:C} ({code})",
    Declined(var reason)        => $"Declined: {reason}",
    Failed(var ex)              => $"Error: {ex.Message}",
    _ => throw new UnreachableException(),   // until the `union` keyword makes this provably exhaustive
};
```

No mutable state, no inheritance-for-reuse, no null, no control-flow exceptions,
every case handled — and the shape of the data is the documentation. That is the
target for all C# here.
