# Asynchronous JavaScript

`async`/`await` over Promises is the idiom — flat, readable, try/catch-able.
The footguns are all about *not handling* a promise (floating rejections) and
*accidentally serializing or losing* parallel work. Get those right.

## `async`/`await`, not callbacks or `.then` chains

```javascript
async function loadUser(id) {
  const res = await fetch(`/users/${id}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
```

`await` unwraps a promise; an `async` function always returns a promise. Use
`try/catch` for errors (below). Reserve raw `.then()`/`.catch()` for terse
one-liners and places you can't use `await`.

## Never leave a promise floating

An unhandled promise rejection is a silent (or process-crashing) bug. Every
promise must be `await`ed, returned, or `.catch`ed:

```javascript
await save(data);                 // ✅ awaited
return save(data);                // ✅ returned (caller handles)
save(data).catch(reportError);    // ✅ explicitly handled (fire-and-forget)
save(data);                        // ❌ floating — rejection lost
```

Enable ESLint `no-floating-promises` (typescript-eslint, works on JS with
`@ts-check`) to catch these mechanically.

## Parallel vs sequential — choose deliberately

Independent async work should run **in parallel**; only `await` in a loop when each
step depends on the previous:

```javascript
// ❌ accidentally sequential — each await blocks the next
for (const id of ids) results.push(await fetchUser(id));

// ✅ parallel
const results = await Promise.all(ids.map((id) => fetchUser(id)));

// ✅ deliberately sequential (later depends on earlier)
let cursor;
for (const page of pages) cursor = await fetchPage(page, cursor);
```

### The `forEach`-async trap

`Array.prototype.forEach` ignores the promise its callback returns — the work is
launched but **not awaited**, so it neither blocks nor is error-handled:

```javascript
items.forEach(async (x) => { await save(x); });   // ❌ all floating, order lost
// use instead:
await Promise.all(items.map((x) => save(x)));     // parallel
for (const x of items) await save(x);             // sequential
```

## The Promise combinators

| Combinator              | Resolves when…                          | Use for…                              |
|-------------------------|-----------------------------------------|---------------------------------------|
| `Promise.all`           | all succeed (rejects on first failure)  | parallel work that must all succeed   |
| `Promise.allSettled`    | all settle (never rejects)              | run all, then inspect each outcome    |
| `Promise.race`          | first settles (resolve *or* reject)     | timeouts, first-wins                  |
| `Promise.any`           | first success (rejects only if all fail)| fastest successful source             |

```javascript
const outcomes = await Promise.allSettled(tasks);
const ok = outcomes.filter((o) => o.status === 'fulfilled').map((o) => o.value);
```

## Error handling in async code

```javascript
async function run() {
  try {
    const data = await load();
    return process(data);
  } catch (err) {
    // err is whatever was thrown/rejected — narrow it (don't assume Error)
    throw new Error('run failed', { cause: err });   // wrap with cause
  } finally {
    await cleanup();
  }
}
```

- `try/catch/finally` works naturally with `await`.
- Wrap-and-rethrow with `{ cause }` to preserve the original (see
  `safety-without-types.md`).
- A `catch (err)` value can be anything; guard with `err instanceof Error` before
  reading `.message`.

## Cancellation with `AbortController`

The standard cancellation mechanism — supported by `fetch`, timers, streams, and
your own functions:

```javascript
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), 5000);
try {
  const res = await fetch(url, { signal: controller.signal });
  return await res.json();
} finally {
  clearTimeout(timeout);
}
```

Accept a `{ signal }` in your own async APIs and check `signal.aborted` /
listen for `'abort'` to make them cancelable.

## `Promise.withResolvers` (ES2024)

When you must resolve/reject a promise from outside its executor (bridging
event-based APIs), `Promise.withResolvers()` is cleaner than the old captured-
variable pattern:

```javascript
const { promise, resolve, reject } = Promise.withResolvers();
emitter.once('done', resolve);
emitter.once('error', reject);
return promise;
```

## Async iteration & streams

For sequences that arrive over time (paginated APIs, streams), use async
generators and `for await…of`:

```javascript
async function* pages(url) {
  let next = url;
  while (next) {
    const res = await fetch(next);
    const page = await res.json();
    yield page.items;
    next = page.nextUrl;
  }
}

for await (const items of pages('/start')) handle(items);
```

## Rules of thumb

- Default to `async`/`await`; never leave a promise floating.
- Parallelize independent work with `Promise.all`; only `await`-in-loop when
  sequential by necessity. Never `await` inside `forEach`.
- Wrap-and-rethrow with `{ cause }`; treat `catch` values as unknown.
- Make long-running async APIs cancelable with `AbortSignal`.
