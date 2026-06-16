---
name: idiomatic-javascript
description: >-
  Write, refactor, or review modern, idiomatic, functional-leaning JavaScript
  (.js, .mjs, .cjs) — for when you're genuinely in plain JS: a build-free script,
  a small Node tool/CLI, a library that ships JS, a browser snippet, or config.
  Use this for any "write a JS script/function" request. Steers toward modern ES
  (modules, const, ===, ?./??), type safety WITHOUT a compiler via `// @ts-check`
  + JSDoc + runtime validation, immutability and array methods over mutation and
  loops, correct async/await (no floating promises), plain-object data modeling,
  and Error-based error handling — away from var/==/callback-hell/prototype/`this`
  footguns. If a build step is available, prefer TypeScript (`idiomatic-typescript`);
  this skill is for real JavaScript, made safe and clean.
---

# Idiomatic JavaScript

Modern JavaScript is a capable, expression-oriented, functional-friendly language
— first-class functions, closures, modules, rich array/iterator methods, and (via
`// @ts-check` + JSDoc) most of TypeScript's safety with **zero build step**. The
job of this skill is to write JS that is modern, safe, and clean despite the
language's long tail of footguns and the muscle memory of ES5-era and OOP habits.

**First decision: should this even be plain JS?** If you control the toolchain,
TypeScript is usually the better choice — use the `idiomatic-typescript` skill.
Reach for *this* skill when JS is the right tool: a tiny script with no build, a
Node one-off, a published package that ships `.js`, a `<script>` in a page, a
config file, or a quick automation. Then make it genuinely good.

> **Part of the `idiomatic-code` family** — the shared cross-language philosophy and the Rosetta Stone (porting + review) live there.
>
> Stack family: the "make illegal states unrepresentable", discriminated-union,
> and railway-error ideas come from the F# skills, `functional-csharp`, and
> `idiomatic-typescript`. In JS you express them with plain objects + a `kind`
> tag, and you get type *checking* from JSDoc rather than the syntax — same ideas,
> lighter enforcement.

## Break the muscle memory (reflex → idiomatic)

When your instinct fires the left column, write the right column instead.

| Reflex (ES5 / OOP / habit)                          | Idiomatic modern JS                                                  |
|-----------------------------------------------------|---------------------------------------------------------------------|
| `var`                                               | `const` by default; `let` only when reassigned                      |
| `==` / `!=`                                          | `===` / `!==` (no coercion surprises)                               |
| `for (let i=0; …)` building an array                | `map`/`filter`/`reduce`/`flatMap`; `for…of` for effects             |
| Mutating shared objects/arrays                      | Immutable update: spread, pure functions, `structuredClone`         |
| `function` + `prototype` inheritance                | Modules + composition; `class` only when it earns it                |
| Nested callbacks                                    | `async`/`await` over Promises                                       |
| `const that = this` / `.bind(this)`                 | Arrow functions; avoid `this` in plain code                         |
| `arguments`                                         | Rest params `(...args)`                                             |
| `f.apply(null, arr)`                                | Spread: `f(...arr)`                                                 |
| `'Hello ' + name + '!'`                             | Template literals: `` `Hello ${name}!` ``                          |
| `JSON.parse(JSON.stringify(x))` to clone           | `structuredClone(x)`                                                |
| `require`/`module.exports` (new code)              | ESM `import`/`export`                                               |
| `throw 'oops'`                                       | `throw new Error('oops', { cause })`                                |
| `items.forEach(async …)`                            | `for…of` + `await`, or `await Promise.all(items.map(…))`           |
| Untyped "hope it works"                             | `// @ts-check` + JSDoc + validate input at the boundary             |
| `obj && obj.a && obj.a.b`                           | `obj?.a?.b`                                                          |
| `x != null ? x : d`                                 | `x ?? d`                                                             |

If you truly need runtime identity, a base class from a framework, or
encapsulated mutable state — use a `class` (with `#private` fields). Make it a
decision, not a default.

## The creed

1. **Modern baseline.** ES modules, `const`/`let`, `===`, `?.`/`??`, arrow
   functions, destructuring, template literals. No `var`, no `==`, no
   `arguments`.
2. **Type-safe without a compiler.** Put `// @ts-check` atop files and describe
   shapes with JSDoc; validate untrusted input at the boundary. You get
   editor-grade checking on plain `.js`.
