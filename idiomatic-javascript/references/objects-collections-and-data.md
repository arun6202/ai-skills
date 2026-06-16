# Objects, collections & data modeling

Model data with plain objects and the right collection type. Reach for a `class`
only when it earns its place. JavaScript's structural, dynamic nature makes plain
objects + functions the natural default — the same "data + functions" shape the
F#/TS skills favor.

## Plain objects are the default container

```javascript
const user = { id: '1', name: 'Ada', roles: ['admin'] };

// build behavior as functions over data, not methods on a class:
const isAdmin = (u) => u.roles.includes('admin');
```

Object shorthand, computed keys, and spread keep this terse:

```javascript
const make = (name, value) => ({ name, [`${name}Id`]: value });   // shorthand + computed key
const patched = { ...user, name: 'Ada L.' };                       // immutable update
```

Add JSDoc + `// @ts-check` to get these shapes type-checked (see
`safety-without-types.md`).

## Discriminated unions by convention

JavaScript has no native unions, but the *pattern* is just a plain object with a
literal tag (`kind`/`type`/`status`) and a `switch` — the same modeling discipline
as TypeScript, enforced by JSDoc:

```javascript
// @ts-check

/**
 * @typedef {{ kind: 'circle', radius: number }}              Circle
 * @typedef {{ kind: 'rect', width: number, height: number }} Rect
 * @typedef {Circle | Rect} Shape
 */

/** @param {Shape} shape @returns {number} */
function area(shape) {
  switch (shape.kind) {
    case 'circle': return Math.PI * shape.radius ** 2;
    case 'rect':   return shape.width * shape.height;
    default: {
      /** @type {never} */
      const _exhaustive = shape;   // type error if a case is unhandled
      throw new Error(`unhandled: ${JSON.stringify(shape)}`);
    }
  }
}
```

This makes illegal states unrepresentable (a circle can't carry `width`) and,
with `@ts-check`, gives compile-time exhaustiveness via the `never` assignment —
the F# idea, in plain JS.

## `Map` / `Set` vs objects

Use the right structure:

- **Plain object** — a fixed-ish record with known string keys (a DTO, config).
- **`Map`** — a dynamic key→value dictionary, especially with non-string keys,
  frequent add/delete, or when insertion order and `.size` matter:
  ```javascript
  const byId = new Map(users.map((u) => [u.id, u]));   // lookup table
  byId.get('1'); byId.has('1'); byId.size;
  ```
- **`Set`** — a collection of unique values; dedupe with `[...new Set(xs)]`.
  ES2025 adds set algebra: `a.intersection(b)`, `a.union(b)`, `a.difference(b)`.

Prefer `Map` over an object-as-dictionary when keys are user/data-driven (avoids
prototype-key pitfalls like `__proto__` and inherited keys).

## Iterating and reshaping objects

```javascript
Object.keys(obj);                       // ['a', 'b']
Object.values(obj);                     // [1, 2]
Object.entries(obj);                    // [['a', 1], ['b', 2]]
Object.fromEntries(pairs);              // build an object from [k, v] pairs

// transform an object immutably via entries:
const upper = Object.fromEntries(
  Object.entries(obj).map(([k, v]) => [k, String(v).toUpperCase()]),
);

// group rows by a key (ES2024):
const byRole = Object.groupBy(users, (u) => u.roles[0] ?? 'none');
```

Use `Object.hasOwn(obj, key)` (not `key in obj`, which sees inherited keys; not
`obj.hasOwnProperty` directly).

## When a `class` earns its place

Default to plain objects + functions/closures. Choose a `class` when you genuinely
need:

- **Encapsulated mutable state with invariants** — use `#private` fields so the
  state is truly hidden:
  ```javascript
  class RingBuffer {
    #items = [];
    #cap;
    constructor(cap) { this.#cap = cap; }
    push(x) { this.#items.push(x); if (this.#items.length > this.#cap) this.#items.shift(); }
    get items() { return [...this.#items]; }   // hand out a copy, not the internals
  }
  ```
- **`instanceof` identity** — notably **custom error types** (`extends Error`, see
  `safety-without-types.md`).
- **A framework base class** you must extend, or an interface/protocol you must
  implement.

Even then: prefer **composition over inheritance** (deep `extends` chains are a JS
anti-pattern), keep fields `#private`, expose behavior via methods, and don't hand
out internal references. A small stateful need is often better served by a
closure (`functions-and-immutability.md`) than a class.

## Avoid prototype hacking

Don't mutate built-in prototypes (`Array.prototype.foo = …`) or hand-wire
`Object.create`/`__proto__` inheritance chains in app code — it breaks tooling,
collides across libraries, and confuses readers. Use modules, plain objects,
composition, and (where warranted) `class`.
