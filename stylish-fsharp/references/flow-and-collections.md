# Flow & collections

Most "loops" are really a *map*, *filter*, *fold*, or *find* wearing imperative
clothes. Naming the operation makes intent obvious, removes the off-by-one and
forgot-to-reset-the-accumulator bugs, and composes. The rule of thumb from
*Stylish F# 6* ch. 5: **if you wrote `mutable` or `for` to build a result, there
is almost always a collection function that says it more clearly.**

## Pipelines

`|>` feeds a value into a function as its last argument, so data reads
left-to-right / top-to-bottom in the order it's transformed:

```fsharp
files
|> Seq.map File.GetLastWriteTime
|> Seq.max
```

Put each step on its own line. The shape flowing between steps is the story; if a
step's purpose is murky, bind it to a name or project into an anonymous record.

## Replace the loop

| Imperative shape                         | Idiomatic replacement                          |
|------------------------------------------|------------------------------------------------|
| accumulate into a list/array             | `Seq.map` / `Seq.collect`                      |
| `for` with an `if` that keeps some       | `Seq.filter` (or `Seq.choose` to map+filter)   |
| running total / fold state               | `Seq.fold` (or `Seq.sum`/`sumBy`, `average`)   |
| find the first match                     | `Seq.find` / `Seq.tryFind`                     |
| max/min, possibly by a key               | `Seq.max` / `Seq.maxBy` (+ the `try` variants) |
| side effect per item                     | `Seq.iter`                                     |
| split into yes/no groups                 | `List.partition` / `List.groupBy`              |

```fsharp
// Mutable linear search (Listing 5-6) collapses to:
let tryFindFirstWithGrade grade students =
    students |> Seq.tryFind (fun s -> s.Grade = grade)      // Listing 5-7

// Mutable cumulative product (Listing 5-21) collapses to:
let product s = s |> Seq.fold (fun acc x -> acc * x) 1.0    // Listing 5-22

// Mutable RMS (Listing 5-19) collapses to:
let rms s = s |> Seq.averageBy (fun x -> x ** 2.0) |> sqrt  // Listing 5-20
```

### `choose` = map + keep the `Some`s

When a transform can fail per item, return `Option` and `choose` away the misses
in one pass — cleaner than `map` then `filter` then unwrap (Listing 4-17):

```fsharp
rows
|> Array.choose (fun r ->
    match Int32.TryParse r with
    | true, n -> Some n
    | _       -> None)
```

### `fold` and `scan`

`fold` reduces a sequence to a single value with an accumulator; `scan` is `fold`
that emits every intermediate accumulator (a running tally). Reach for `fold`
only when no specialized function (`sum`, `max`, `countBy`, …) already expresses
the intent — the named one is clearer.

### Keep lambdas short

A pipeline stays readable when each lambda is a glance. If a lambda grows past a
line or two, lift it to a named `let` function and reference it — possibly
point-free (Listing 4-18). `Seq.iter printGradeLabel` beats
`Seq.iter (fun s -> printGradeLabel s)`.

## Total functions: `tryX` returns `Option`

A lookup/aggregation that can have "no answer" should say so in its type, not
throw and not return a sentinel. `Seq.max` throws on empty; define/​use the
total form (Listings 5-3, 5-16):

```fsharp
module Seq =
    let tryMax s = if Seq.isEmpty s then None else s |> Seq.max |> Some
```

The standard library already gives you `tryHead`, `tryFind`, `tryItem`,
`tryPick`, `tryExactlyOne`, etc. Prefer them; the caller then `match`es or pipes
through `Option.defaultValue`. See `errors-and-effects.md`.

## Recursion

When a problem is genuinely recursive (trees, "repeat until"), write a recursive
function — but make it **tail-recursive** so it compiles to a loop and won't blow
the stack. The idiom is an inner `rec` helper carrying an accumulator:

```fsharp
let sum xs =
    let rec loop acc = function
        | []      -> acc
        | x :: tl -> loop (acc + x) tl     // tail call: nothing happens after it
    loop 0 xs
```

For "keep going until the source dries up", a **recursive `seq` generator** is
the immutable answer to a `while` loop (Listing 5-14):

```fsharp
let rec apiToSeq () =
    seq {
        match tryGetFromApi () |> Option.ofObj with
        | Some thing -> yield thing
                        yield! apiToSeq ()
        | None       -> ()
    }
```

`yield` emits one; `yield!` splices in another sequence.

## `seq` vs `list` vs `array`

- **`list`** (`[1; 2; 3]`) — the default immutable collection. Singly-linked:
  O(1) prepend (`x :: xs`) and head/tail, great for recursion and pattern
  matching; O(n) index and append. Most domain code wants lists.
- **`array`** (`[|1; 2; 3|]`) — contiguous, mutable, O(1) indexed access, cache
  friendly. Use for numeric/hot-path work and interop; prefer not to mutate it.
- **`seq`** (`IEnumerable<'T>`) — lazy and possibly infinite; nothing computes
  until enumerated. Use for pipelines over large/streamed/expensive sources so
  you don't materialize intermediates. Note it re-evaluates on each iteration
  unless cached, and `.NET` renders `None` oddly in notebooks.

All three share the same function names (`List.map`, `Array.map`, `Seq.map`), so
the pipeline style is identical; pick the collection by its cost profile, not by
habit. Convert at the end with `Seq.toList`/`Seq.toArray` when you need to
materialize.

## Don't fear local mutation — but contain it

Immutability is the default, not a religion. A `mutable` or array buffer inside a
function, never escaping it, is fine when profiling shows a real hot path
(`objects-async-perf.md`). The contract that matters is that the function is
*observably* pure: same input, same output, no shared state mutated.