3. **Functional-leaning.** Pure functions, immutability, array methods, closures.
   Avoid shared mutable state; reach for `class` only with a reason.
4. **Async done right.** `async`/`await`, never a floating promise; parallelize
   with `Promise.all`/`allSettled`; don't `await` in a `forEach`.
5. **Model data as plain objects.** Discriminated unions by convention (a `kind`
   tag) + `switch`; classes are not the default container.
6. **Fail with `Error` objects.** `throw new Error(msg, { cause })`; handle
   rejections; never swallow.
7. **Lint and test.** ESLint + a formatter; `node:test` for tests; run a type
   check (`tsc --checkJs`) in CI.

## Quick reach-for guide

| You need to…                              | Reach for…                                                       |
|-------------------------------------------|------------------------------------------------------------------|
| Types in plain JS                         | `// @ts-check` + JSDoc `@param`/`@returns`/`@typedef`            |
| "One of N shapes" / a state              | Plain objects with a `kind` tag + `switch` (+ JSDoc union)       |
| Transform a collection                    | `map`/`filter`/`reduce`/`flatMap`                                |
| "Maybe absent"                            | `?.` / `??`; return `undefined`; validate at edges               |
| Deep copy                                 | `structuredClone(x)`                                            |
| Run async work in parallel                | `await Promise.all(items.map(fn))`                              |
| Group / dedupe                            | `Object.groupBy` / `Map.groupBy`; `new Set(...)`               |
| Validate untrusted input (JSON, args)     | a schema (zod) or a JSDoc-typed guard                          |
| Deterministic resource cleanup            | `using` (explicit resource management) where supported          |

## Reference files — read on demand

- **`references/modern-syntax.md`** — the modern baseline: `const`/`let`, `===`,
  arrow functions, destructuring, spread/rest, template literals, `?.`/`??`/logical
  assignment, `for…of`, modules. *Read to replace ES5 patterns.*
- **`references/functions-and-immutability.md`** — pure functions, closures,
  higher-order functions, composition, immutable update, `Object.freeze`,
  `structuredClone`, array-method pipelines, `this`/arrow nuances. *Read for
  functional style.*
- **`references/objects-collections-and-data.md`** — plain objects vs `Map`/`Set`,
  discriminated unions by convention, when a `class` (with `#private`) earns its
  place, `Object.entries/fromEntries/groupBy`, iteration. *Read when modeling
  data.*
- **`references/async.md`** — Promises, `async`/`await`, error handling,
  `Promise.all`/`allSettled`/`race`/`any`, the `forEach`-async trap, parallel vs
  sequential, `AbortController`, `Promise.withResolvers`, async iteration. *Read
  for async code.*
- **`references/safety-without-types.md`** — `// @ts-check` + JSDoc (typedefs,
  generics, unions), runtime validation at boundaries, `Error` handling, ESLint,
  `node:test`. *Read to make JS correct without TypeScript.*
- **`references/modern-platform.md`** — ESM vs CommonJS, the recent standard
  library (ES2024–2026: `Object.groupBy`, iterator helpers, Set methods,
  `Promise.withResolvers`, `using`, `Temporal`), Node LTS, running JS, and when to
  switch to TypeScript. *Read for platform/feature currency.*

## A taste

```javascript
// @ts-check

/**
 * @typedef {{ status: 'ok', value: number }} Ok
 * @typedef {{ status: 'error', message: string }} Err
 * @typedef {Ok | Err} Parsed
 */

/**
 * @param {string} input
 * @returns {Parsed}
 */
function parsePort(input) {
  const n = Number(input);
  return Number.isInteger(n) && n > 0 && n < 65536
    ? { status: 'ok', value: n }
    : { status: 'error', message: `'${input}' is not a valid port` };
}

const result = parsePort(process.argv[2] ?? '');
switch (result.status) {
  case 'ok':    console.log(`port ${result.value}`); break;
  case 'error': console.error(result.message); break;
  default: { /** @type {never} */ const _ = result; throw new Error('unreachable'); }
}
```

`const`, `===`, modules-ready, no mutation, expected failure as a value, every
case handled — and `// @ts-check` + JSDoc means the editor and CI type-check this
plain `.js` file. That is the target for all JavaScript here.
