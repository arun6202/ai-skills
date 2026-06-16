# Workflows, states & dependencies

A business use case is a **function with a type**. Design that type — and the
type of every step — before writing a single body. The signatures *are* the
design; getting them right with the domain expert is the real work.

## A workflow is one typed function

Model the whole use case as input → output, with effects in the type:

```fsharp
type PlaceOrder =
    UnvalidatedOrder -> AsyncResult<PlaceOrderEvent list, PlaceOrderError>
```

Read it aloud: "place-order takes an unvalidated order and asynchronously returns
either a list of events or a place-order error." That single line is the
context's public contract (it lives in `*.PublicTypes`). Inputs, output events,
and errors are all explicit types:

```fsharp
// input: a command carrying raw, unvalidated data from outside
type UnvalidatedOrder = { OrderId : string; Lines : UnvalidatedOrderLine list; (* … *) }

// outputs: things that happened, as a DU of events
type PlaceOrderEvent =
    | ShippableOrderPlaced of ShippableOrderPlaced
    | BillableOrderPlaced  of BillableOrderPlaced
    | AcknowledgmentSent   of OrderAcknowledgmentSent

// errors: everything that can go wrong, as a DU
type PlaceOrderError =
    | Validation   of ValidationError
    | Pricing      of PricingError
    | RemoteService of RemoteServiceError
```

A workflow consumes a **command** (an instruction, named imperatively) and emits
**events** (facts in the past tense). Other contexts react to the events; this
is how bounded contexts integrate (see `boundaries-and-architecture.md`).

## Design every step as a type first

Before implementing, write the function type of each step in `*.InternalTypes`.
This is the heart of "type-first design" — you discover the shape of the solution
in the signatures, cheaply, and can review them with a domain expert:

```fsharp
type ValidateOrder =
    CheckProductCodeExists                       // dependency
     -> CheckAddressExists                       // dependency
     -> UnvalidatedOrder                         // input
     -> AsyncResult<ValidatedOrder, ValidationError>   // output

type PriceOrder =
    GetPricingFunction                           // dependency
     -> ValidatedOrder                           // input
     -> Result<PricedOrder, PricingError>        // output
```

Note the convention: **dependencies first, then the real input last**, so partial
application yields a clean `Input -> Output` function.

## States are types; transitions are functions

Model an entity's lifecycle as a chain of *distinct* types, one per stage, and
make each step take one stage and return the next:

```
UnvalidatedOrder  --validate-->  ValidatedOrder  --price-->  PricedOrder  --…
```

```fsharp
type ValidatedOrder = { OrderId : OrderId; Lines : ValidatedOrderLine list; (* … *) }
type PricedOrder    = { OrderId : OrderId; AmountToBill : BillingAmount; Lines : PricedOrderLine list; (* … *) }
```

Because `priceOrder` requires a `ValidatedOrder`, the compiler makes it
*impossible* to price an order you haven't validated, or to emit an order you
haven't priced. The state machine is enforced by the type checker, not by
runtime flags or your memory. Prefer this to a single mutable `Order` with an
`status : string` field and nullable sections.

## Implement steps, then compose

Each step is a small function annotated with its type; the body falls out:

```fsharp
let validateOrder : ValidateOrder =
    fun checkProductCodeExists checkAddressExists unvalidatedOrder ->
        asyncResult {
            let! orderId =
                unvalidatedOrder.OrderId |> OrderId.create "OrderId"
                |> Result.mapError ValidationError
                |> AsyncResult.ofResult
            let! lines =
                unvalidatedOrder.Lines
                |> List.map (toValidatedOrderLine checkProductCodeExists)
                |> Result.sequence                        // List<Result> -> Result<List>
                |> AsyncResult.ofResult
            // …assemble and return the ValidatedOrder
            return { OrderId = orderId; Lines = lines; (* … *) }
        }
```

The overall workflow chains the steps, mapping each step's error into the
workflow error DU so the rails stay one consistent type:

```fsharp
let placeOrder
    checkProductExists checkAddressExists getPricingFunction      // dependencies
    calculateShippingCost createAckLetter sendAck
    : PlaceOrder =
    fun unvalidatedOrder ->
        asyncResult {
            let! validated =
                validateOrder checkProductExists checkAddressExists unvalidatedOrder
                |> AsyncResult.mapError PlaceOrderError.Validation
            let! priced =
                priceOrder getPricingFunction validated
                |> AsyncResult.ofResult
                |> AsyncResult.mapError PlaceOrderError.Pricing
            let withShipping = priced |> addShippingInfo calculateShippingCost |> freeVipShipping
            let ackOpt       = acknowledgeOrder createAckLetter sendAck withShipping
            return createEvents priced ackOpt
        }
```

See `effects-and-errors.md` for `asyncResult`, `Result.sequence`,
`AsyncResult.ofResult`/`mapError`.

## Dependencies are parameters (DI by partial application)

A step that needs a capability takes it as a **leading function parameter** — not
an interface, not a service locator. The type of the dependency *is* its
contract:

```fsharp
type CheckProductCodeExists = ProductCode -> bool
type GetProductPrice        = ProductCode -> Price
type CheckAddressExists     = UnvalidatedAddress -> AsyncResult<CheckedAddress, AddressValidationError>
```

This keeps the domain pure and testable: pass a stub function in tests, the real
one in production. There is exactly **one place** that knows the concrete
implementations — the composition root in `*.Api`:

```fsharp
let workflow =
    Implementation.placeOrder
        checkProductExists            // real impls injected here, once
        checkAddressExists
        getPricingFunction
        calculateShippingCost
        createOrderAcknowledgmentLetter
        sendOrderAcknowledgment
// `workflow` is now UnvalidatedOrder -> AsyncResult<…>; the rest of the app sees only that
```

Partial application supplies the dependencies and hands back the clean
`Input -> Output` function the workflow type promised. That is the entirety of
"dependency injection" in functional F# — no framework required.

## Checklist

- [ ] The use case is a single typed function (command → events/`Result`).
- [ ] Input is a command (imperative noun-phrase); outputs are events (past tense).
- [ ] Every step has a written function type *before* a body exists.
- [ ] Each lifecycle stage is its own type; transitions move between them.
- [ ] Dependencies are leading function parameters, wired once at a composition root.
- [ ] Step errors are normalized into one workflow error DU.
