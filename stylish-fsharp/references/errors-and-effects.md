# Errors & effects

Make absence and failure *values* the type system tracks, not surprises thrown at
runtime. The two tools are `Option` (maybe absent) and `Result` (succeeded, or
failed with a reason), and the discipline that strings them together is
railway-oriented programming.

## `Option<'T>` — maybe absent

`Some x | None`. Use it for any value that might legitimately not be there. Never
introduce `null` into your own types (Listings 3-6, 3-15).

Don't reach inside with `.IsSome`/`.Value` (Listing 3-13) — that throws and
defeats the point. Instead transform with the combinators, or `match`:

```fsharp
config
|> Map.tryFind "timeout"        // 'a option
|> Option.map int               // apply only if present       (Listing 3-11)
|> Option.defaultValue 30       // supply a fallback            (Listing 3-8/3-9)

// chain might-fail steps; the first None short-circuits
user
|> tryGetAccount                // User    -> Account option
|> Option.bind tryGetBalance    // Account -> Balance option    (Listing 3-12)
```

| Combinator             | Use it to…                                            |
|------------------------|-------------------------------------------------------|
| `Option.map`           | apply a function to the value if present              |
| `Option.bind`          | chain another might-fail (`'a -> 'b option`) step     |
| `Option.iter`          | run a side effect only when present (Listing 3-10)    |
| `Option.defaultValue`  | collapse to a plain value with a fallback             |
| `Option.filter`        | keep `Some` only if a predicate holds                 |
| `Option.orElse`        | try an alternative `option` when `None`               |

`Option.ofObj` / `ofNullable` convert at .NET boundaries; `ValueOption`
(`ValueSome`/`ValueNone`) is the struct form for hot paths (Listings 3-19, 3-25).

## `Result<'T,'TError>` — succeeded or failed-with-reason

`Ok x | Error e`. Use it when callers need to know *why* something failed, not
just that a value is missing. Make the error a **domain DU**, not a bare string,
so callers can branch and you can localize messages at the edge:

```fsharp
type ValidationError =                              // Listing 11-12
    | MustNotBeEmpty
    | MustContainMixedCase
    | MustContainOne of chars : string
    | ErrorSaving    of exn : exn
```

## Railway-oriented programming

Model each step as `'a -> Result<'b, 'error>`. Two "rails" run side by side: a
success track and a failure track. `Result.bind` stays on the success rail and
*switches to failure on the first `Error`*, carrying it untouched to the end —
so the happy path reads as a straight line and errors are handled once.

```fsharp
open Result        // bind, map, mapError

// Compose the steps with >> into one function; no nested matches.   (Listing 11-13)
let validateAndSave : string -> Result<unit, ValidationError> =
    notEmpty
    >> bind mixedCase
    >> bind (containsAny "-_!?")
    >> map  tidy            // map: a plain 'a -> 'b step that can't fail
    >> bind save
```

- **`map`** lifts a never-fails step (`'a -> 'b`) onto the rail.
- **`bind`** lifts a might-fail step (`'a -> Result<'b,_>`); use it to add a
  switch where the track can diverge to failure.
- **`mapError`** transforms the failure value — translate internal errors to
  user-facing messages at the boundary (Listing 11-13), keeping inner steps
  ignorant of presentation.

Collect outcomes over a collection by mapping the pipeline and then `choose`-ing
the successes, or partition `Ok`/`Error` to report both (Exercise 11-2):

```fsharp
data
|> Array.map processMessage          // -> Result<Reading, MessageError>[]
|> Array.choose (function Ok r -> Some r | Error _ -> None)
```

### `Option` vs `Result` — which?

- "Absent is normal, no explanation needed" (a cache miss, an optional field) →
  **`Option`**.
- "Failure needs a reason the caller acts on" (validation, parsing, I/O) →
  **`Result`** with an error DU.
- Convert with `Option.toResult`-style helpers or
  `match opt with Some x -> Ok x | None -> Error e` at the seam.

## Exceptions — only at the edges

Exceptions are for the genuinely exceptional and for .NET interop, not for
control flow. Catch them at the boundary and convert to a `Result` so the rest of
your code stays total (Listing 11-12):

```fsharp
let save s =
    try  dbSave s |> Ok
    with e -> Error (ErrorSaving e)
```

Raise (rather than return `Error`) only for programmer mistakes / invariant
violations that should crash loudly — e.g. an `ArgumentOutOfRangeException` in a
smart constructor guarding an impossible input (Listing 2-3).

## Computation expressions — flatten the rails

When `bind`/`map` chains get noisy, a computation expression lets you write the
happy path linearly with `let!` doing the binding and short-circuiting under the
hood. Built-in: `seq { }`, `async { }`, `task { }`. For `option`/`result`, F# 6
ships them via `FSharp.Core` (or use the popular `FsToolkit.ErrorHandling`):

```fsharp
let parseCustomer line = result {
    let! cols  = splitColumns line          // Result<string[], _>
    let! email = Email.tryCreate cols[1]    // unwraps Ok, bails on first Error
    return { Name = cols[0]; Email = email }
}
```

`let!`/`do!`/`return!` are the CE forms of `bind`/`bind-unit`/`return-a-wrapped`.
Use a CE when the linear form is clearly more readable than `>> bind …`; use the
point-free railway when the steps compose cleanly. Both are idiomatic — see
`functions.md` for writing your own CE.

## At application scale

For railway-oriented programming across a whole workflow — `AsyncResult`,
normalizing each step's error into one workflow error DU, `sequence`/`traverse`
over lists of results, and **applicative validation** (collect *all* errors
rather than failing fast) — see the **`functional-domain-modeling`** skill
(`references/effects-and-errors.md`).
