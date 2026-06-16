# Discriminated unions in C#

A discriminated union (DU) models a value that is **exactly one of a fixed set of
shapes** — the single most useful functional modeling tool, and the one C# has
lacked natively. C# 15 is adding it (the `union` keyword, in preview); until then
you use stop-gaps. This file covers both, and how to write today so migration is
trivial later.

## Why you want them

DUs make illegal states unrepresentable and give you **exhaustive** handling: a
payment is `Approved | Declined | Failed` and nothing else, so a `switch` that
covers those three is complete and the compiler can warn when a fourth appears.
They replace inheritance-for-data, nullable-soup, and enum+payload hacks.

---

## Stop-gap #1: abstract record + sealed cases (no dependencies)

The idiomatic, zero-dependency DU today: a closed hierarchy of records consumed
by a `switch` expression.

```csharp
public abstract record Shape;
public sealed record Circle(double Radius)              : Shape;
public sealed record Rectangle(double Width, double Height) : Shape;
public sealed record Triangle(double Base, double Height)   : Shape;

static double Area(Shape s) => s switch
{
    Circle(var r)            => Math.PI * r * r,
    Rectangle(var w, var h)  => w * h,
    Triangle(var b, var h)   => 0.5 * b * h,
    _ => throw new UnreachableException(),   // the only "leak" — see caveat
};
```

Conventions that make this clean and migration-ready:

- **`abstract`** base so it can't be instantiated; **`sealed`** cases so the set is
  closed and nobody adds a subtype elsewhere.
- Keep the case records small and **positional** so positional patterns read well.
- Optionally nest the cases inside the base to namespace them
  (`Shape.Circle`) and signal the closed set:
  ```csharp
  public abstract record Shape
  {
      public sealed record Circle(double Radius) : Shape;
      public sealed record Rectangle(double Width, double Height) : Shape;
  }
  ```
- **One `switch` per operation**, each ending with the `UnreachableException`
  arm.

**The caveat:** the compiler does *not* force you to handle every case — exhaustiveness
is by convention + the runtime `_` arm, not a compile error. Mitigate with: a
single switch per operation, unit tests that exercise each case, and (optionally)
an analyzer. This gap is precisely what the `union` keyword closes.

---

## Stop-gap #2: OneOf (library, ergonomic Match)

[`OneOf`](https://github.com/mcintyre321/OneOf) gives a generic union with a
`Match`/`Switch` that *is* enforced — you must supply a handler for every arm,
so it's effectively exhaustive at compile time:

```csharp
// using OneOf;
public OneOf<User, NotFound, Error> FindUser(int id) => ...;

string message = FindUser(42).Match(
    user     => $"Found {user.Name}",
    notFound => "No such user",
    error    => $"Error: {error.Message}");   // miss an arm -> won't compile
```

Good for ad-hoc result-or-error returns where you don't want to declare a named
base type. Trade-off: cases are positional/anonymous (less self-documenting than
named records), and it's a dependency.

## Stop-gap #3: dunet (source generator)

[`dunet`](https://github.com/domn1995/dunet) generates the union boilerplate
(including an enforced `Match`) from a partial record marked `[Union]`:

```csharp
[Union]
public partial record Shape
{
    partial record Circle(double Radius);
    partial record Rectangle(double Width, double Height);
}

// generated Match requires all cases:
var area = shape.Match(
    circle    => Math.PI * circle.Radius * circle.Radius,
    rectangle => rectangle.Width * rectangle.Height);
```

Best of both: named cases *and* compile-time-enforced matching, no runtime
library. Trade-off: a build-time generator dependency.

### Choosing a stop-gap

- **Public domain model / many operations** → abstract record + sealed cases
  (most idiomatic, migrates cleanly to `union`).
- **Want enforced match now, named cases** → dunet.
- **One-off result/error returns** → OneOf (or a `Result`/`ErrorOr` type, see
  `errors-and-nullability.md`).

---

## The future: the `union` keyword (C# 15 / .NET 11, preview)

C# is gaining native unions. **Status: preview, available from .NET 11 Preview 2,
shipping with C# 15; the design is explicitly provisional and the syntax may
change** — do not adopt in production yet, but write today's code so the switch is
a one-line change.

**Type union over existing types** (your example):

```csharp
public record Cat(string Name);
public record Dog(string Name);
public record Bird(string Name);

public union Pet(Cat, Dog, Bird);          // a value is exactly one of these

static string Describe(Pet pet) => pet switch
{
    Cat c  => $"Cat: {c.Name}",
    Dog d  => $"Dog: {d.Name}",
    Bird b => $"Bird: {b.Name}",
    // exhaustive: covering all members needs NO discard arm
};
```

**`[Union]` attribute pattern** — existing classes/structs can opt in by
implementing the union pattern (public single-parameter constructors defining the
cases + a public `Value` property), letting libraries provide union types.

What native unions add over the stop-gaps:

- **Compiler-enforced exhaustiveness**: a `switch` covering all members needs no
  discard; adding a member produces a **compiler warning** at unhandled switches.
- **Nullability tracking**: the union integrates with NRT flow analysis;
  nullable members require a `null` arm.
- **Efficient representation**: the compiler generates a struct storing the value
  as a single `object?` (boxing value types), with implicit conversions from each
  case type so assignment is direct (`Pet p = new Cat("Tom");`).

### Write-now, migrate-later

The migration from "abstract record + sealed cases" to `union` is nearly
mechanical, because **the consumption side is identical** — both use `switch` with
the same patterns. To minimize churn later:

1. Model cases as `sealed record`s with positional members (same names you'd use
   in a `union`).
2. Centralize matching in `switch` expressions (one per operation), not scattered
   `is`/cast.
3. Keep the `_ => throw new UnreachableException()` arm; when you move to `union`,
   delete that arm and let the compiler prove exhaustiveness.

That way the abstract-record DU you write today becomes a `union` tomorrow by
swapping the declaration and dropping the discard — the `switch`es stay as they
are.
