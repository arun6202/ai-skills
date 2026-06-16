# Pattern matching & active patterns

Pattern matching is F#'s sharpest tool — and active patterns push it *past* what
Haskell, OCaml, or Scala offer out of the box. Use it to decompose data and
branch in one move, with the compiler checking you handled every case.

## `match` basics

```fsharp
match shape with
| Circle r         -> Math.PI * r * r
| Rectangle (w, h) -> w * h
| Point            -> 0.0
```

- **Exhaustiveness is the point.** The compiler warns on a missing case, so
  adding a DU case lights up every place that must change. Don't paper over it
  with `| _ ->` unless "everything else" is genuinely one behavior.
- Patterns **bind** while they match: `Circle r` pulls out the radius. No
  separate accessor call, no chance of reading the wrong field.
- Combine cases that share a result with an or-pattern:
  `| MustNotBeNull | MustNotBeEmpty -> "required"`.

## `when` guards

Add a boolean condition to a case when the shape alone isn't enough:

```fsharp
match n with
| x when x < 0 -> "negative"
| 0            -> "zero"
| _            -> "positive"
```

Keep guards cheap and side-effect-free; if a guard gets complex, an active
pattern (below) usually reads better.

## Decompose anything

```fsharp
match value with
| (a, b)                      -> ...          // tuples
| [ single ]                  -> ...          // a one-element list
| first :: rest               -> ...          // head/tail
| [| x; y; z |]               -> ...          // a three-element array
| { Name = n; Age = a }       -> ...          // records (by field)
| Some x                      -> ...          // options
```

Decompose in the **parameter position** when there's a single shape, skipping the
`match` entirely (Listing 6-11):

```fsharp
let dist (x1, y1) (x2, y2) = sqrt ((x2 - x1) ** 2.0 + (y2 - y1) ** 2.0)
```

## Pattern match on type / null at boundaries

```fsharp
match (person : Person) with
| :? Child as c -> $"Child of {c.ParentName}"   // type test + bind (Listing 6-31)
| _             -> person.Name

match stringFromOutside with
| null -> "(none)"                               // only at .NET boundaries (6-33)
| s    -> s.ToUpper()
```

Type tests belong at interop edges; inside your own code, model the variants as a
DU instead of downcasting.

## Active patterns — extend matching itself

Active patterns let you match against *computed* views of a value, not just its
literal structure. They turn "transform then test" into a name you can pattern on.

### Single-case — transform on the way in

```fsharp
let (|Currency|) (x : float) = Math.Round(x, 2)     // Listing 6-25

match 100.0 / 3.0 with
| Currency 33.33 -> true                            // rounds, then matches
| _ -> false

let add (Currency a) (Currency b) = a + b           // also works in parameters
```

### Multi-case — classify into a closed set

```fsharp
let (|Mitsubishi|Samsung|Other|) (s : string) =     // Listing 6-27
    match s.Substring(0, 3) with
    | "MWT" -> Mitsubishi
    | "SWT" -> Samsung
    | _     -> Other

match turbine with
| Mitsubishi -> "Mitsubishi"
| Samsung    -> "Samsung"
| Other      -> "unknown"
```

### Partial `(|Name|_|)` — "matches, or doesn't"

Returns `option`; ideal for validation/parse-style tests and pairs perfectly with
`List.choose` (Listings 6-28, 6-29):

```fsharp
let (|Int|_|) (s : string) =
    match Int32.TryParse s with
    | true, n -> Some n
    | _       -> None

match token with
| Int n -> $"number {n}"
| _     -> "not a number"
```

### Parameterized — pass arguments to the pattern

```fsharp
let (|Regex|_|) pattern s =                          // Listing 6-29
    let m = Regex.Match(s, pattern)
    if m.Success then Some s else None

zipCodes |> List.choose (fun (Regex @"^\d{5}$" z) -> z)
```

### Combine with `&`

Require several patterns of the *same* value at once (Listing 6-30):

```fsharp
match postcode with
| PostCode (Some p) & OuterLondon (Some area) -> $"promo in {area}"
| PostCode (Some p)                            -> "no promo here"
| _                                            -> "invalid postcode"
```

## When to use which

- Reach for **active patterns** when match arms repeat the same parse/round/regex
  work, or when the meaningful distinction is computed rather than structural.
  They give your `match` a domain vocabulary (`Int`, `Mitsubishi`, `Regex`).
- Keep them **pure and cheap** — a pattern that does I/O or heavy work surprises
  the reader, who expects matching to be free.
- Prefer a **partial** pattern for yes/no tests, a **multi-case** for a small
  closed classification, and a **single-case** purely to normalize input.
- Don't over-abstract: if a plain `match` is already clear, leave it.

## Anti-patterns

- Reaching into an `Option`/DU with `.Value`/`.IsSome` instead of matching
  (Listing 3-13) — it throws and skips exhaustiveness.
- A `| _ -> ...` that hides cases you should handle — it silences the very
  warning that protects you when the type grows.
- Deeply nested `match` where an active pattern or a `&`/or-pattern would
  flatten it.
