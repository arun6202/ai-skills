# Narrowing & type guards

The functional alternative to casting: instead of telling the compiler "trust me"
with `as`, *prove* a value's type so the compiler narrows it for you. Narrowing is
how you safely consume `unknown` and discriminated unions — and every `as` you
remove is a bug the compiler can now catch.

## Built-in narrowing

TypeScript follows control flow and narrows types automatically:

```typescript
function describe(x: string | number | null) {
  if (x === null)         return 'nothing';
  if (typeof x === 'string') return x.toUpperCase();   // x: string here
  return x.toFixed(2);                                   // x: number here
}
```

The narrowing operators:

- **`typeof`** — for primitives: `'string' | 'number' | 'boolean' | 'bigint' |
  'symbol' | 'undefined' | 'object' | 'function'`.
- **`instanceof`** — for class instances: `if (e instanceof Error) …`.
- **`in`** — for object shape: `if ('radius' in shape) …`.
- **Truthiness & equality** — `if (x)`, `if (x != null)`, `x === 'literal'`
  (the discriminant check for unions).
- **`Array.isArray(x)`** — for arrays.

Let narrowing do the work before reaching for a guard or a cast.

## User-defined type guards (`x is T`)

When a check is reusable or too complex for inline narrowing, write a function
whose return type is a **type predicate** `arg is T`. A `true` result narrows the
argument at the call site:

```typescript
type User = { id: string; name: string };

function isUser(x: unknown): x is User {
  return typeof x === 'object' && x !== null
    && 'id' in x && typeof (x as { id: unknown }).id === 'string'
    && 'name' in x && typeof (x as { name: unknown }).name === 'string';
}

const data: unknown = await res.json();
if (isUser(data)) {
  data.name;        // ✅ narrowed to User
}
```

This is the safe gateway from `unknown` (JSON, external input) into your typed
world. For anything beyond trivial shapes, prefer a **schema validator** (zod,
valibot) that gives you a guard *and* a derived type from one definition — far
less error-prone than hand-written guards.

### Inferred type predicates (TS 5.5+)

Since 5.5, TypeScript can often infer the predicate from a function body, so a
filter narrows without an explicit annotation:

```typescript
const names = [1, 'a', 2, 'b'];
const strings = names.filter((x) => typeof x === 'string');   // string[] inferred
```

Still write explicit `x is T` for exported/public guards where the contract should
be pinned.

## Assertion functions (`asserts`)

When you want to *throw* on failure rather than branch, use an assertion function.
After it returns, the type is narrowed for the rest of the scope:

```typescript
function assert(condition: unknown, message?: string): asserts condition {
  if (!condition) throw new Error(message);
}

function assertIsString(x: unknown): asserts x is string {
  if (typeof x !== 'string') throw new TypeError('expected string');
}

function handle(input: unknown) {
  assertIsString(input);
  input.trim();          // ✅ input: string from here on
}
```

Use these at trust boundaries and for invariants that should crash loudly.

## Discriminant narrowing (unions)

For discriminated unions, the discriminant *is* the guard — no custom function
needed (see `discriminated-unions.md`):

```typescript
if (shape.kind === 'circle') shape.radius;   // narrowed
```

## Avoid `as` — and the safer ways when you can't

Type assertions (`value as Foo`) tell the compiler to stop checking — they're a
common source of runtime errors that "shouldn't happen." Replace them:

- **Narrowing / guards** instead of `as` (above).
- **`satisfies`** to *check* a literal against a type without changing it
  (`types-and-inference.md`) — frequently what people reach for `as` to do.
- **Generics** instead of `as` to thread a type through.

When an assertion is genuinely unavoidable (e.g. you know more than the compiler
about a `JSON.parse` result you've already validated):

- Keep it as narrow as possible and *adjacent to a real check*.
- Prefer `as const` and branded-type parsers over bare `as SomeBigType`.
- **Never** use the double assertion `as unknown as T` except at a truly
  unavoidable FFI boundary, with a comment explaining why.
- Avoid the non-null assertion `x!`; narrow with `if (x)` or `x ?? throw`-style
  handling instead — `!` hides exactly the `null` the compiler was warning about.

## `unknown` in `catch`

With `useUnknownInCatchVariables` (on under `strict`), a caught error is `unknown`
— narrow it before use:

```typescript
try {
  risky();
} catch (e: unknown) {
  if (e instanceof Error) console.error(e.message);
  else console.error('Unknown error', e);
}
```

## Rules of thumb

- Prefer control-flow narrowing → type guard → `satisfies` → (last resort)
  carefully-scoped `as`.
- Turn untrusted `unknown` into typed values at one guarded boundary (ideally a
  schema), then trust the types inward.
- Write explicit `x is T` for shared guards; lean on inference for inline filters.
- Treat `as` and `!` as smells to justify, not defaults.
