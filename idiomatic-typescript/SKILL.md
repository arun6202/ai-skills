---
name: idiomatic-typescript
description: >-
  Write, refactor, or review idiomatic, type-driven, functional-leaning
  TypeScript (.ts, .tsx, .mts). Use this whenever you produce TypeScript — even a
  quick "write this in TS" — to steer toward making illegal states
  unrepresentable: discriminated unions over class hierarchies and enums,
  `unknown` over `any`, narrowing over `as` assertions, immutability and array
  methods over mutation and loops, strict null handling, and exhaustiveness
  checking with `never`. Reach for it when modeling data/state, choosing
  `type` vs `interface`, handling errors, fixing `any`/`as` soup, or setting up a
  strict tsconfig. Counters the reflexes of OOP-heavy, `any`-laden,
  loosely-typed TypeScript. Targets TS 6.x (strict + ESM default) and notes the
  TS 7 native (Go/`tsgo`) compiler.
---

# Idiomatic TypeScript

TypeScript is, at its best, a **type-driven, functional-leaning** language: a
structural type system powerful enough to make illegal states unrepresentable,
with native discriminated unions and exhaustiveness checking that put it in the
same league as F# for domain modeling. Write to that strength — model data
precisely with `type`s and unions, transform it with pure functions and array
methods, and let the compiler prove your code total.

The enemy is muscle memory: untyped JavaScript habits (`any`, mutation, loops)
and reflexive OOP (deep class hierarchies, inheritance, `enum`). Default to the
type-driven, functional form below; reach for a class or a mutation only with a
reason.

> **Part of the `idiomatic-code` family** — the shared cross-language philosophy and the Rosetta Stone (porting + review) live there.
>
> Part of a stack family. The "make illegal states unrepresentable" and
> railway-error ideas come straight from the F# skills (`stylish-fsharp`,
> `functional-domain-modeling`) and the C# one (`functional-csharp`). TypeScript
> has **native** discriminated unions and exhaustiveness — so it does this even
> more directly than C# (which needs union stop-gaps).

## Break the muscle memory (reflex → idiomatic)

When your instinct fires the left column, write the right column instead.

| Reflex (JS / OOP / habit)                           | Idiomatic TypeScript                                                |
|-----------------------------------------------------|---------------------------------------------------------------------|
| `any`                                               | `unknown` + narrowing, or a real type                               |
| `value as Foo` to silence the compiler              | Narrow with a type guard; use `satisfies` to *check* without widening|
| `enum Color { ... }`                                | Union of literals `type Color = 'red' \| 'green'`, or `as const`    |
| Class hierarchy + inheritance for data/variants     | Discriminated union + functions (or composition)                    |
| `class` for a plain data bag                        | `type`/`interface` object; a function to build it                   |
| Mutating arrays/objects (`push`, reassign fields)   | Immutable update: spread, `readonly`, `map`/`filter`                |
| `for`/`forEach` building an array                   | `map`/`filter`/`reduce`/`flatMap`                                   |
| `throw` for expected failure                        | `Result<T,E>` union / typed errors                                  |
| `x!` non-null assertion                             | Narrow it (`if (x) …`), or fix the type                             |
| Ad-hoc `if (x !== null && x !== undefined)`         | `strictNullChecks` + `?.` / `??`                                    |
| `namespace Foo { }`                                 | ES modules (`import`/`export`)                                      |
| `Object` / `Function` / `{}` as a type             | A precise type, `Record<K,V>`, or `unknown`                         |
| Boolean flags with illegal combinations             | Discriminated union of the legal states                             |
| `(x: any) => …` generic-ish helper                  | A real generic with a constraint: `<T extends …>`                   |

If you genuinely need runtime identity, a framework base class, or
encapsulated mutable state — use a class. Make it a decision, not a default.

## The creed

1. **Make illegal states unrepresentable.** Model with discriminated unions,
   `readonly`, branded primitives, and `required`/precise fields so bad data can't
   typecheck. A wrong program should fail to compile.
2. **`unknown`, never `any`.** `any` disables the type system silently. `unknown`
   forces you to narrow before use. Treat `any` (and implicit `any`) as a bug.
