# Functions & immutability

JavaScript has first-class functions and closures — it's a strong functional
language. Lean on pure functions, immutable data, and array-method pipelines;
treat shared mutable state as the thing to avoid.

## Pure functions

A pure function's output depends only on its inputs and it mutates nothing
outside itself. Prefer them — they're testable, cacheable, and composable:

```javascript
// pure: returns a new value, touches nothing external
const withTax = (price, rate) => price * (1 + rate);

// impure: mutates an argument (avoid)
const addItemBad = (cart, item) => { cart.items.push(item); return cart; };
// pure version: returns a new cart
const addItem = (cart, item) => ({ ...cart, items: [...cart.items, item] });
```

Keep side effects (I/O, logging, DOM, network) at the edges; keep the core logic
pure.

## Immutability

`const` only stops *rebinding* — the object is still mutable. Encode immutability
by never mutating and producing new values:

```javascript
const moved   = { ...point, x: point.x + 10 };          // object update
const renamed = { ...user, name: 'Ada' };
const added   = [...items, newItem];                     // append
const removed = items.filter((i) => i.id !== id);        // remove
const updated = items.map((i) => i.id === id ? { ...i, done: true } : i); // update

const deepCopy = structuredClone(original);              // true deep clone
Object.freeze(config);                                    // shallow runtime lock
```

- **Spread** for shallow immutable updates (objects and arrays).
- **`structuredClone(x)`** for a real deep copy — replaces the
  `JSON.parse(JSON.stringify(x))` hack (which loses `Date`, `Map`, `undefined`,
  etc.).
- **`Object.freeze`** enforces shallow immutability at runtime (throws in strict
  mode on mutation); deep-freeze recursively if you need it. For *checked*
  immutability prefer JSDoc `readonly`/`@type` with `// @ts-check`
  (`safety-without-types.md`).
- Keep state shallow where you can — deep nesting makes immutable updates verbose
  and usually signals a flatter shape would serve better.

## Array methods over loops

Most loops are a `map` (transform), `filter` (keep), or `reduce` (fold). Name the
operation:

```javascript
// imperative
const names = [];
for (const o of orders) if (o.total > 100) names.push(o.customer.name);

// idiomatic
const names = orders.filter((o) => o.total > 100).map((o) => o.customer.name);
```

| Loop shape                | Method                                   |
|---------------------------|------------------------------------------|
| transform each            | `map`                                    |
| keep some                 | `filter`                                 |
| transform + flatten       | `flatMap`                                |
| running total / fold      | `reduce` (or `Math.max(...)`, etc.)      |
| first match               | `find` / `findLast` (`undefined` if none)|
| any / all                 | `some` / `every`                         |
| group / dedupe            | `Object.groupBy` / `new Set(...)`        |

Prefer the specific method (`some`, `find`) over a `reduce` reimplementing it.
Reach for `reduce` only when nothing else fits, and keep its callback small.

Use `for…of` (not a method) when the body is a *side effect*, when you need
`break`/`continue`, or when you must `await` in sequence (`async.md`).

## Higher-order functions & closures

Functions are values: pass them in to parameterize behavior, return them to
capture state:

```javascript
const by = (key) => (a, b) => a[key] < b[key] ? -1 : a[key] > b[key] ? 1 : 0;
users.sort(by('name'));

// closure captures `count` privately — a function, not a class
const makeCounter = () => {
  let count = 0;
  return () => ++count;
};
const next = makeCounter();
next(); next();   // 1, 2 — `count` is unreachable except through `next`
```

Closures are the lightweight alternative to a small stateful class: the state is
private by construction.

## Composition

No pipe operator yet; compose with small helpers or chaining:

```javascript
const pipe = (...fns) => (x) => fns.reduce((v, f) => f(v), x);
const compose = (...fns) => (x) => fns.reduceRight((v, f) => f(v), x);

const clean = pipe(
  (s) => s.trim(),
  (s) => s.toLowerCase(),
  (s) => s.replace(/\s+/g, '-'),
);
clean('  Hello World  ');   // 'hello-world'
```

## `this` and arrows

- In plain functional code, **avoid `this`** — use parameters and closures.
- Arrow functions inherit `this` lexically, so they're correct for callbacks and
  never need `.bind(this)`.
- Reserve regular `function`/methods for cases that genuinely need a dynamic
  `this` (object methods, class methods, some framework APIs). Don't pass an
  object method as a bare callback (`arr.forEach(obj.method)`) — it loses `this`;
  wrap it (`arr.forEach((x) => obj.method(x))`).

## Performance note

Array methods allocate intermediate arrays; for the overwhelming majority of code
that's irrelevant and clarity wins. On a measured hot path over large data, a
single `for…of` or a one-pass `reduce` (fusing steps) is a legitimate
optimization — keep the function pure on the outside even if it mutates a local
accumulator inside.
