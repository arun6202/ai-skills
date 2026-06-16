# C# 14 / .NET 10 features for functional style

The C# 14 additions (shipped in .NET 10, November 2025) lean the language further
toward concise, functional code. Use them idiomatically — here's what each buys a
functional-leaning codebase.

## Extension members (the headline)

C# 14 generalizes extension methods into **extension members** — extension
properties, static members, and operators — declared in an `extension` block
that names the receiver once. This lets you build F#-style "modules of functions"
over types you don't own, and add computed views without subclassing:

```csharp
public static class EnumerableExtensions
{
    extension<T>(IEnumerable<T> source)          // receiver named once
    {
        public bool IsEmpty => !source.Any();              // extension property
        public T? SecondOrDefault => source.Skip(1).FirstOrDefault();
        public IEnumerable<T> Intersperse(T sep)           // extension method
        {
            // ...
        }
    }

    extension(string s)
    {
        public bool IsBlank => string.IsNullOrWhiteSpace(s);
        public string Truncate(int n) => s.Length <= n ? s : s[..n];
    }
}

bool none = items.IsEmpty;          // reads like a real member
string t   = name.Truncate(10);
```

Why it matters functionally: behavior lives in **static functions over data**
(not methods baked into mutable classes), you can grow a fluent pipeline
vocabulary (`source.IsEmpty`, `xs.Intersperse(...)`), and you keep types as plain
records while attaching operations alongside. Static and operator extension
members let you add factory-style members and lifted operators to existing types
too.

## The `field` keyword — validated properties without backing fields

`field` is a contextual keyword for the compiler-generated backing field, so you
can add logic to an accessor without declaring a private field. Pair it with
`init` for a **validated immutable property**:

```csharp
public string Name
{
    get => field;
    init => field = value is { Length: > 0 } v ? v.Trim()
                                               : throw new ArgumentException("required");
}
```

This keeps records/value objects terse while still enforcing invariants — no
separate `_name` field, no constructor ceremony.

## Null-conditional assignment

Assignment now works through `?.`, so you assign only when the target is
non-null — fewer defensive `if (x is not null)` blocks:

```csharp
order?.Note = note;          // no-op if order is null
config?.Items ??= [];        // initialize only when present and currently null
```

It complements nullable reference types (see `errors-and-nullability.md`) for
clean, total handling of "maybe absent" without imperative null guards.

## Primary constructors — keep the necessary classes lean

When you *do* need a class (a service holding injected dependencies, say), a
primary constructor captures them immutably in one line — closer to a function
closure than a field-and-constructor class:

```csharp
public class OrderService(IClock clock, IPriceList prices)
{
    public Receipt Place(Order o) => /* use clock, prices */;
}
```

Treat the captured parameters as read-only collaborators. (Records have had
primary constructors since C# 9; this is for the rare hand-written class.)

## Collection expressions & spread (use everywhere)

`[...]` with the `..` spread is the default way to build collections and to
materialize pipelines immutably (full treatment in
`pipelines-and-expressions.md`):

```csharp
IReadOnlyList<int> xs = [0, .. source.Select(f), 99];
ImmutableArray<int> ys = [.. xs];
```

## `params` collections

`params` now accepts more than arrays — `IEnumerable<T>`, `Span<T>`,
`ReadOnlySpan<T>` — so variadic helpers are allocation-friendly and pipeline-y:

```csharp
static string Join(params ReadOnlySpan<string> parts) => string.Join(", ", parts);
```

## Smaller niceties

- **Lambda parameter modifiers**: lambdas can take `ref`/`out`/`in`/`scoped`
  parameters without spelling out the full type — handy when passing lambdas to
  span/`TryParse`-style APIs.
- **`nameof` with unbound generics**: `nameof(List<>)` works, useful in
  diagnostics and source generators.
- **First-class spans**: improved implicit conversions between arrays and
  `Span<T>`/`ReadOnlySpan<T>` make zero-allocation pipelines smoother on hot paths.

## How these change your defaults

- Add behavior with **extension members over data**, not methods on stateful
  classes.
- Use **`field` + `init`** for validated, immutable properties.
- Lean on **null-conditional assignment** and NRT instead of imperative null
  guards.
- Build and pass data with **collection expressions**; keep results immutable.

None of these require classes or mutation — they make the functional path the
*shorter* path, which is exactly how you beat the OOP muscle memory.
