# Records & immutability

Records are C#'s functional product type: concise, immutable by default, with
value equality and non-destructive update built in. Reach for a `record` first;
fall back to a `class` only when you need reference identity or encapsulated
mutable state.

## Records in one screen

```csharp
// Positional record: the idiomatic "data bundle". Immutable, value-equal.
public record Customer(string Name, EmailAddress Email, DateOnly Since);

var c1 = new Customer("Ada", email, today);
var c2 = c1 with { Name = "Ada L." };   // non-destructive update -> a new record
bool same = c1 == c2;                    // value equality: false (Name differs)
```

That single line gives you: an immutable type, a constructor, `Name`/`Email`/
`Since` properties, value-based `Equals`/`GetHashCode`, a readable `ToString()`,
and `Deconstruct` for positional patterns. The class equivalent is ~40 lines of
boilerplate you should never hand-write again.

## record class vs record struct

- **`record` (class)** — reference type, heap-allocated, value equality. The
  default for domain data.
- **`record struct`** — value type, stack/inline, value equality. Use for small,
  short-lived values to avoid allocation. Make it **`readonly record struct`** so
  it's truly immutable:
  ```csharp
  public readonly record struct Point(double X, double Y);
  ```

## Three ways to declare; pick by shape

```csharp
// 1. Positional — terse, ideal for pure data
public record Money(decimal Amount, string Currency);

// 2. Init-only properties — when you want named initialization / docs per member
public record Order
{
    public required OrderId Id { get; init; }      // must be set at creation
    public required Customer Customer { get; init; }
    public IReadOnlyList<OrderLine> Lines { get; init; } = [];   // sane default
}

// 3. Mix — positional plus extra init members
public record Invoice(InvoiceId Id)
{
    public DateOnly Due { get; init; }
}
```

- **`init`** accessors allow object-initializer syntax at creation, then lock the
  property — immutability without a giant constructor.
- **`required`** forces the caller to set a member (compile error otherwise),
  giving you "no half-built objects" without writing a validating constructor.
  Combine `required` + `init` for mandatory-but-immutable.

## `with` is your "change" operator

Never mutate — produce a new value with the changes:

```csharp
var shipped = order with { Status = OrderStatus.Shipped, ShippedOn = today };
```

`with` does a shallow copy then applies the overrides. It's cheap and the
functional substitute for setters and the builder pattern.

## Validate on construction without losing terseness

Records can still enforce invariants. Put validation in the body or, better, wrap
constrained primitives in their own small types (see
`discriminated-unions.md` and the F# `functional-domain-modeling` skill's
constrained-types pattern):

```csharp
public record Temperature
{
    public double Celsius { get; }
    public Temperature(double celsius) =>
        Celsius = celsius >= -273.15
            ? celsius
            : throw new ArgumentOutOfRangeException(nameof(celsius));
}
```

For a value object you'll create from untrusted input, prefer a static factory
returning `Result`/`Option` over a throwing constructor (see
`errors-and-nullability.md`).

## Immutable collections

A record is only as immutable as its fields. A `List<T>` property is a mutation
hole. Default to read-only / immutable collections:

- **Expose** `IReadOnlyList<T>` / `IReadOnlyDictionary<K,V>` on records.
- **Build** with collection expressions and LINQ, materializing once:
  ```csharp
  IReadOnlyList<int> doubled = [.. source.Select(x => x * 2)];
  ```
- **For shared mutable-looking state**, use `System.Collections.Immutable`
  (`ImmutableArray<T>`, `ImmutableList<T>`) whose "mutators" return new instances:
  ```csharp
  ImmutableList<string> next = names.Add("Grace");   // names is unchanged
  ```

## equality nuance: collections break value equality

Record value equality compares fields with `==`/`EqualityComparer`. A record
containing a `List<T>`/array compares those **by reference**, so two records with
equal contents may be "unequal". Fixes: use `ImmutableArray<T>` with a value
comparer, expose `IReadOnlyList<T>` backed by immutable storage, or override
equality deliberately. Easiest rule: **don't put mutable collections in records.**

## When a class is the right call

Choose `class` when you need:
- **Reference identity** — two entities are "the same" by id, not by content
  (though often better modeled as a record with an `Id` and equality on `Id`).
- **Encapsulated mutable state with invariants** — e.g. a buffer/cache whose
  mutation is the point and must stay consistent.
- **A framework base type / inheritance contract** you must implement.

Even then, keep the surface small, prefer `readonly` fields, and expose behavior
through methods rather than public setters.
