# Functions & composition

Functions are values. Build behavior by partially applying and composing small
functions rather than writing big ones — the parts are testable, nameable, and
recombinable. (*Stylish F# 6*, ch. 9.)

## Currying & partial application

F# functions are curried: `let add a b = a + b` has type `int -> int -> int`,
i.e. "give me an `a`, get back a function awaiting `b`." Supplying some arguments
returns a specialized function — for free, no lambda needed:

```fsharp
let add a b = a + b
let increment = add 1            // int -> int                  (Listing 9-3)

let between lo hi x = x >= lo && x <= hi
let isPercent = between 0 100    // reusable predicate
```

Design for this: **put the "configuration" arguments first and the "data"
argument last.** Then `data |> myFunc config` reads naturally and `myFunc config`
is a ready-made pipeline stage. This single convention is why the F# standard
library pipes so cleanly (`List.map f`, `List.filter pred`).

### Curried vs tupled

- **Curried** (`f a b`) — the F# default; enables partial application and piping.
  Use it for your own functions.
- **Tupled** (`f (a, b)`) — arguments arrive together as a tuple. Use it for
  .NET interop and when arguments are genuinely a single unit (Listings 9-5,
  9-8). Tupled args can't be partially applied.

## Composition `>>`

`>>` glues functions end to end: `(f >> g) x = g (f x)`. Where `|>` flows a
*value*, `>>` builds a new *function* from pieces:

```fsharp
let normalize = Seq.map Char.ToLower >> Seq.filter Char.IsLetter >> String.Concat
let result = normalize input
```

`<<` composes right-to-left (`g << f`); prefer `>>` so reading order matches
execution order. Composition is exactly what makes the railway pipeline in
`errors-and-effects.md` read as a straight line.

## Point-free style — and when to stop

Eta reduction removes an argument that's just passed straight through:

```fsharp
let printAll items = items |> List.iter (printfn "%A")   // explicit
let printAll = List.iter (printfn "%A")                  // point-free (Listing 9-17)
```

Point-free is elegant *when it removes noise without removing meaning*. Stop when:

- the dropped name was documenting what the argument *is*,
- inference gets confused (a value restriction error often means: add the arg
  back), or
- a reader would have to mentally re-add the argument to follow it.

Clarity wins over cleverness. A named argument is not a failure.

## Higher-order functions & closures

Pass functions in to parameterize behavior; return functions to capture state.
A closure can hide mutable or expensive state behind a clean signature:

```fsharp
let makeCounter () =                                     // Listing 9-12
    let mutable n = 0
    fun () -> n <- n + 1; n

let next = makeCounter ()
next (), next ()    // 1, 2  — the mutable n is encapsulated, never exposed
```

This is the functional alternative to a small stateful class: the state is
unreachable except through the returned function.

## `inline` & generic numeric code

`inline` copies a function's body at each call site, which lets it work over *any*
type that supports the operators it uses (statically-resolved type parameters) —
F#'s answer to Haskell-style numeric type classes — and removes call overhead on
hot paths (Listing 5-2 exercise; ch. 12):

```fsharp
let inline square x = x * x      // works for int, float, decimal, …
```

Use it for small generic-math helpers and measured hot paths; don't `inline`
large functions (it bloats code) or anything you want to mock/override.

## Custom operators — sparingly

You *can* define operators (`let (.+.) a b = …`), and a private local one can
remove real noise — e.g. a private `~~` for `float` to de-clutter mixed
int/float arithmetic (Listing 2-13). But operators are write-once / read-many:
an unfamiliar symbol costs every future reader. Reserve them for a small, well-
known vocabulary (or established ones like `>=>`); otherwise prefer a named
function.

## Writing your own computation expression

When you have a recurring "wrap / chain / unwrap" pattern (a custom result type,
a parser, a builder), give it a CE so callers write linear `let!` code. A builder
is just a class exposing `Bind`, `Return`, and friends:

```fsharp
type OptionBuilder() =
    member _.Bind(x, f)  = Option.bind f x
    member _.Return(x)   = Some x
    member _.ReturnFrom(x) = x
let option = OptionBuilder()

let tryArea shape = option {
    let! r = tryRadius shape       // bails to None on the first None
    return Math.PI * r * r
}
```

Implement only the members your CE needs (`Bind`/`Return` cover most;
`Zero`/`Combine`/`Delay`/`For`/`Using` enable control-flow and `use!`). This is
how `seq`, `async`, `task`, and `result` are built — the mechanism is open to
you. Don't build one where plain `bind`/`map` composition is already clear; reach
for it when the linear form genuinely reads better.
