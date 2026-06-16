# Modern platform & features

The runtime and module landscape, plus the recently standardized library you can
reach for. Knowing what's modern keeps you from hand-rolling things the platform
now provides — and from using a feature your target can't run.

## ES modules vs CommonJS

Write **ES modules** (`import`/`export`) for new code — the standard for browsers
and Node, statically analyzable and tree-shakeable.

```javascript
// ESM
import { readFile } from 'node:fs/promises';
import { parse } from './parser.js';     // Node ESM needs the explicit extension
export function run() {}
export default config;
```

- In Node, opt a package into ESM with `"type": "module"` in `package.json` (then
  `.js` is ESM; use `.cjs` for an occasional CommonJS file, `.mjs` to force ESM).
- **CommonJS** (`require`/`module.exports`) is legacy but everywhere; you'll read
  and maintain it. Don't write new CJS unless a constraint demands it. Modern Node
  can even `require()` synchronous ESM, but prefer clean ESM.
- Use the **`node:` prefix** for built-ins (`node:fs`, `node:path`, `node:test`) —
  explicit and unambiguous.

## Recently standardized library (ES2024–2026)

Reach for these instead of utilities or hacks — but confirm your runtime/baseline
supports them (Node 22+/24+ and current browsers cover most; the ES2026 set is
newest):

**ES2024**
- `Object.groupBy(items, fn)` / `Map.groupBy(...)` — group without `reduce`.
- `Promise.withResolvers()` — get `{ promise, resolve, reject }` (see `async.md`).
- `Array.fromAsync(asyncIterable)` — build an array from an async iterable.
- `/v` RegExp flag (set notation, string properties).

**ES2025**
- **Iterator helpers** — lazy `.map`/`.filter`/`.take`/`.drop`/`.flatMap`/
  `.reduce`/`.toArray` directly on iterators, no intermediate arrays:
  ```javascript
  const firstThreeEvens = numbers.values().filter((n) => n % 2 === 0).take(3).toArray();
  ```
- **Set methods** — `union`, `intersection`, `difference`, `symmetricDifference`,
  `isSubsetOf`, `isSupersetOf`, `isDisjointFrom`.
- `Promise.try(fn)` — start a sync-or-async fn on the promise track, catching sync
  throws.
- `RegExp.escape(str)` — safely escape a string for use in a RegExp.
- **Import attributes** — `import data from './x.json' with { type: 'json' }`.

**ES2026**
- **`Temporal`** — the modern date/time API replacing the broken `Date`. Use it
  for date math, time zones, and durations once your runtime ships it.
- **Explicit resource management** — `using` / `await using` for deterministic
  cleanup (see below).
- `Error.isError(x)`, `Math.sumPrecise(iterable)`, `Uint8Array` base64/hex methods.

## Explicit resource management (`using`)

`using` binds a disposable and calls its `[Symbol.dispose]()` when the block
exits — JS's `try/finally`-free cleanup (like C#/Python `with`). `await using`
awaits `[Symbol.asyncDispose]()`:

```javascript
function openFile(path) {
  const handle = openSync(path);
  return { handle, [Symbol.dispose]() { closeSync(handle); } };
}

{
  using file = openFile('data.txt');
  read(file.handle);
}   // file disposed automatically here, even on throw
```

Reach for it for files, locks, DB connections, spans — anything with paired
acquire/release. (Newest feature; verify runtime/transpiler support.)

## Always pass the radix / be explicit

```javascript
Number.parseInt('08', 10);   // 8 — always pass radix 10
Number.isNaN(x);             // not the global isNaN (which coerces)
Number.isInteger(x);
structuredClone(obj);        // deep clone (not JSON round-trip)
crypto.randomUUID();          // standard UUIDs, no library
```

## Node.js versions (2026)

- **Node 24** — current **Active LTS**; the default target for new work.
- **Node 22** — **Maintenance LTS**; fine for existing apps.
- **Node 26** — Current (non-LTS); enters LTS in October 2026.
- Node is moving to **one major release per year** starting with Node 27.

Target **Active or Maintenance LTS** for anything you ship; pin the engine in
`package.json` `"engines"`. Newer Node also runs `.ts` via type-stripping and has
`--watch`, `--env-file`, and a stable built-in test runner — see below.

## Running and tooling

- **Run**: `node script.js`. `node --watch` re-runs on change; `--env-file=.env`
  loads env vars without a dependency.
- **Test**: `node --test` with the built-in `node:test` + `node:assert/strict`
  (no dependency). Vitest/Jest remain fine if already in use.
- **Type-check**: install `typescript` as a dev dep and run `tsc --noEmit` over
  your `// @ts-check`/`checkJs` JS in CI (see `safety-without-types.md`).
- **Lint/format**: ESLint (flat config) + Prettier, or **Biome** for an
  all-in-one fast linter+formatter.

## When to switch to TypeScript

This skill makes plain JS good; but if you find yourself:

- writing extensive JSDoc `@typedef`/`@template` generics,
- wanting enums, interfaces, or richer type modeling, or
- already running a build/bundler step,

…then the friction has crossed the line — use **`idiomatic-typescript`** instead.
JSDoc-typed JS is designed to be a smooth on-ramp: the same type concepts, so
migrating `.js` → `.ts` is mostly mechanical when the time comes.
