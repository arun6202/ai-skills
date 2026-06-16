# Coroutines & tooling

Kotlin's concurrency model is **coroutines** with **structured concurrency**:
suspending functions that read like sequential code, run inside a scope that owns
their lifetime, and propagate cancellation and errors automatically. Plus the
project tooling and the K2 compiler.

## Suspend functions

A `suspend` function can pause without blocking a thread; you call it from another
suspend function or a coroutine builder:

```kotlin
suspend fun fetchUser(id: Int): User =
    withContext(Dispatchers.IO) {        // move blocking/IO work off the caller's thread
        api.getUser(id)
    }
```

`withContext` switches dispatcher for a block and returns its result. Mark IO/CPU
work with the right dispatcher; never block inside a coroutine (use suspending
equivalents like `delay`, not `Thread.sleep`).

## Structured concurrency — scopes own their work

Coroutines run in a **`CoroutineScope`**. Children launched in a scope can't
outlive it; if one fails, siblings are cancelled and the error propagates. This is
what makes concurrency leak-free.

```kotlin
suspend fun loadDashboard(): Dashboard = coroutineScope {   // returns when all children finish
    val user    = async { fetchUser() }      // run concurrently
    val orders  = async { fetchOrders() }
    Dashboard(user.await(), orders.await())
}
```

- **`coroutineScope { }`** — suspends until all children complete; fails fast if
  any child fails. Use it to run several things concurrently and combine results.
- **`async { }.await()`** — concurrent work that returns a value (`Deferred`).
- **`launch { }`** — fire a coroutine that returns no value (a `Job`); use for side
  effects.
- **`supervisorScope { }`** — children fail independently (one failure doesn't
  cancel siblings); use for independent tasks.

### Never use `GlobalScope`

`GlobalScope` coroutines aren't tied to any lifetime — they leak and ignore
cancellation. Instead, **inject a `CoroutineScope`** for work that must outlive the
current call (e.g. a service scope), or use the platform's lifecycle scope
(`viewModelScope`, `lifecycleScope` on Android). Always launch into a scope you
control.

## Cancellation

Cancellation is cooperative: suspending functions check for it, and you should too
in long CPU loops (`ensureActive()` / `yield()`). Cleanup goes in `finally`; don't
swallow `CancellationException` (rethrow it):

```kotlin
val job = scope.launch { work() }
job.cancel()                      // requests cancellation
```

## Flow — asynchronous streams

`Flow<T>` is a cold, suspending stream — the async sequence (think iterators that
arrive over time). It has the same functional operators as collections:

```kotlin
fun tick(): Flow<Int> = flow {
    var n = 0
    while (true) { emit(n++); delay(1000) }
}

tick()
    .map { it * 2 }
    .filter { it % 3 == 0 }
    .collect { println(it) }       // terminal operator; runs the flow
```

- **Cold** flows start when collected; operators (`map`/`filter`/`flatMapLatest`/
  `debounce`/…) are applied lazily.
- **`StateFlow`** — a hot, always-has-a-value observable holder (state); **`SharedFlow`**
  — a hot broadcast stream (events). Use `StateFlow` for UI/state, `SharedFlow` for
  one-off events.
- Choose dispatchers with `flowOn`; collect in a scope.

## Channels

For coroutine-to-coroutine communication (producer/consumer), use `Channel`
(hot, point-to-point). Prefer `Flow` for streams of data; reach for `Channel` when
you need queue-like hand-off between coroutines.

## Tooling

- **Gradle (Kotlin DSL)** — `build.gradle.kts`; the standard build tool. Use the
  Kotlin DSL for type-safe build scripts.
- **K2 compiler** — the rewritten frontend, **stable and default since Kotlin 2.0**
  (all targets: JVM, Native, Wasm, JS), with large compile-speed gains. Just use a
  2.x toolchain; nothing to opt into.
- **Kotlin Multiplatform (KMP)** — share Kotlin across JVM/Android/iOS/JS/Native
  from `commonMain`, with `expect`/`actual` for platform specifics. Increasingly
  the reason to choose Kotlin beyond Android.
- **ktlint** / **detekt** — formatting and static analysis; run in CI. Follow the
  official Kotlin coding conventions.
- **Testing** — JUnit5 or **Kotest** (expressive matchers/specs); `kotlinx-
  coroutines-test` (`runTest`, virtual time) for testing suspend/Flow code.
- **`kotlinx-serialization`** — `@Serializable` for compile-time JSON (no
  reflection); pairs with data classes.

## Recent language niceties (2.x)

- **Guard conditions in `when`** (2.1) — see `when-and-control-flow.md`.
- **Non-local `break`/`continue`** in inline-function lambdas (2.1).
- **`data object`** for stateless sealed cases; **`@JvmInline value class`** for
  zero-cost newtypes (see `data-and-modeling.md`).
- Prefer expression bodies, trailing lambdas, and named/default args throughout.

## Checklist

- [ ] Suspend functions + `withContext` for IO/CPU; never block a coroutine.
- [ ] Run concurrent work in a scope (`coroutineScope`/`supervisorScope`); never
      `GlobalScope`.
- [ ] Inject a `CoroutineScope` for work outliving the call; honor cancellation.
- [ ] `Flow` for streams; `StateFlow` for state, `SharedFlow` for events.
- [ ] Gradle Kotlin DSL, ktlint/detekt, Kotest/JUnit + coroutines-test in CI.
