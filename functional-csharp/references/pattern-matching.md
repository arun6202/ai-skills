# Pattern matching

Pattern matching is how functional C# branches and decomposes. It replaces
chains of `if`/`is`/cast, the visitor pattern, and most virtual dispatch with a
single readable expression that returns a value.

## `switch` expressions, not `switch` statements

The `switch` *expression* returns a value, so it composes and assigns directly —
prefer it over the statement form and over `if`/`else if` ladders:

```csharp
string Classify(int n) => n switch
{
    < 0      => "negative",
    0        => "zero",
    < 100    => "small",
    _        => "large",
};
```

Each arm is `pattern => expression`. The `_` is the discard (catch-all). Keep
arms as expressions; if one needs work, call a local function rather than
breaking out of the expression.

## The pattern toolbox

```csharp
result switch
{
    // Type pattern (+ binding)
    Approved a            => $"ok {a.AuthCode}",

    // Property pattern — match on members, nest freely
    Declined { Reason: "insufficient_funds" } => "no funds",
    Declined { Reason.Length: > 100 }         => "long reason",

    // Positional pattern — deconstruct a record/tuple
    Failed(var ex)        => ex.Message,

    // Relational + logical patterns: and / or / not
    Approved { Amount: >= 1000 and < 5000 } => "mid",
    not Failed            => "handled",

    _ => "??",
};
```

- **Type pattern**: `Circle c` — matches and binds.
- **Property pattern**: `{ Status: Shipped, Lines.Count: > 0 }` — match nested
  members, including length/count; no casting.
- **Positional pattern**: `Point(0, var y)` — deconstruct via `Deconstruct`
  (records get it free).
- **Relational**: `< 0`, `>= 100`. **Logical**: `and`, `or`, `not`.
- **`var` pattern**: `var x` — always matches and binds (useful to capture a
  computed value with a `when` guard).
- **Constant / null**: `0`, `"yes"`, `null`, `not null`.

## List patterns

Match the shape of a sequence (arrays, spans, lists):

```csharp
int[] xs = [1, 2, 3];
string shape = xs switch
{
    []            => "empty",
    [var only]    => $"one: {only}",
    [var first, .., var last] => $"{first}..{last}",   // slice with ..
    [1, 2, ..]    => "starts 1,2",
    _             => "other",
};
```

## `when` guards for conditions a pattern can't express

```csharp
order switch
{
    { Total: var t } when t > budget => "over budget",
    { Lines.Count: 0 }               => "empty order",
    _                                => "ok",
};
```

Keep guards cheap and side-effect free.

## Tuples: branch on several values at once

A clean state-machine / decision-table style:

```csharp
(state, evt) switch
{
    (Idle,    Start) => Running,
    (Running, Pause) => Paused,
    (Paused,  Start) => Running,
    (_,       Stop)  => Idle,
    _ => state,
};
```

## Exhaustiveness — the one caveat (until `union`)

A `switch` expression that doesn't cover all inputs throws
`SwitchExpressionException` at runtime. For a closed model you control, make the
intent explicit and fail loudly on a forgotten case:

```csharp
_ => throw new UnreachableException(),   // System.Diagnostics
```

Today the compiler does **not** force you to handle every subtype of an abstract
record — that exhaustiveness check is exactly what the upcoming `union` keyword
adds (see `discriminated-unions.md`). Until then: model cases as `sealed` records,
keep one `switch` per operation, and use the `UnreachableException` arm so adding
a case surfaces fast in tests.

## Replace the visitor pattern entirely

The classic OOP visitor — an interface with a `Visit` overload per type,
`Accept` methods, double dispatch — is just a `switch` expression over patterns:

```csharp
// Instead of IShapeVisitor<T> + Accept(...) on every shape:
static double Area(Shape s) => s switch
{
    Circle(var r)        => Math.PI * r * r,
    Rectangle(var w, var h) => w * h,
    _ => throw new UnreachableException(),
};
```

Add a new operation = a new function with a `switch`, not a new method on every
class. This is the functional inversion of the expression problem, and it's
almost always what you want for closed data + open operations.

## Replace `is`-cast ladders

```csharp
// Don't:
if (x is Cat) { var c = (Cat)x; ... }
else if (x is Dog) { var d = (Dog)x; ... }

// Do:
var msg = x switch { Cat c => ..., Dog d => ..., _ => ... };
```
