# Modern TypeScript & config

The compiler config is part of the design: a strict tsconfig is what makes all the
other idioms in this skill enforceable. Plus the recent language features worth
reaching for, and the 2026 tooling landscape.

## Strict tsconfig — the non-negotiables

`strict: true` is the baseline (and the default in **TS 6.0+**). But `strict`
doesn't include several high-value flags — turn these on too:

```jsonc
{
  "compilerOptions": {
    "strict": true,                          // noImplicitAny, strictNullChecks, etc.
    "noUncheckedIndexedAccess": true,        // arr[i] is T | undefined — huge for safety
    "exactOptionalPropertyTypes": true,      // `x?: T` ≠ `x: T | undefined`
    "noImplicitOverride": true,              // must write `override`
    "noFallthroughCasesInSwitch": true,
    "noImplicitReturns": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "verbatimModuleSyntax": true,            // explicit `import type`, clean ESM emit
    "isolatedModules": true,                 // safe for single-file transpilers/bundlers

    "target": "ES2022",
    "module": "NodeNext",                    // or "ESNext"/"Preserve" per bundler
    "moduleResolution": "NodeNext",
    "skipLibCheck": true
  }
}
```

- **`noUncheckedIndexedAccess`** is the most underused safety flag: it makes
  `array[i]` and `record[key]` return `T | undefined`, forcing you to handle the
  out-of-bounds/missing case. Pairs perfectly with narrowing.
- **`strict`** is what gives you `strictNullChecks`, `noImplicitAny`, and
  `useUnknownInCatchVariables` — the foundations the rest of this skill assumes.
- Use a vetted base like `@tsconfig/strictest` and extend it, rather than
  hand-maintaining every flag.

## ES modules, not namespaces

Use `import`/`export` (ESM). `namespace` is legacy (a pre-modules module system) —
don't write new ones. With `verbatimModuleSyntax`, separate type-only imports:

```typescript
import { createUser } from './user.js';
import type { User } from './user.js';        // erased at runtime
export type { User };
```

(In `NodeNext`, relative imports use the `.js` extension even from `.ts` sources —
the path is the *output* path.) TS 6.0 makes **ESM the default** module mode.

## Recent language features worth using

- **`satisfies`** (4.9) — check a value against a type without widening it; often
  what you actually wanted instead of `as` (`types-and-inference.md`).
- **`using` / `await using`** (5.2) — explicit resource management. A `using`
  binding calls `[Symbol.dispose]()` (or `[Symbol.asyncDispose]()`) at scope exit —
  the deterministic-cleanup pattern (like C# `using`):
  ```typescript
  function openFile(path: string) {
    const handle = acquire(path);
    return { handle, [Symbol.dispose]() { handle.close(); } };
  }
  { using f = openFile('a.txt'); read(f.handle); }   // f disposed here
  ```
- **`const` type parameters** (5.0) — `<const T>` infers the *narrowest* (literal,
  readonly) type for an argument without the caller writing `as const`.
- **`NoInfer<T>`** (5.4) — block inference at one position so another argument
  drives the type parameter (e.g. constrain a value to a previously-given set).
- **Inferred type predicates** (5.5) — `filter(x => typeof x === 'string')`
  narrows to `string[]` without an explicit `x is T` (`narrowing-and-guards.md`).
- **`Object.groupBy` / `Map.groupBy`** (runtime, ES2024) — group without `reduce`.

## The TS 7 native compiler (Go) — what to know

The compiler is being rewritten in **Go** ("Project Corsa", binary **`tsgo`**,
repo `microsoft/typescript-go`):

- **TS 6.0** (March 2026) is the **last JavaScript-based** release — it also
  flipped defaults: `strict` on, ESM default.
- **TS 7.0** (beta, April 2026, via `@typescript/native-preview` / `tsgo`) is the
  native compiler — Microsoft cites **~10× faster** builds and editor responsiveness
  with near-complete type-checking parity.
- **It is a compiler/tooling rewrite, not a language change.** The types, syntax,
  and semantics are the same; everything in this skill applies unchanged. Adopt
  `tsgo` for speed when it's stable for your setup; you don't rewrite code for it.

Until TS 7 is stable for your project, build/check with TS 6.x; you can trial
`tsgo` side by side.

## Running TypeScript

- **Node.js** can run `.ts` directly via **type stripping** (`node file.ts`;
  unflagged from Node 23.6 / available in 22 LTS behind a flag) — it erases types,
  it does not type-check. Type-check separately with `tsc --noEmit`/`tsgo`.
- **`tsx`** runs/watches TS for dev with full transpilation; **`tsc`** (or `tsgo`)
  is the type checker and emitter; **bundlers** (esbuild/Vite/Rollup) transpile but
  don't type-check — always run a real type check in CI.
- For libraries, emit declaration files (`"declaration": true`); consider
  `isolatedDeclarations` for fast, parallelizable `.d.ts` generation.

## Lint & format

- **typescript-eslint** (`typescript-eslint` flat config) is the standard linter;
  enable the type-checked rules (`recommendedTypeChecked`/`strictTypeChecked`).
  High-value rules: `no-explicit-any`, `no-unnecessary-condition`,
  `switch-exhaustiveness-check`, `no-floating-promises`,
  `consistent-type-imports`.
- **Prettier** for formatting (or Biome for an all-in-one fast linter+formatter).
- Wire `tsc --noEmit` + eslint into CI and pre-commit. The compiler and linter
  together enforce the idioms so you don't have to police them by hand.

## Checklist

- [ ] `strict` + `noUncheckedIndexedAccess` (+ the extras above) on.
- [ ] ESM only; `import type` for types; no `namespace`.
- [ ] No `any` (`no-explicit-any`); `as`/`!` justified, not reflexive.
- [ ] Type-check in CI (bundler/Node-strip alone don't check types).
- [ ] Reach for `satisfies`, `using`, `const` type params where they fit.
