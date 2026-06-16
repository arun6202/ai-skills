# Null safety

Kotlin bakes nullability into the type system: `String` can never be null,
`String?` might be. The compiler forces you to handle the nullable case, so NPEs
are largely designed out — *unless* you reach for `!!`. The whole game is **handle
null safely**; `!!` is the smell to avoid.

## Nullable vs non-nullable types

```kotlin
val name: String = "Ada"     // never null
val maybe: String? = find()  // String or null

maybe.length                  // ❌ compile error: maybe might be null
name.length                   // ✅ always fine
```

A non-nullable type genuinely can't hold null, so most of your code never thinks
about it. Add `?` only where absence is real.

## Safe calls `?.` and Elvis `?:`

```kotlin
val len: Int? = maybe?.length          // null if maybe is null, else its length
val len: Int = maybe?.length ?: 0      // Elvis: supply a default for null
val city = user?.address?.city ?: "—"  // chain safe calls
maybe?.let { println(it) }             // run a block only when non-null
```

- **`?.`** short-circuits to `null` if the receiver is null.
- **`?:`** (Elvis) provides a fallback for `null` — the idiomatic replacement for
  `if (x != null) x else default`.
- Elvis also handles early exit: `val u = find() ?: return` / `?: throw ...`.

## Smart casts

Once you've checked for null (or type), the compiler **narrows** the type for the
rest of the scope — no re-checking, no cast:

```kotlin
fun greet(name: String?) {
    if (name != null) {
        println(name.length)   // `name` is smart-cast to non-null String here
    }
}

fun describe(x: Any): String =
    if (x is String) "string of ${x.length}" else "other"   // smart cast after `is`
```

Smart casts work for `val`s and local `var`s the compiler can prove haven't
changed. (A mutable property accessed across threads won't smart-cast — capture it
in a local `val` first.)

## `?.let` for "do this if non-null"

A clean idiom for running a block on a non-null value:

```kotlin
user?.email?.let { sendWelcome(it) }   // only if both are non-null

// transform-or-default:
val display = name?.let { "Hi, $it" } ?: "Hi, guest"
```

(See `functions-and-extensions.md` for the full scope-function family.)

## Avoid `!!`

`value!!` throws an NPE if `value` is null — it throws away exactly the safety the
type system gives you:

```kotlin
val n = map["key"]!!            // ❌ NPE if absent
val n = map["key"] ?: error("key missing")   // ✅ explicit, with a message
```

Better alternatives when you expect non-null:

- **`?:` with a default or `error()`/`throw`** — explicit handling.
- **`requireNotNull(x) { "msg" }`** / **`checkNotNull(x)`** — assert with a clear
  message (preconditions vs invariants).
- **Restructure** so the value is non-nullable in the first place (e.g. validate
  at the boundary, then carry a non-null type).

Reserve `!!` for cases you can *prove* are non-null and even then prefer the
explicit forms. It's acceptable in tests.

## `lateinit` — narrow use only

`lateinit var` lets you declare a non-null property initialized later (DI,
framework lifecycle) without making it nullable:

```kotlin
private lateinit var repository: UserRepository   // set in onCreate/init
```

Use it only for genuine deferred initialization (Android views, injected
dependencies), not to dodge nullability for ordinary values — accessing it before
assignment throws. For lazily-computed values prefer `by lazy { }`.

## Java interop: platform types

Values coming from Java have **platform types** (`String!`) — the compiler doesn't
know if they're nullable, so it won't protect you, and an unexpected null becomes
an NPE at first use. At the interop boundary:

- **Annotate or assume nullable**: treat Java return values as `T?` and handle
  null, or rely on `@Nullable`/`@NotNull` annotations the library provides.
- **Validate once at the boundary** (`requireNotNull`, `?:`) and carry a clean
  non-null Kotlin type inward.

## Rules of thumb

- Model "maybe absent" as `T?`; let non-nullable types stay null-free.
- Handle null with `?.` / `?:` / smart casts / `?.let` — `guard`-style early exit
  with `?: return`/`throw`.
- Don't `!!`; use `requireNotNull`/`?: error(...)` or restructure.
- Treat Java values as nullable until proven otherwise; sanitize at the boundary.
