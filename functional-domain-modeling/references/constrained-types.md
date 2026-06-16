# Constrained (simple) types

The foundation of a type-driven domain: every primitive with a rule becomes its
own type whose **only constructor validates**. After construction the value is
provably valid, so no function downstream re-checks it. This is "parse, don't
validate" applied systematically.

## The pattern

A constrained type is a `private` single-case DU plus a same-named module giving
a `create` (returns `Result`) and a `value` (extracts the raw):

```fsharp
type String50 = private String50 of string

module String50 =
    let value (String50 s) = s
    let create fieldName s =
        ConstrainedType.createString fieldName String50 50 s   // string -> Result<String50,string>
```

- **`private`** means no code outside the module can build a `String50` except
  through `create` — invalid instances are unrepresentable.
- **`create` takes a `fieldName`** so the error message names the offending field
  (`"FirstName must not be more than 50 chars"`) — invaluable when validating a
  big record.
- **`value`** is the one-line way back out, used at boundaries (DTOs) and for
  display.

## Factor the rules into one helper module

Don't hand-write the same null/length/range/regex checks per type. DMMF
centralizes them in a `ConstrainedType` module; each specific type just supplies
its constructor and bounds:

```fsharp
module ConstrainedType =

    /// non-null, length-bounded string
    let createString fieldName ctor maxLen str =
        if String.IsNullOrEmpty str then
            Error $"{fieldName} must not be null or empty"
        elif str.Length > maxLen then
            Error $"{fieldName} must not be more than {maxLen} chars"
        else
            Ok (ctor str)

    /// integer in [minVal, maxVal]
    let createInt fieldName ctor minVal maxVal i =
        if   i < minVal then Error $"{fieldName}: must not be less than {minVal}"
        elif i > maxVal then Error $"{fieldName}: must not be greater than {maxVal}"
        else Ok (ctor i)

    /// string matching a regex
    let createLike fieldName ctor pattern str =
        if String.IsNullOrEmpty str then Error $"{fieldName}: must not be null or empty"
        elif Regex.IsMatch(str, pattern) then Ok (ctor str)
        else Error $"{fieldName}: '{str}' must match '{pattern}'"
```

Then each type is three trivial lines:

```fsharp
type OrderId = private OrderId of string
module OrderId =
    let value (OrderId s) = s
    let create fieldName s = ConstrainedType.createString fieldName OrderId 50 s

type WidgetCode = private WidgetCode of string
module WidgetCode =
    let value (WidgetCode c) = c
    let create fieldName c = ConstrainedType.createLike fieldName WidgetCode @"W\d{4}" c

type UnitQuantity = private UnitQuantity of int
module UnitQuantity =
    let value (UnitQuantity v) = v
    let create fieldName v = ConstrainedType.createInt fieldName UnitQuantity 1 1000 v
```

Add `createDecimal` and `createStringOption` (returns `Ok None` for empty,
`Error` only if present-but-invalid) the same way.

## Choices become DUs that lift

When a value is "one of these constrained kinds", model it as a DU over the
constrained types, and have its `create` dispatch and **lift** the sub-result
with `Result.map`:

```fsharp
type ProductCode =
    | Widget of WidgetCode
    | Gizmo  of GizmoCode

module ProductCode =
    let value = function Widget (WidgetCode c) -> c | Gizmo (GizmoCode c) -> c
    let create fieldName code =
        if String.IsNullOrEmpty code then Error $"{fieldName}: must not be empty"
        elif code.StartsWith "W" then WidgetCode.create fieldName code |> Result.map Widget
        elif code.StartsWith "G" then GizmoCode.create  fieldName code |> Result.map Gizmo
        else Error $"{fieldName}: format not recognized '{code}'"
```

`OrderQuantity` (Unit vs Kilogram) follows the same shape — pick the inner type
by context, then `Result.map` it up to the union.

## Domain operations live on the type too

Put behavior that belongs to the value in its module, returning `Result` when it
can break an invariant:

```fsharp
module Price =
    let value (Price v) = v
    let create v = ConstrainedType.createDecimal "Price" Price 0.0M 1000M v
    let multiply qty (Price p) = create (qty * p)        // may exceed bounds -> Result

module BillingAmount =
    let value (BillingAmount v) = v
    let create v = ConstrainedType.createDecimal "BillingAmount" BillingAmount 0.0M 10000M v
    let sumPrices prices =
        prices |> List.map Price.value |> List.sum |> create   // Result
```

### `unsafeCreate` — the rare, honest escape hatch

Sometimes you *know* a literal is in range (a hard-coded `0M` shipping cost). A
clearly-named `unsafeCreate` that throws on violation documents that you took
responsibility — far better than silently weakening `create`:

```fsharp
let unsafeCreate v =
    match create v with
    | Ok x -> x
    | Error e -> failwithf "Not expecting %s to be out of bounds: %s" "Price" e
```

Use it sparingly, only for provably-valid constants, never for external input.

## Why this pays off

- **Validation happens once**, at the boundary, and the type remembers it.
- **Errors are precise and field-named**, ready to aggregate (see
  `effects-and-errors.md` on applicative validation).
- **Signatures document the rules**: a function taking `EmailAddress` cannot be
  handed a raw unvalidated string.
- It scales: a 20-field record validates by `let!`-chaining 20 one-line `create`s
  in a `result { }` block (see `workflows.md`).
