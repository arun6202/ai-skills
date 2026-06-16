# Types & inference

The foundation: describe data precisely, let the compiler infer what it can, and
annotate the boundaries. TypeScript's structural type system is a tool for making
illegal states unrepresentable — use it, don't fight it with `any`/`as`.

## `type` vs `interface`

Both describe object shapes; the differences guide the choice:

- **`type`** — the default for this skill. Required for unions, tuples, mapped and
  conditional types, function types, and primitive/literal aliases. Use it for
  data and variants.
  ```typescript
  type Id = string;
  type Status = 'active' | 'inactive';          // unions need `type`
  type Point = { readonly x: number; readonly y: number };
  type Handler = (e: Event) => void;
  ```
- **`interface`** — best when you want an extensible/implementable object
  *contract*: `extends`, `implements`, or declaration merging (e.g. augmenting a
  library type). It also gives slightly faster checking and sometimes cleaner
  error messages for large object types.
  ```typescript
  interface Repository<T> { get(id: string): Promise<T | undefined>; }
  ```

Rule of thumb: **`type` for data and unions; `interface` for object contracts you
expect to extend/implement.** Don't agonize — they're interchangeable for plain
objects. Be consistent within a codebase.

## Let inference work; annotate boundaries

Over-annotation is noise; under-annotation lets `any` creep in. The balance:

- **Don't annotate** what TS infers correctly: local `const`/`let`, obvious return
  types, callback parameters with contextual typing.
  ```typescript
  const total = items.reduce((sum, x) => sum + x.price, 0);   // all inferred
  ```
- **Do annotate**: function *parameters* (no contextual type otherwise), the
  *return type of exported/public functions* (locks the contract, catches drift,
  speeds checking), and anything where inference would widen wrongly.
  ```typescript
  export function parsePrice(input: string): number | undefined { … }
  ```

Annotating exported return types is the highest-value habit: it documents intent
and turns an accidental return-type change into a local error instead of a
surprise at the call site.

## `unknown` and `never` — the honest top and bottom

- **`unknown`** is the type-safe `any`: it accepts any value but lets you do
  *nothing* with it until you narrow. Use it for untrusted input (JSON, `catch`,
  library boundaries) and narrow with guards (`narrowing-and-guards.md`).
- **`never`** is the empty type: no value has it. It's how you get
  **exhaustiveness** (`assertNever(x: never)`) and the result of functions that
  never return. If a variable is unexpectedly `never`, your union narrowing is
  already complete.

Banish `any`: enable `noImplicitAny`, and treat an explicit `any` as a TODO. When
you think you need `any`, you almost always want `unknown` + a guard, or a
generic.

## `as const` — preserve literals, derive types from data

`as const` makes a literal deeply `readonly` and keeps its *narrowest* type, so
you can derive a union type from a single source of truth:

```typescript
const ROLES = ['admin', 'editor', 'viewer'] as const;
type Role = typeof ROLES[number];          // 'admin' | 'editor' | 'viewer'

const ROUTES = { home: '/', user: '/user/:id' } as const;
type RouteKey = keyof typeof ROUTES;       // 'home' | 'user'
```

This is the idiomatic replacement for `enum`: one runtime array/object *and* a
derived type, no separate declaration to drift, and the values are plain strings.

## `satisfies` — check without widening

`satisfies` (TS 4.9+) validates that a value conforms to a type while keeping the
value's *narrow inferred* type — unlike a type annotation, which widens it:

```typescript
type Config = Record<string, string | number>;

const config = {
  port: 3000,
  host: 'localhost',
} satisfies Config;

config.port.toFixed();   // ✅ `port` is still `number`, not `string | number`
```

Use `satisfies` whenever you want "make sure this matches the type, but let me
keep the specific keys/values I wrote."

## Avoid `enum`

TS `enum`s are quirky: numeric enums allow out-of-range values, they emit runtime
code, `const enum` has its own caveats, and they don't play well with structural
typing or tree-shaking. Prefer a **union of string literals** (zero runtime, fully
checked) or an **`as const` object** when you also need a runtime value list:

```typescript
type Direction = 'north' | 'south' | 'east' | 'west';   // most cases

const Direction = { North: 'north', South: 'south' } as const;
type Direction = typeof Direction[keyof typeof Direction];   // when you need values too
```

## Structural typing (not nominal)

TS types are compatible by *shape*, not by name: anything with the right members
fits. This enables flexible composition, but means two different concepts with the
same shape are interchangeable. When you need a *nominal* distinction (an `Email`
that isn't just any `string`), use a **branded type**:

```typescript
type Email = string & { readonly __brand: 'Email' };
// only a validating parser can produce one — see narrowing-and-guards.md
```

## Utility types — transform existing types

Reuse types instead of re-declaring; the built-ins cover most needs:

| Utility            | Produces                                   |
|--------------------|--------------------------------------------|
| `Partial<T>`       | all properties optional                    |
| `Required<T>`      | all properties required                    |
| `Readonly<T>`      | all properties `readonly`                  |
| `Pick<T, K>`       | subset of properties                       |
| `Omit<T, K>`       | T without properties K                     |
| `Record<K, V>`     | object type with keys K, values V          |
| `ReturnType<F>` / `Parameters<F>` | a function's return / params |
| `NonNullable<T>`   | T without `null`/`undefined`               |
| `Awaited<T>`       | the awaited result of a Promise            |

```typescript
type User = { id: string; name: string; email: Email };
type UserPatch = Partial<Omit<User, 'id'>>;   // editable fields, all optional
```

## Generics — precise, constrained

Use generics (not `any`) for code that's shape-agnostic; constrain them with
`extends` so the body stays type-safe:

```typescript
function first<T>(arr: readonly T[]): T | undefined { return arr[0]; }
function prop<T, K extends keyof T>(obj: T, key: K): T[K] { return obj[key]; }
```

Let call-site inference fill the type parameters; annotate them only when
inference can't (or use `const` type params / `NoInfer` — see
`modern-ts-and-config.md`).
