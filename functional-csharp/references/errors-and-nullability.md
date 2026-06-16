# Errors & nullability

Make "absent" and "failed" into values the type system tracks, instead of `null`
surprises and exceptions thrown for ordinary outcomes. C# gives you nullable
reference types for absence and `Result`/`Option` types for failure; reserve
exceptions for the genuinely exceptional, at the boundary.

## Nullable reference types are your first `Option`

Turn them on everywhere (`<Nullable>enable</Nullable>` in the .csproj) and let the
compiler track absence through the flow analysis:

```csharp
#nullable enable

Customer? Find(int id);        // the ? says "may be absent" — in the type

if (Find(id) is { } customer)  // pattern: not-null, bound to `customer`
    Use(customer);             // here `customer` is non-null, guaranteed
```

- `T?` on reference types is a compile-time annotation: the compiler warns when
  you might dereference null. Treat warnings as errors.
- Prefer pattern checks (`is { } x`, `is null`, `is not null`) and the
  null-coalescing operators (`??`, `??=`) over manual `!= null` ladders.
- Avoid the null-forgiving `!` operator — it silences the very check that
  protects you. Use it only when you can prove the compiler wrong.

For simple "maybe a value" cases, `T?` is enough and idiomatic. Reach for a real
`Option<T>` when you want to **chain** operations (`Map`/`Bind`) or when `null`
can't express intent (e.g. distinguishing "absent" from "present but null").

## `Option<T>` — explicit, chainable absence

A minimal stop-gap (or use `LanguageInt`/`LanguageExt`'s `Option<T>`):

```csharp
public abstract record Option<T>
{
    public sealed record Some(T Value) : Option<T>;
    public sealed record None : Option<T>;

    public Option<TOut> Map<TOut>(Func<T, TOut> f) => this switch
    {
        Some s => new Option<TOut>.Some(f(s.Value)),
        _      => new Option<TOut>.None(),
    };

    public Option<TOut> Bind<TOut>(Func<T, Option<TOut>> f) => this switch
    {
        Some s => f(s.Value),
        _      => new Option<TOut>.None(),
    };

    public T DefaultValue(T fallback) => this is Some s ? s.Value : fallback;
}
```

## `Result<T,E>` — succeeded, or failed with a reason

When callers need to know *why* something failed, return a `Result`, not a thrown
exception. Model the error as a type (often a DU — see
`discriminated-unions.md`), not a bare string:

```csharp
public abstract record Result<T, E>
{
    public sealed record Ok(T Value) : Result<T, E>;
    public sealed record Error(E Err) : Result<T, E>;
}

public static class Result
{
    public static Result<TOut, E> Map<T, TOut, E>(
        this Result<T, E> r, Func<T, TOut> f) => r switch
    {
        Result<T, E>.Ok ok => new Result<TOut, E>.Ok(f(ok.Value)),
        Result<T, E>.Error e => new Result<TOut, E>.Error(e.Err),
        _ => throw new UnreachableException(),
    };

    public static Result<TOut, E> Bind<T, TOut, E>(
        this Result<T, E> r, Func<T, Result<TOut, E>> f) => r switch
    {
        Result<T, E>.Ok ok => f(ok.Value),
        Result<T, E>.Error e => new Result<TOut, E>.Error(e.Err),
        _ => throw new UnreachableException(),
    };
}
```

## Railway-oriented programming in C#

With `Map` (apply a never-fails step) and `Bind` (chain a might-fail step) as
extension methods, a validation/processing pipeline reads as a straight line that
short-circuits on the first error — the same railway as the F# skills:

```csharp
Result<Receipt, OrderError> PlaceOrder(UnvalidatedOrder input) =>
    Validate(input)            // Result<ValidatedOrder, OrderError>
        .Bind(Price)           // Result<PricedOrder, OrderError>
        .Bind(Charge)          // Result<PaidOrder, OrderError>
        .Map(MakeReceipt);     // Result<Receipt, OrderError>
```

Consume at the edge with an exhaustive `Match`/`switch`, turning the two tracks
into one output (e.g. an HTTP response):

```csharp
IResult ToHttp(Result<Receipt, OrderError> r) => r switch
{
    Result<Receipt, OrderError>.Ok ok   => Results.Ok(ok.Value),
    Result<Receipt, OrderError>.Error e => Results.BadRequest(Describe(e.Err)),
    _ => throw new UnreachableException(),
};
```

## Don't hand-roll if a library fits

Mature libraries give you battle-tested `Option`/`Result`, `Map`/`Bind`, and
async overloads — prefer them over reinventing the monad:

- **[`ErrorOr`](https://github.com/amantinband/error-or)** — lightweight
  `ErrorOr<T>` with `Then`/`Match`; great default for result-or-error returns.
- **[`CSharpFunctionalExtensions`](https://github.com/vkhorikov/CSharpFunctionalExtensions)**
  — `Result`, `Maybe<T>`, railway helpers; DDD-friendly.
- **[`LanguageExt`](https://github.com/louthy/language-ext)** — a full FP library
  (Option, Either, Validation, immutable collections, higher-kinded emulation).
  Powerful; adopt deliberately — it's a large surface and a distinct dialect.
- **OneOf** — for the union side (see `discriminated-unions.md`).

## Exceptions: only at the edges

Exceptions are for the genuinely exceptional and for interop — not control flow.
Catch them at the boundary and convert to a `Result` so the core stays total:

```csharp
static Result<string, IoError> ReadAll(string path)
{
    try { return new Result<string, IoError>.Ok(File.ReadAllText(path)); }
    catch (IOException ex) { return new Result<string, IoError>.Error(new IoError(ex)); }
}
```

Throw (rather than return `Error`) only for programmer mistakes / broken
invariants that should crash loudly — e.g. an unreachable switch arm or an
argument that violates a precondition.

## Rules of thumb

- `T?` for simple absence; `Option<T>` when you need to chain or disambiguate.
- `Result<T,E>` with a typed error for expected failure; exceptions only at the
  boundary.
- Treat nullable warnings as errors; avoid `!`.
- Compose with `Map`/`Bind`; collapse to a value with an exhaustive `Match` at the
  edge.
