# Immutability & pipelines

Default to immutable data and transform it with pure functions and array methods.
Mutation and index loops are the JavaScript habit; the idiomatic, safer form is
`readonly` types updated by producing new values, processed through `map`/
`filter`/`reduce`.

## Make data `readonly`

Encode immutability in the type so accidental mutation is a compile error:

```typescript
type Point = { readonly x: number; readonly y: number };

const p: Point = { x: 1, y: 2 };
p.x = 5;                          // ❌ compile error

// whole-type / arrays:
type Config = Readonly<{ host: string; port: number }>;
function sum(xs: readonly number[]): number { … }   // ReadonlyArray<number>
```

- Mark record fields `readonly`, or wrap with `Readonly<T>`.
- Accept `readonly T[]` (a.k.a. `ReadonlyArray<T>`) in function parameters — it
  both signals "I won't mutate this" and accepts mutable arrays too.
- `as const` makes a literal deeply readonly *and* narrows its type
  (`types-and-inference.md`) — ideal for constant tables/config.

## Update immutably

"Change" a value by building a new one with the spread operator — never mutate in
place:

```typescript
const moved   = { ...p, x: p.x + 10 };               // object update
const renamed = { ...user, name: 'Ada' };
const added   = [...items, newItem];                 // array append
const removed = items.filter((i) => i.id !== id);    // array remove
const updated = items.map((i) => i.id === id ? { ...i, done: true } : i); // array update
```

For deep updates, spread at each level (or use a library like Immer with care).
Keep state shallow where you can — deep nesting makes immutable updates verbose
and is often a sign a discriminated union or a flatter shape would serve better.

## Pipelines over loops

Most loops are a `map` (transform), `filter` (keep), or `reduce` (fold). Name the
operation; it's shorter and bug-resistant:

```typescript
// Imperative:
const names: string[] = [];
for (const o of orders) if (o.total > 100) names.push(o.customer.name);

// Pipeline:
const names = orders
  .filter((o) => o.total > 100)
  .map((o) => o.customer.name);
```

| Loop shape                        | Array method                              |
|-----------------------------------|-------------------------------------------|
| transform each                    | `map`                                     |
| keep some                         | `filter`                                  |
| transform + flatten               | `flatMap`                                 |
| running total / reduce            | `reduce` (or `Math.max(...)`, etc.)       |
| first match                       | `find` (`undefined` if none)              |
| any / all                         | `some` / `every`                          |
| group by key                      | `Object.groupBy` / `Map.groupBy`          |
| de-dupe                           | `[...new Set(xs)]`                        |
| build a lookup                    | `new Map(xs.map((x) => [x.id, x]))`       |

Prefer the specific method (`some`, `find`) over a `reduce` that reimplements it.
Reach for `reduce` only when no named method fits — and keep its callback small.

## Keep callbacks pure & short

A pipeline reads well when each step is a glance. Lift a growing lambda to a named
function and pass it point-free:

```typescript
const isExpensive = (o: Order): boolean => o.total > 100;
const customerName = (o: Order): string => o.customer.name;

const names = orders.filter(isExpensive).map(customerName);
```

Pure callbacks (no external mutation, output depends only on input) make pipelines
predictable and the functions reusable/testable.

## Composition

TypeScript has no pipe operator yet, but composition is easy. For a few steps,
nest or chain; for many, a small `pipe` helper reads top-to-bottom:

```typescript
const pipe = <T>(x: T, ...fns: Array<(v: T) => T>): T => fns.reduce((v, f) => f(v), x);

const clean = (s: string) => pipe(s, (x) => x.trim(), (x) => x.toLowerCase());
```

(For heterogeneous, fully-typed pipelines, use the `pipe` from a library such as
Remeda or Effect rather than hand-rolling the overloads.)

## Performance note

Array methods allocate intermediate arrays; for the vast majority of code this is
irrelevant and clarity wins. On a measured hot path over large data, a single
`for...of` (or `reduce` in one pass, fusing steps) is a legitimate optimization —
keep the function pure on the outside even if it mutates a local accumulator
inside.

```typescript
// One-pass fold instead of filter().map().reduce():
const total = orders.reduce((sum, o) => o.total > 100 ? sum + o.total : sum, 0);
```

Write it clean and immutable first; optimize the proven hot spot, not by reflex.
