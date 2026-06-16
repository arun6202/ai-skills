# Effects & errors at workflow scale

Effects belong in the type. "Can fail" is `Result<'ok,'error>`; "is async" is
`Async<'a>`; "async and can fail" is `AsyncResult<'ok,'error>`. Keep pure/total
steps plain, and lift them only where they meet effectful steps — so the type of
each function honestly states what it does.

This builds on `stylish-fsharp/references/errors-and-effects.md` (Option vs
Result, the railway idea). Here we operate it at application scale.

## `AsyncResult` — the workflow's two-and-a-half track

```fsharp
type AsyncResult<'success,'failure> = Async<Result<'success,'failure>>
```

Most real workflows are `AsyncResult`: they touch I/O (async) and can fail
(result). You'll want a small toolkit (the book ships its own `Result.fs`; in
real projects use **`FsToolkit.ErrorHandling`**, which provides all of this):

| Need                                          | Function                                  |
|-----------------------------------------------|-------------------------------------------|
| lift a plain value onto the rails             | `AsyncResult.retn` / `Result.Ok`          |
| lift a sync `Result` into `AsyncResult`       | `AsyncResult.ofResult`                    |
| map the success value                         | `AsyncResult.map` / `Result.map`          |
| map/convert the error value                   | `AsyncResult.mapError` / `Result.mapError`|
| chain a next might-fail step                  | `AsyncResult.bind` / `Result.bind`        |
| `List<Result>` → `Result<List>`              | `Result.sequence` (a.k.a. traverse)       |

## Computation expressions flatten the rails

Writing `bind`/`map` chains by hand gets noisy. The `result { }` and
`asyncResult { }` CEs let you write the happy path linearly; `let!` unwraps an
`Ok`/`Async<Ok>` and **short-circuits on the first `Error`**:

```fsharp
let toCustomerInfo (dto : UnvalidatedCustomerInfo) = result {
    let! first  = String50.create   "FirstName"    dto.FirstName
    let! last   = String50.create   "LastName"     dto.LastName
    let! email  = EmailAddress.create "Email"      dto.EmailAddress
    let! vip    = VipStatus.create  "VipStatus"    dto.VipStatus
    return { Name = { FirstName = first; LastName = last }
             EmailAddress = email; VipStatus = vip }
}
```

That validates a whole record in one readable block — any failure aborts with its
error. Use `asyncResult { }` identically when steps are async; lift sync pieces
in with `AsyncResult.ofResult`.

## Normalize errors into one workflow error DU

Each step naturally produces *its own* error type (a creation string, an address
error). For the rails to compose, convert every step's error into the single
workflow error DU with `mapError` at the seam:

```fsharp
unvalidatedOrder.OrderId
|> OrderId.create "OrderId"        // Result<OrderId, string>
|> Result.mapError ValidationError // Result<OrderId, ValidationError>
```

and again where a sub-workflow error rolls up to the top error type:

```fsharp
validateOrder … |> AsyncResult.mapError PlaceOrderError.Validation
priceOrder    … |> AsyncResult.mapError PlaceOrderError.Pricing
```

Model errors as a **DU, not strings**, so callers can branch and you can localize
messages at the boundary:

```fsharp
type PlaceOrderError =
    | Validation    of ValidationError
    | Pricing       of PricingError
    | RemoteService of RemoteServiceError      // infra failure, distinct from domain failure
```

Keep **domain errors** (a bad product code) separate from **infrastructure
errors** (a timeout) — they're handled, logged, and retried differently.

## `sequence` / `traverse` — many results into one

Validating a list of lines gives `ValidatedOrderLine list` only if *all* succeed.
`map` then `sequence` turns `List<Result<_,_>>` into `Result<List<_>, _>`:

```fsharp
unvalidatedOrder.Lines
|> List.map (toValidatedOrderLine checkProductExists)   // Result<Line, Err> list
|> Result.sequence                                      // Result<Line list, Err>  (first Error wins)
```

(`FsToolkit.ErrorHandling` spells these `List.traverseResultM` /
`List.sequenceResultM`.)

## Monadic (fail-fast) vs applicative (collect-all) validation

- **Monadic** (`let!`, `bind`, `sequence`) stops at the **first** error. Right for
  pipeline steps where later steps depend on earlier ones (you can't price an
  order that failed to validate).
- **Applicative** (`Validation` / `apply` / `<*>`) runs independent checks and
  **accumulates every** error. Right for form validation, where the user wants all
  problems at once, not one at a time:

```fsharp
// gather all field errors, not just the first
let validateCustomer first last email =
    let ctor f l e = { FirstName = f; LastName = l; Email = e }
    ctor
    <!> (String50.create "First" first   |> Validation.ofResult)
    <*> (String50.create "Last"  last    |> Validation.ofResult)
    <*> (EmailAddress.create "Email" email |> Validation.ofResult)
    // -> Validation<Customer, string list>
```

Use applicative `Validation` at the input boundary to report all errors; switch
to monadic `Result`/`AsyncResult` once inside the dependent pipeline. `Validation`
is just `Result<'ok, 'error list>` with an applicative `apply` — `FsToolkit`
provides it and the `validation { }` CE.

## Rules of thumb

- Put the effect in the signature; never hide async or failure behind a plain
  return type.
- Convert each step's error to the workflow error DU **at the call site**, with
  `mapError`.
- Reach for a CE when the linear form reads better; reach for explicit
  `bind`/`map` composition when the steps compose point-free and cleanly.
- Don't introduce `AsyncResult` until a step is genuinely async — keep pure steps
  `Result` (or plain) and lift at the boundary with `AsyncResult.ofResult`.
