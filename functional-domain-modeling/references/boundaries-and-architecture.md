# Boundaries & architecture

Keep a **pure domain core** and push every effect — serialization, persistence,
network, clock, randomness — to the outer edge. The result is the "functional
onion" (a hexagonal / ports-and-adapters architecture): dependencies point
inward, the core knows nothing of the outside world, and you can test the whole
domain with plain values and stub functions.

## The onion

```
            ┌─────────────────────────────────────────┐
            │  Api / composition root  (I/O, wiring)   │   ← impure edge
            │   ┌─────────────────────────────────┐    │
            │   │   DTOs  ·  serialization         │    │   ← boundary translation
            │   │   ┌─────────────────────────┐    │    │
            │   │   │   Workflows (pipelines)  │    │    │   ← pure use cases
            │   │   │   ┌─────────────────┐    │    │    │
            │   │   │   │  Domain types   │    │    │    │   ← pure core
            │   │   │   │  (Simple+Compound)   │    │    │
            │   │   │   └─────────────────┘    │    │    │
            │   │   └─────────────────────────┘    │    │
            │   └─────────────────────────────────┘    │
            └─────────────────────────────────────────┘
```

- **Core** (`SimpleTypes`, `CompoundTypes`): immutable domain types, no I/O.
- **Workflows** (`Implementation`): pure functions composing steps; effects only
  via injected dependencies (`workflows.md`).
- **Boundary** (`Dto`): translate between the wire/db and the domain.
- **Edge** (`Api`): the only place that does real I/O, knows concrete
  dependencies, and wires everything together (the composition root).

Rule: **nothing inner depends on anything outer.** The domain never references a
DTO, a JSON library, or a database type.

## DTOs: translation at the boundary

Domain types use constrained types (`EmailAddress`, `OrderId`) and DUs — great
inside, but not directly serializable and not stable as a wire contract. So at
the boundary, define **DTOs**: flat records of primitive, serializer-friendly
types, each paired with conversions in a same-named module.

```fsharp
type CustomerInfoDto = {                 // primitives only -> JSON/db friendly
    FirstName : string
    LastName  : string
    EmailAddress : string
    VipStatus : string
}

module CustomerInfoDto =

    /// inbound, no validation: external data -> an *unvalidated* domain input
    let toUnvalidatedCustomerInfo (dto : CustomerInfoDto) : UnvalidatedCustomerInfo =
        { FirstName = dto.FirstName; LastName = dto.LastName
          EmailAddress = dto.EmailAddress; VipStatus = dto.VipStatus }   // 1:1 copy

    /// inbound with validation: external data -> a *validated* domain object (may fail)
    let toCustomerInfo (dto : CustomerInfoDto) : Result<CustomerInfo, string> =
        result {
            let! first = String50.create "FirstName" dto.FirstName
            let! last  = String50.create "LastName"  dto.LastName
            let! email = EmailAddress.create "Email" dto.EmailAddress
            let! vip   = VipStatus.create "VipStatus" dto.VipStatus
            return { Name = { FirstName = first; LastName = last }
                     EmailAddress = email; VipStatus = vip }
        }

    /// outbound: domain -> DTO, always succeeds (unwrap with `value`)
    let fromCustomerInfo (d : CustomerInfo) : CustomerInfoDto =
        { FirstName = d.Name.FirstName |> String50.value
          LastName  = d.Name.LastName  |> String50.value
          EmailAddress = d.EmailAddress |> EmailAddress.value
          VipStatus = d.VipStatus |> VipStatus.value }
```

Three directions, by intent:
- **`toUnvalidated*`** — a plain copy, when raw input feeds a workflow that will
  validate it itself.
- **`toDomain`** — validating, returning `Result`, when you import directly into a
  validated domain object (e.g. loading from the database).
- **`fromDomain`** — always-succeeds export, unwrapping constrained types with
  `value`.

DTOs are also your **anti-corruption layer** and **versioning seam**: the wire
shape can change independently of the domain, absorbed in these conversions.

## The serialization pipeline

A request becomes a string at the edge and is translated inward, run through the
pure workflow, then translated back out — the domain never sees JSON:

```fsharp
let placeOrderApi : PlaceOrderApi =
    fun request ->
        request.Body                                   // 1. JSON string in
        |> deserializeJson<OrderFormDto>               // 2. string -> DTO
        |> OrderFormDto.toUnvalidatedOrder             // 3. DTO -> domain input
        |> workflow                                    // 4. pure workflow -> AsyncResult<events,error>
        |> Async.map (fun result ->
            match result with
            | Ok events -> events |> List.map PlaceOrderEventDto.fromDomain |> serializeJson |> ok200
            | Error err -> err |> PlaceOrderErrorDto.fromDomain |> serializeJson |> badRequest400)
//          5. events/error -> DTOs -> JSON string out
```

The pure core is steps 3→4; everything else is boundary plumbing.

## Persistence ignorance

The domain model is designed around the business, **not** the database schema.
Persistence is just another injected dependency at the edge (`LoadOrder`,
`SaveOrder` are function types), and the database's row shapes are DTOs, never
domain types. Keep ORMs, connection strings, and SQL out of the core entirely —
load to a DTO, `toDomain` it, run the workflow, `fromDomain` the result, save.

## Bounded contexts & integration events

A large system is several bounded contexts, each with its own model and ubiquitous
language. They **don't share domain types** — coupling them would defeat the
point. Instead they communicate with **events** (the past-tense outputs of
workflows), serialized as DTOs and passed via a queue/bus:

```fsharp
type PlaceOrderEvent =
    | ShippableOrderPlaced of ShippableOrderPlaced   // → Shipping context
    | BillableOrderPlaced  of BillableOrderPlaced    // → Billing context
    | AcknowledgmentSent   of OrderAcknowledgmentSent
```

The Order context emits `BillableOrderPlaced`; the Billing context consumes its
own DTO of it and translates into *its* domain. Each context stays autonomous,
and the events are the contract between them.

## Checklist

- [ ] Domain core has zero references to JSON, SQL, HTTP, or DTO types.
- [ ] Every external shape has a primitive DTO with `toDomain`/`fromDomain`.
- [ ] I/O and concrete dependencies live only at the composition root.
- [ ] The model follows the business, not the database schema.
- [ ] Contexts integrate via serialized events, never shared domain types.
