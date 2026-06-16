# Nullability & errors

Track absence and failure in the types. With strict null checking on, `null`/
`undefined` are honest parts of a type the compiler forces you to handle; and for
expected failures, prefer a `Result` value over a thrown exception so callers
can't ignore the error.

## `strictNullChecks` is non-negotiable

Under `strict` (default in TS 6.0), `null` and `undefined` are not assignable to
other types — they must appear explicitly, and you must narrow before use:

```typescript
function find(id: string): User | undefined { … }

const u = find(id);
u.name;                 // ❌ Object is possibly 'undefined'
if (u) u.name;          // ✅ narrowed
```

This eliminates the "cannot read property of undefined" class of bug at compile
time. Never turn it off.

## `null` vs `undefined` — pick a convention

TypeScript/JS have both. They behave almost identically in the type system; the
noise comes from mixing them. A pragmatic convention:

- Use **`undefined`** for "absent" (missing property, no return value, optional
  parameter) — it's what `?` and most APIs produce.
- Reserve **`null`** for "explicitly set to nothing" when an API/DB distinguishes
  it, or to match an external contract (JSON, the DOM).
- Use optional properties `field?: T` (which is `T | undefined`) rather than
  `field: T | null` unless you specifically need `null`.

Whatever you choose, be consistent; don't return `null` from one function and
`undefined` from its sibling.

## Optional chaining & nullish coalescing

These two operators replace ad-hoc null ladders:

```typescript
const city = user?.address?.city ?? 'unknown';   // safe access + default
obj.cache ??= new Map();                          // assign only if null/undefined
list?.forEach(fn);                                // call only if present
```

- **`?.`** short-circuits to `undefined` if the left side is `null`/`undefined`.
- **`??`** supplies a fallback only for `null`/`undefined` (unlike `||`, which also
  fires on `0`, `''`, `false` — a frequent bug). Prefer `??` for defaults.

## Expected failure → `Result`, not `throw`

Throwing is invisible in the type signature — callers don't know a function can
fail, and TypeScript can't force them to handle it. For *expected* failures
(validation, parsing, I/O you anticipate), return a discriminated union instead
(see `discriminated-unions.md`):

```typescript
type Result<T, E> =
  | { ok: true;  value: T }
  | { ok: false; error: E };

function parseConfig(raw: unknown): Result<Config, string> {
  if (!isConfigShape(raw)) return { ok: false, error: 'invalid config' };
  return { ok: true, value: raw };
}

const r = parseConfig(input);
if (!r.ok) { reportError(r.error); return; }
use(r.value);                                  // r.value narrowed to Config
```

Model the error as a **typed value** — a string, or better a union of error cases
— so callers can branch and you can render messages at the edge:

```typescript
type ParseError =
  | { kind: 'empty' }
  | { kind: 'tooLong'; max: number }
  | { kind: 'badFormat'; value: string };
```

### Compose results (railway-style)

Small helpers let you chain fallible steps without nesting, the same railway as
the F#/C# skills:

```typescript
const map = <T, U, E>(r: Result<T, E>, f: (t: T) => U): Result<U, E> =>
  r.ok ? { ok: true, value: f(r.value) } : r;

const flatMap = <T, U, E>(r: Result<T, E>, f: (t: T) => Result<U, E>): Result<U, E> =>
  r.ok ? f(r.value) : r;
```

For anything substantial, use a library rather than hand-rolling: **`neverthrow`**
(`Result`/`ResultAsync` with `.map`/`.andThen`/`.match`) is the popular choice;
**Effect** offers a full typed effect system (`Effect<A, E, R>`) if you want F#-
computation-expression-grade composition with dependency tracking.

## `unknown` in `catch`

Errors are `unknown` (with `useUnknownInCatchVariables`, on under `strict`) —
narrow before use; don't assume `Error`:

```typescript
try {
  await save();
} catch (e: unknown) {
  if (e instanceof Error) log(e.message);
  else log(`Non-error thrown: ${String(e)}`);
}
```

## When to throw

Throwing is still right for the genuinely exceptional and for programmer errors:

- **Invariant violations / bugs** — an impossible state, a failed precondition,
  `assertNever`. Crash loudly.
- **Truly unexpected I/O** at a boundary you'll catch-and-convert into a `Result`
  one level up.
- Don't throw for ordinary, expected branches (not-found, validation failed,
  user typo) — that's what `Result`/`undefined` are for.

Convert exceptions to results at the boundary so the core stays total:

```typescript
async function readJson(path: string): Promise<Result<unknown, string>> {
  try { return { ok: true, value: JSON.parse(await readFile(path, 'utf8')) }; }
  catch (e) { return { ok: false, error: e instanceof Error ? e.message : String(e) }; }
}
```

## Rules of thumb

- `strictNullChecks` on; narrow before dereferencing.
- `??`/`?.` over manual null checks and over `||` for defaults.
- Return `Result`/`T | undefined` for expected failure; throw only for bugs and
  unexpected boundary errors, converting to `Result` at the edge.
- Treat `catch` variables as `unknown`.
