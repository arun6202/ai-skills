# Safety without a compiler

Plain JavaScript can be *type-checked* — not at runtime, but by the TypeScript
engine reading your JSDoc, with zero build step and `.js` files. Combine that with
runtime validation at the edges, real `Error` handling, linting, and tests, and
JS becomes about as safe as it gets without committing to a `.ts` toolchain. This
is the JavaScript skill's signature move.

## `// @ts-check` + JSDoc

Put `// @ts-check` at the top of a `.js` file and the TypeScript language service
(in VS Code, and via `tsc`) checks it using JSDoc annotations:

```javascript
// @ts-check

/**
 * @param {string} name
 * @param {number} [count] - optional
 * @returns {string}
 */
function greet(name, count = 1) {
  return `Hi ${name}`.repeat(count);
}

greet(42);          // ✗ error: number not assignable to string — caught, in plain JS
```

To check a whole project instead of per-file, add a `jsconfig.json` (or
`tsconfig.json`) with `"checkJs": true` and `"allowJs": true`, and install
TypeScript as a dev dependency to run `tsc --noEmit` in CI:

```jsonc
// jsconfig.json
{ "compilerOptions": { "checkJs": true, "strict": true, "noUncheckedIndexedAccess": true },
  "include": ["src"] }
```

You get editor errors, autocomplete, and CI type-checking on ordinary JavaScript.

## JSDoc you'll actually use

```javascript
/** @type {string[]} */
const names = [];

/**
 * @typedef {object} User
 * @property {string} id
 * @property {string} name
 * @property {string} [email]   - optional property
 */

/** @type {User} */
const u = { id: '1', name: 'Ada' };

/**
 * Generic via @template.
 * @template T
 * @param {readonly T[]} arr
 * @returns {T | undefined}
 */
const first = (arr) => arr[0];

/** @typedef {{ kind: 'ok', value: number } | { kind: 'err', message: string }} Result */

// import a type from another module without importing a value:
/** @type {import('./user.js').User} */
let current;
```

Key tags: `@param`, `@returns`, `@type`, `@typedef`/`@property`, `@template`
(generics), `@satisfies` (TS 5.0+), `@readonly`, `@deprecated`. For complex/shared
shapes, define a `@typedef` once and reference it. JSDoc unions (`A | B`) plus a
`@type {never}` exhaustiveness check give you discriminated-union safety
(`objects-collections-and-data.md`).

## Validate untrusted input at the boundary

`@ts-check` checks your *code*, not runtime *data*. Anything crossing a trust
boundary — JSON, `fetch` responses, CLI args, env vars, form input — is `unknown`
in reality. Validate it once at the edge, then trust it inward:

```javascript
/** @param {unknown} data @returns {data is User} */
function isUser(data) {
  return typeof data === 'object' && data !== null
    && 'id' in data && typeof data.id === 'string'
    && 'name' in data && typeof data.name === 'string';
}

const raw = await res.json();      // unknown at runtime
if (!isUser(raw)) throw new Error('bad user payload');
use(raw);                          // now safely typed + validated
```

For anything beyond trivial shapes, use a **schema validator** — **zod** is the
common choice: one schema gives you runtime validation *and* an inferred JSDoc/TS
type, far less error-prone than hand-written guards:

```javascript
import { z } from 'zod';
const User = z.object({ id: z.string(), name: z.string(), email: z.string().optional() });
const user = User.parse(await res.json());   // throws on bad data; `user` is typed
```

## Error handling

- **Throw `Error` objects, never strings.** Strings lose stack traces and break
  `instanceof`:
  ```javascript
  throw new Error('config not found');                 // ✅
  throw new Error('load failed', { cause: originalErr }); // ✅ preserve the chain
  ```
- **Custom error types** for `instanceof` discrimination:
  ```javascript
  class ValidationError extends Error {
    /** @param {string} message */
    constructor(message) { super(message); this.name = 'ValidationError'; }
  }
  ```
- **Treat `catch` values as unknown** — anything can be thrown:
  ```javascript
  try { … } catch (err) {
    if (err instanceof Error) log(err.message);
    else log(`non-error thrown: ${String(err)}`);
  }
  ```
- Don't swallow errors (empty `catch`); handle, wrap-and-rethrow, or let them
  propagate. Reserve throwing for the exceptional — return values for expected
  outcomes (`Result`-style objects, see SKILL.md taste).

## Lint & test

- **ESLint** (flat config) is the standard linter. With `@ts-check`/a jsconfig you
  can enable typescript-eslint's type-aware rules on JS. High-value rules:
  `no-floating-promises`, `no-unused-vars`, `eqeqeq`, `no-var`,
  `no-implicit-coercion`, `prefer-const`. Add a formatter (Prettier or Biome).
- **`node:test`** is the built-in test runner — no dependency needed:
  ```javascript
  import { test } from 'node:test';
  import assert from 'node:assert/strict';
  test('parsePort rejects junk', () => {
    assert.deepEqual(parsePort('x'), { status: 'error', message: "'x' is not a valid port" });
  });
  ```
  Run with `node --test`. (Vitest/Jest remain fine if you already use them.)

## The safety stack, in order

1. `// @ts-check` + JSDoc (or a `jsconfig.json` with `checkJs`) → static checking.
2. Runtime validation (zod / guards) at every trust boundary.
3. `Error` objects + deliberate handling; no floating promises.
4. ESLint + formatter + `node:test`, all run in CI (`tsc --noEmit` for the type
   check).

If you find yourself writing extensive JSDoc generics and typedefs, that's the
signal to switch to TypeScript proper — see `idiomatic-typescript`.
