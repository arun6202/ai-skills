# Discriminated unions

This is TypeScript's superpower and the single highest-leverage modeling tool:
a value that is **exactly one of a fixed set of shapes**, distinguished by a
common literal *discriminant* property. Unlike C# (which needs union stop-gaps),
TypeScript has these natively, with compiler-checked exhaustiveness — squarely in
F# territory.

## The shape

Give every member a shared literal tag (commonly `kind`, `type`, `status`, or
`_tag`), then `switch` on it:

```typescript
type Shape =
  | { kind: 'circle'; radius: number }
  | { kind: 'rectangle'; width: number; height: number }
  | { kind: 'triangle'; base: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case 'circle':    return Math.PI * shape.radius ** 2;     // shape: the circle member
    case 'rectangle': return shape.width * shape.height;
    case 'triangle':  return 0.5 * shape.base * shape.height;
    default:          return assertNever(shape);
  }
}
```

Inside each `case`, TypeScript **narrows** `shape` to that member, so
`shape.radius` is available only in the `'circle'` branch — accessing the wrong
field is a compile error. The discriminant does the work; no casts, no `instanceof`.

## Exhaustiveness with `never`

The `assertNever` helper turns "forgot a case" into a **compile-time** error: if a
new member is added to the union, `shape` in the `default` branch is no longer
`never`, and the call fails to typecheck.

```typescript
function assertNever(x: never): never {
  throw new Error(`Unhandled case: ${JSON.stringify(x)}`);
}
```

This is the same guarantee F# gives by default and what C#'s upcoming `union`
keyword adds — and TypeScript has it today. Make every `switch` over a union end
with `default: return assertNever(x)` so adding a case lights up every site that
must change.

(Tip: `eslint`'s `@typescript-eslint/switch-exhaustiveness-check` can flag
non-exhaustive switches even without the `default` arm.)

## Make illegal states unrepresentable

The reason to reach for unions over a bag of optional fields: a union encodes only
the *legal* combinations. Compare:

```typescript
// ❌ illegal states representable: isLoading + error + data can all coexist
type State = {
  isLoading: boolean;
  data?: User;
  error?: string;
};

// ✅ exactly one state at a time
type State =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: User }
  | { status: 'error'; error: string };
```

With the union, "loading *and* error" can't be constructed, and `data` is only
reachable once you've narrowed to `'success'`. This is the TypeScript expression
of the domain-modeling discipline in the F# `functional-domain-modeling` skill.

## State machines

Unions model transitions cleanly — branch on `(state, event)`:

```typescript
type State = { kind: 'idle' } | { kind: 'running'; startedAt: number } | { kind: 'done'; result: string };
type Event = { kind: 'start' } | { kind: 'finish'; result: string } | { kind: 'reset' };

function reduce(state: State, event: Event): State {
  switch (state.kind) {
    case 'idle':    return event.kind === 'start'  ? { kind: 'running', startedAt: Date.now() } : state;
    case 'running': return event.kind === 'finish' ? { kind: 'done', result: event.result }     : state;
    case 'done':    return event.kind === 'reset'  ? { kind: 'idle' }                            : state;
    default:        return assertNever(state);
  }
}
```

## `Result` and `Option` as unions

Model expected failure as data instead of throwing (see `nullability-and-errors.md`):

```typescript
type Result<T, E> =
  | { ok: true;  value: T }
  | { ok: false; error: E };

type Option<T> =
  | { some: true;  value: T }
  | { some: false };

function parsePort(s: string): Result<number, string> {
  const n = Number(s);
  return Number.isInteger(n) && n > 0 && n < 65536
    ? { ok: true, value: n }
    : { ok: false, error: `'${s}' is not a valid port` };
}

const r = parsePort(input);
if (r.ok) use(r.value);          // narrowed to value
else      console.error(r.error); // narrowed to error
```

## Tips that keep unions clean

- **Pick one discriminant name** per union and make it a string literal (`kind`,
  `type`, `status`). Numbers/booleans work but read worse.
- **Keep members flat and specific** — each carries exactly the data that state
  needs, nothing more (no shared optional fields "just in case").
- **Name the member types** when reused across functions:
  ```typescript
  type Circle = { kind: 'circle'; radius: number };
  type Shape  = Circle | Rectangle | Triangle;
  ```
- **Narrow with the discriminant**, not `instanceof`/`as`. A `switch` or
  `if (x.kind === '…')` is all you need.
- **Prefer unions to inheritance** for closed sets of variants with open
  operations — add an operation = a new function with a `switch`, not a method on
  every subclass.
