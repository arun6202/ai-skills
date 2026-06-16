# Pipelines & expressions

Replace loops-that-mutate with **LINQ pipelines**, and statement blocks with
**expressions**. The result reads as a description of *what* you want, computed by
composing small transformations, with no off-by-one bugs and no accumulator to
forget to reset.

## LINQ is the pipeline (C#'s `|>`)

Most `for`/`foreach` loops are a `Select` (map), `Where` (filter), or `Aggregate`
(fold) in disguise. Name the operation:

```csharp
// Imperative:
var result = new List<string>();
foreach (var o in orders)
    if (o.Total > 100)
        result.Add(o.Customer.Name);

// Pipeline:
var result = orders
    .Where(o => o.Total > 100)
    .Select(o => o.Customer.Name)
    .ToList();
```

| Loop shape                          | LINQ                                            |
|-------------------------------------|-------------------------------------------------|
| transform each item                 | `Select`                                        |
| keep some items                     | `Where`                                         |
| transform + flatten                 | `SelectMany`                                    |
| running total / reduce              | `Aggregate` (or `Sum`/`Count`/`Max`/`Average`)  |
| first match / maybe none           | `FirstOrDefault` / `First` (prefer the `OrDefault` + null check) |
| group by a key                      | `GroupBy`                                       |
| de-dup / order                      | `Distinct` / `DistinctBy` / `OrderBy`           |
| yes/no split                        | `GroupBy(predicate)` or two `Where`s            |

Prefer the specialized operator (`Sum`, `Max`, `Count`) over a hand-written
`Aggregate` — it states intent. Reach for `Aggregate` only when no named operator
fits.

## Materialize once, at the end

LINQ is **lazily evaluated**: `Where`/`Select` build a query that runs only when
enumerated. Enumerating twice re-runs the work (and can hit a database twice).
So: compose lazily, then materialize a single time with `ToList()`/`ToArray()`/a
collection expression when you need the results.

```csharp
var query = source.Where(IsActive).Select(Project);  // nothing has run yet
var list  = query.ToList();                            // runs once, here
```

Beware capturing a lazy query that closes over something that changes, and avoid
returning `IEnumerable<T>` that secretly re-queries — return `IReadOnlyList<T>`
when you've materialized.

## Expression-bodied everything

Use `=>` for members whose body is one expression — methods, properties,
constructors, local functions:

```csharp
public decimal Subtotal => Lines.Sum(l => l.Amount);
public string FullName => $"{First} {Last}";
static int Square(int x) => x * x;
```

Combined with `switch` expressions (see `pattern-matching.md`), most methods
become a single expression with no `return` statement and no mutable locals.

## Functions are values

A delegate/`Func`/`Action` is a first-class function. Pass behavior directly
instead of wrapping it in a one-method interface or a strategy class:

```csharp
// Instead of IDiscountStrategy with one method + DI registration:
decimal Total(IEnumerable<Line> lines, Func<Line, decimal> price) =>
    lines.Sum(price);

var withVat = Total(lines, l => l.Amount * 1.2m);
```

- **Higher-order functions**: take and return functions to parameterize and to
  capture state in closures.
- **Static lambdas** (`static x => ...`) prevent accidental capture (no closure
  allocation), useful in hot paths.
- **Local functions** keep a helper next to its only caller, can be recursive,
  and read better than a private method for one-off logic.

## Composition

C# has no `>>` operator, but composition is a one-liner — define it once as an
extension and pipe cleanly:

```csharp
public static Func<A, C> Then<A, B, C>(this Func<A, B> f, Func<B, C> g) => x => g(f(x));

var process = Parse.Then(Validate).Then(Normalize);   // A -> D
var output  = process(input);
```

For value pipelines, a `Pipe`/`Apply` extension reads like F#'s `|>`:

```csharp
public static TOut Pipe<TIn, TOut>(this TIn x, Func<TIn, TOut> f) => f(x);

var result = input.Pipe(Parse).Pipe(Validate).Pipe(Normalize);
```

(These tiny helpers are also in libraries; one small static class is fine too.)

## Collection expressions

Construct any collection with `[...]`, and combine with the spread `..`:

```csharp
int[]              a = [1, 2, 3];
List<int>          b = [0, .. a, 4];          // spread: 0,1,2,3,4
IReadOnlyList<int> c = [.. source.Select(f)]; // materialize a pipeline immutably
ImmutableArray<int> d = [.. a];
```

They work for arrays, `List<T>`, spans, immutable collections, and any type with
a collection builder — one syntax, target-typed. Prefer them over
`new List<int> { ... }` and `.ToList()` where the target type is known.

## Avoid mutation; thread state functionally

When you think you need a mutable accumulator, reach for `Aggregate` (fold) or a
recursive local function carrying state — keep the transformation observably pure:

```csharp
var (count, total) = items.Aggregate(
    (Count: 0, Total: 0m),
    (acc, x) => (acc.Count + 1, acc.Total + x.Amount));
```

Contained local mutation in a tight, non-escaping loop is fine for a measured hot
path — but the default, and the API surface, should be immutable.
