---
name: functional-domain-modeling
description: >-
  Design F# domain models, bounded contexts, and business workflows the
  type-driven, domain-driven way — the method of Scott Wlaschin's "Domain
  Modeling Made Functional". Use this whenever you model a domain or business
  rule in F#, design a use-case / workflow / pipeline, structure an F#
  application (domain core vs boundaries vs composition root), turn commands into
  events, model entity lifecycles/state machines, inject dependencies the
  functional way, handle errors at application scale (railway-oriented
  programming), or set up serialization/persistence boundaries with DTOs. Reach
  for this for any "how should I structure / model this in F#" question — not
  just when DDD is named. Part of the `idiomatic-code` family; complements `stylish-fsharp` (micro-level idioms) and
  `fsharp-vs-frontier` (positioning); emit idiomatic F# per those.
---

# Functional domain modeling

Design the domain with **types first, implementation second.** A good F# domain
model reads like the domain expert's own words, makes illegal states impossible
to construct, and expresses each business workflow as a single typed function.
The implementation then becomes "make the compiler happy" — and when it
compiles, large classes of bugs are already gone. This is the method of
*Domain Modeling Made Functional* (Scott Wlaschin), distilled.

The mantra: **the types are the design.** Spend your thinking on the type
signatures; the bodies follow.

## Core principles

1. **Ubiquitous language in types.** Name types and cases exactly as the domain
   expert speaks (`PricedOrder`, `Vip`, `WidgetCode`). A non-programmer should be
   able to read your type definitions. Code and conversation share one vocabulary.
2. **Make illegal states unrepresentable.** Encode every rule in the type so bad
   data cannot be constructed — then you never re-check it downstream. (See
   `stylish-fsharp/references/domain-modeling.md` for the type mechanics; this
   skill applies them at domain scale.)
3. **Constrain at the edge, trust at the core.** Wrap primitives in validated
   types (`String50`, `EmailAddress`, `OrderId`) whose only constructor returns a
   `Result`. Once inside the domain, values are always valid — "parse, don't
   validate." See `references/constrained-types.md`.
4. **A workflow is a function.** Model each business use case as one typed
   function from a command/input to a `Result`/`AsyncResult` of output events:
   `type PlaceOrder = UnvalidatedOrder -> AsyncResult<PlaceOrderEvent list, PlaceOrderError>`.
   Design every step as a *type* before writing any body. See `references/workflows.md`.
5. **States are types; transitions are functions.** Model a lifecycle as distinct
   types (`UnvalidatedOrder` → `ValidatedOrder` → `PricedOrder`), each step taking
   one and producing the next. The compiler then forbids skipping a stage (you
   can't price an unvalidated order). See `references/workflows.md`.
6. **Effects in the type, not hidden.** "Can fail" shows up as `Result`,
   "is async" as `Async`, both as `AsyncResult`. Keep total/pure steps plain and
   lift them where they meet effectful ones. See `references/effects-and-errors.md`.
7. **Dependencies are parameters.** Pass capabilities (`checkProductExists`,
   `getProductPrice`) as leading function arguments and inject them by partial
   application at a single composition root. No DI container, no interfaces-for-
   mocking. See `references/workflows.md`.
8. **Keep the domain pure; push I/O to the edges.** The core is total functions
   over immutable data. Database, network, JSON, and clock live at the boundary,
   behind DTOs and injected dependencies. See `references/boundaries-and-architecture.md`.

## The shape of a bounded context

DMMF lays a context out so dependencies point *inward* and the file order tells
the story (mirrors the `OrderTaking` sample):

| File / layer            | Holds                                                            |
|-------------------------|-----------------------------------------------------------------|
| `Common.SimpleTypes`    | constrained primitives (`String50`, `OrderId`, `OrderQuantity`) |
| `Common.CompoundTypes`  | shared records/DUs built from them (`Address`, `CustomerInfo`)   |
| `*.PublicTypes`         | the workflow's input command, output events, error DU, and the **workflow function type** — the context's public contract |
| `*.InternalTypes`       | per-step function types + intermediate state types (design-first)|
| `*.Implementation`      | the step bodies + the workflow assembled as a pipeline           |
| `*.Dto`                 | primitive DTOs + `toDomain`/`fromDomain` at the boundary          |
| `*.Api`                 | composition root: wire real dependencies, serialize, expose      |

The pure domain (SimpleTypes → Implementation) knows nothing of JSON, HTTP, or
databases. Those appear only in `Dto` and `Api`.

## Workflow: how to model a new domain

1. **Gather the verbs and nouns.** Capture the workflow (a verb: "place order")
   and its data (nouns) in the domain expert's language. Note what's required vs
   optional, and what can go wrong.
2. **Write the input, events, and error types**, then the workflow function type.
   Get sign-off on these signatures *before* implementing — they're the design.
3. **Constrain the primitives** as single-case DUs with smart constructors.
4. **Type each step** (`InternalTypes`): inputs, dependencies, output, effect.
5. **Implement steps** as small functions; **compose** them into the workflow with
   `result`/`asyncResult`, normalizing each step's error into the workflow's
   error DU.
6. **Add boundaries last**: DTOs + serialization, then wire dependencies in the
   composition root.

## Reference files — read on demand

- **`references/constrained-types.md`** — the systematic smart-constructor
  pattern and the shared `ConstrainedType` helper module. *Read when modeling
  primitives / value objects.*
- **`references/workflows.md`** — workflows as typed functions, design-with-types,
  states-as-types pipelines, commands/events, and dependency injection by partial
  application. *Read when designing a use case or application flow.*
- **`references/effects-and-errors.md`** — `Result`/`Async`/`AsyncResult`, the
  `result`/`asyncResult` CEs, normalizing errors into a workflow error DU,
  `sequence`/`traverse`, and applicative validation (collect all errors).
  *Read when wiring error handling or async into a pipeline.*
- **`references/boundaries-and-architecture.md`** — the functional onion /
  hexagonal layout, DTOs (`toDomain`/`fromDomain`), the serialization pipeline,
  persistence ignorance, and integration events between contexts. *Read when
  structuring an app or crossing a boundary.*
