# Domain modeling

The F# payoff: **the type system carries the rules.** Spend your design effort
making illegal states unrepresentable, and large classes of bugs simply cannot
be written. Types are the cheapest, most durable documentation you have.

## Discriminated unions — "one of these"

A DU models a value that is exactly one of a fixed set of shapes. Each case may
carry its own data. This is F#'s algebraic-data-type and the workhorse of domain
modeling.

```fsharp
type Shape =
    | Circle of radius : float
    | Rectangle of width : float * height : float
    | Point

let area =
    function
    | Circle r          -> System.Math.PI * r * r
    | Rectangle (w, h)  -> w * h
    | Point             -> 0.0
```

Name the payloads (`radius : float`) — it documents intent and lets consumers
pattern-match by name. Consume a DU with `match`; the compiler warns if you miss
a case, so adding a case surfaces every site that must change. That exhaustiveness
is the feature — don't defeat it with a catch-all `| _ ->` unless the case really
is "everything else".

### Model "states", not "flags"

Replace boolean/nullable combinations that have illegal permutations with a DU
whose cases *are* the legal states:

```fsharp
// Don't: { IsCollection : bool; DeliveryAddress : Address option } — illegal combos exist
type Fulfilment =
    | Collect
    | Deliver of Address
```

Now "delivery with no address" cannot be constructed. (*Stylish F# 6*, Listings
3-15, 3-16.)

## Records — "a bundle of named values"

```fsharp
type Customer =
    { Name  : string
      Email : Email
      Since : System.DateOnly }
```

- **Immutable and structurally equal** by default: two records with equal fields
  are equal, and they hash/compare by content (Listings 7-10, 7-11). This is
  usually what you want — and a reason to prefer records over classes.
- **Copy-and-update** to "change" a field without mutation:
  ```fsharp
  let renamed = { customer with Name = "New Name" }
  ```
  (Listing 7-6.) This is cheap and the idiomatic way to evolve immutable state.
- Field equality is only as good as the field *types*. If a field is a class with
  reference equality, your record inherits that surprise (Listing 7-11) — prefer
  fields that are themselves records/DUs/primitives.
- `[<Struct>]` records live on the stack and avoid allocation for small,
  short-lived values — but struct mutation requires a `mutable` *instance*
  (Listings 7-13, 7-14). Reach for it only when profiling says so.

### Anonymous records — throwaway shapes

For an intermediate or one-off shape you don't want to name, use `{| … |}`:

```fsharp
let summary =
    orders
    |> List.map (fun o -> {| o.Id; Total = o.Lines |> List.sumBy (_.Amount) |})
```

They're structurally typed (same field names+types ⇒ same type), great for
clarifying pipeline intermediates and shaping JSON, and they support
copy-and-update — but you **cannot pattern-match** on them (Listings 4-19, 7-22,
7-24, 7-33). Promote to a named record once a shape is used in more than one
place.

## Single-case DUs — primitives with rules

A bare `string` for an email, a bare `int` for an age, invites mixing them up and
skipping validation. Wrap them, hide the constructor, and offer a smart
constructor that is the *only* way in:

```fsharp
type Email =
    private Email of string

module Email =
    let tryCreate (s : string) : Result<Email, string> =
        if System.String.IsNullOrWhiteSpace s then Error "email required"
        elif not (s.Contains "@")              then Error $"'{s}' is not an email"
        else Ok (Email (s.Trim()))

    let value (Email e) = e          // pattern-match the payload in the parameter
```

- `private` on the constructor means code outside the module can hold an `Email`
  but can never fabricate an invalid one (Listings 2-7, 2-10).
- Pattern-match the payload directly in a parameter — `let value (Email e) = e`
  — instead of a `match` with one case (Listings 2-12, 6-14).
- This is "parse, don't validate": after `tryCreate`, every downstream function
  takes `Email` and needs no re-checking.

Pair the type with a **module of the same name** so the type and its operations
travel together and read as `Email.tryCreate`, `Email.value` (Listing 2-9). Put
the `type` and `module` at the same scope (the compiler allows the shared name).

## Units of measure — typed numbers

F# can attach physical units to numerics, checked at compile time and erased at
runtime (zero cost). This catches the Mars-Climate-Orbiter class of bug that
Haskell/OCaml need libraries for:

```fsharp
[<Measure>] type m
[<Measure>] type s

let distance = 100.0<m>
let time     = 9.58<s>
let speed    = distance / time        // float<m/s>; m + s wouldn't compile
```

Use them for domains thick with quantities (engineering, finance, science). They
compose (`m/s`, `m^2`) and disappear from the compiled output.

## Recursive and generic types

- DUs and records may be **recursive** for trees/graphs; use `and` to define
  mutually-recursive types together (Listings 7-17, 7-18).
- Make types **generic** when the logic is shape-agnostic (`type Tree<'T> = …`);
  pin the parameter only where a concrete type is required (Listings 7-15, 7-16).

## Checklist

- [ ] Can an illegal value be constructed? If yes, push the rule into the type.
- [ ] `Option` for "maybe absent", DU cases for "one of these states" — no `null`,
      no sentinel values, no `isValid` booleans riding alongside the data.
- [ ] Validated primitives are single-case DUs with `private` constructors.
- [ ] Records for product types, DUs for sum types; reach for a class only when a
      reason in `objects-async-perf.md` applies.
- [ ] Each domain type travels with a same-named module of functions.

## Scaling this up

This file covers type *mechanics* in the small. When you're modeling a whole
domain, bounded context, or business workflow — systematic constrained types via
a shared `ConstrainedType` helper, workflows-as-typed-functions, states-as-types
lifecycles, and DTO boundaries — switch to the **`functional-domain-modeling`**
skill, which applies these same primitives at application scale.