3. **Narrow, don't assert.** Prefer control-flow narrowing and type guards over
   `as`. Every `as` is a place the compiler stopped helping you.
4. **Let inference work; annotate boundaries.** Don't annotate what TS infers;
   *do* annotate function parameters, return types of exported/public functions,
   and module API surfaces.
5. **Types are data; functions are behavior.** Reach for `type` + unions over
   class hierarchies; pass functions, not one-method objects.
6. **Immutable by default.** `readonly`, `as const`, spread updates, and array
   methods. New value, not mutation.
7. **Strict, always.** `strict` plus the extra safety flags (see
   `references/modern-ts-and-config.md`). The stricter the config, the more bugs
   the compiler catches for free.

## Quick reach-for guide

| You need to…                              | Reach for…                                                       |
|-------------------------------------------|------------------------------------------------------------------|
| "One of N shapes" / a state              | Discriminated union (`{ kind: '…' } \| …`) + `switch` + `never`  |
| A data bundle                             | `type`/`interface` with `readonly` fields                        |
| A fixed set of names                      | Union of string literals, or `as const` object                   |
| "Maybe absent"                            | `T \| undefined` + `?.`/`??` (strict null checks on)             |
| "Succeeds or fails with a reason"         | `Result<T,E>` union (or `neverthrow`)                            |
| Validate untrusted input                  | `unknown` + type guard / schema (zod) → narrowed type           |
| Check a literal against a type            | `satisfies` (keeps the narrow inferred type)                     |
| Constrain a primitive (Email, UserId)     | Branded type + a `parse`-style guard                            |
| Transform a collection                    | `map`/`filter`/`reduce`/`flatMap`                                |
| Generic over object keys                  | `<K extends keyof T>`                                             |

## Reference files — read on demand

- **`references/types-and-inference.md`** — `type` vs `interface`, inference vs
  annotation, `unknown`/`never`, `as const`, `satisfies`, literal & union types,
  why to avoid `enum`, structural typing, utility types, generics. *Read when
  shaping types.*
- **`references/discriminated-unions.md`** — TypeScript's superpower: tagged
  unions, exhaustive `switch` with `assertNever`, state machines, illegal-states-
  unrepresentable, `Result`/`Option` as unions. *Read when modeling variants or
  state.*
- **`references/narrowing-and-guards.md`** — control-flow narrowing,
  `typeof`/`instanceof`/`in`, user-defined guards (`x is T`), assertion functions
  (`asserts`), exhaustiveness, and avoiding `as`. *Read for safely handling
  `unknown`/unions.*
- **`references/immutability-and-pipelines.md`** — `readonly`/`Readonly<T>`/
  `ReadonlyArray`, `as const`, immutable update patterns, array-method pipelines,
  composition, pure functions. *Read for functional data processing.*
- **`references/nullability-and-errors.md`** — `strictNullChecks`, `null` vs
  `undefined`, `?.`/`??`, `Result`/`Option`, `unknown` in `catch`, typed errors,
  when to throw. *Read for error handling.*
- **`references/modern-ts-and-config.md`** — strict tsconfig (the non-negotiable
  flags), ESM, recent features (`satisfies`, `using`, `const` type params,
  `NoInfer`, inferred predicates), the TS 7 native (Go/`tsgo`) compiler, running
  TS, typescript-eslint. *Read for setup and latest features.*

## A taste

```typescript
// Illegal states unrepresentable + total function + no any, no mutation.
type RemoteData<T> =
  | { readonly status: 'loading' }
  | { readonly status: 'success'; readonly data: T }
  | { readonly status: 'error'; readonly message: string };

function render<T>(state: RemoteData<T>, show: (data: T) => string): string {
  switch (state.status) {
    case 'loading': return 'Loading…';
    case 'success': return show(state.data);   // `data` is narrowed in, typed T
    case 'error':   return `Error: ${state.message}`;
    default:        return assertNever(state); // compile error if a case is added
  }
}

function assertNever(x: never): never {
  throw new Error(`Unhandled case: ${JSON.stringify(x)}`);
}
```

No `any`, no `as`, no mutation, every case handled (the compiler proves it via
`never`), and the union *is* the documentation. That is the target for all
TypeScript here.
