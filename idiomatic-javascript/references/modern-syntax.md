# Modern syntax baseline

The non-negotiable modern baseline. Most JavaScript footguns come from ES5-era
habits; the modern equivalents are shorter and safer. Write to this baseline by
default.

## `const` / `let` — never `var`

```javascript
const MAX = 100;            // default: a binding that won't be reassigned
let total = 0;             // only when you genuinely reassign
total += 1;
```

- `var` is function-scoped and hoisted with surprising semantics — don't use it.
- `const`/`let` are block-scoped. Reach for `const` first; switch to `let` only
  when you reassign the binding. (`const` doesn't freeze the object — see
  `functions-and-immutability.md` for immutability.)

## `===` — never `==`

```javascript
if (x === 0) …            // strict equality, no coercion
if (value == null) …       // the ONE allowed loose check: matches null AND undefined
```

`==` does type coercion with infamous edge cases (`'' == 0`, `[] == ![]`). Always
use `===`/`!==`. The single idiomatic exception: `x == null` (or `x != null`) is a
deliberate, well-understood way to test "null or undefined" at once.

## Arrow functions (and when not)

```javascript
const double = (x) => x * 2;
const points = nums.map((n) => ({ x: n, y: n * n }));   // () around object literal
```

- Arrows are concise and **don't bind their own `this`** — which is exactly what
  you want for callbacks (no more `const that = this`).
- Use a regular `function` (or method shorthand) when you *need* a dynamic `this`
  (object methods relying on the caller, some framework hooks) or a named hoisted
  declaration. In plain functional code, avoid `this` entirely.

## Destructuring

```javascript
const { id, name, email = 'n/a' } = user;        // object, with default
const [first, second, ...rest] = items;          // array + rest
const { data: { items = [] } = {} } = response;  // nested, defensive

function move({ x, y }, dx) { return { x: x + dx, y }; }   // params
```

Destructuring makes intent explicit and pairs with defaults to handle missing
values cleanly.

## Spread & rest

```javascript
const merged = { ...defaults, ...overrides };    // object spread (later wins)
const copy   = [...items];                        // shallow array copy
const all    = [...a, ...b];                       // concat
const max    = Math.max(...nums);                  // spread args
function sum(...xs) { return xs.reduce((a, b) => a + b, 0); }   // rest params
```

Spread replaces `Object.assign`, `.concat`, `.apply`, and `arguments` in almost
all cases, and is the basis of immutable updates.

## Template literals

```javascript
const msg = `Hello ${name}, you have ${count} item${count === 1 ? '' : 's'}`;
const sql = `
  SELECT * FROM users
  WHERE id = ${id}
`;
```

Use template literals instead of `+` concatenation; they handle interpolation and
multi-line strings. (For untrusted interpolation into HTML/SQL, still
escape/parameterize — template literals don't sanitize.)

## Optional chaining & nullish coalescing

```javascript
const city = user?.address?.city ?? 'unknown';   // safe access + default
arr?.[0];                                          // optional index
fn?.(arg);                                         // optional call
config.timeout ??= 30;                             // assign only if null/undefined
```

- `?.` short-circuits to `undefined` if the left side is `null`/`undefined`.
- `??` supplies a default only for `null`/`undefined` — prefer it to `||`, which
  also triggers on `0`, `''`, `false` (a frequent bug: `count || 10` turns a real
  `0` into `10`).
- Logical assignment: `??=`, `||=`, `&&=`.

## `for…of` (not `for…in`, not C-style)

```javascript
for (const item of items) doSomething(item);        // values
for (const [key, value] of Object.entries(obj)) …    // object pairs
for (const [i, item] of items.entries()) …           // index + value
```

- `for…of` iterates *values* of any iterable (arrays, Maps, Sets, strings).
- **Avoid `for…in`** for arrays/data — it iterates enumerable *keys* (including
  inherited ones) as strings. Use `Object.keys/values/entries` for objects.
- Prefer array methods (`map`/`filter`/…) when producing a value; use `for…of`
  for side effects or when you need `break`/`await` (see
  `functions-and-immutability.md` and `async.md`).

## Modules (ESM)

```javascript
import { readFile } from 'node:fs/promises';
import { parse } from './parser.js';      // explicit extension in Node ESM
export function run() { … }
export const VERSION = '1.0.0';
```

Use ES modules (`import`/`export`) for new code — static, tree-shakeable, and the
standard everywhere. Avoid `namespace`-style IIFEs and global `var`s; a module's
top level is already its own scope and is strict by default. (CommonJS interop and
`"type": "module"` details are in `modern-platform.md`.)

## Other modern niceties

```javascript
items.at(-1);                       // last element (negative indexing)
items.findLast((x) => x.active);    // search from the end
Object.hasOwn(obj, 'key');          // safe own-property check (not `in`/hasOwnProperty)
const n = Number.parseInt(s, 10);   // always pass the radix
label: for (…) { … break label; }    // labeled loops when truly needed
```
