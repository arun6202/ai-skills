# Per-language translation guide

Side-by-side idiom translations and an honest "where each wins" verdict. Always
emit **idiomatic** F# (see the `stylish-fsharp` skill), never a transliteration.

## Contents

- [Haskell](#haskell)
- [Erlang / Elixir](#erlang--elixir)
- [OCaml](#ocaml)
- [Scala](#scala)
- [Clojure](#clojure)
- [Rust](#rust)

---

## Haskell

The purest comparison: Haskell is lazy, pure, and built on type classes and
higher-kinded types. F# matches its data modeling and beats it on pattern
matching ergonomics, but cannot abstract over type constructors.

**ADTs are a clean match.**
```haskell
data Shape = Circle Double | Rect Double Double
area (Circle r)  = pi * r * r
area (Rect w h)  = w * h
```
```fsharp
type Shape = Circle of float | Rect of float * float
let area = function
    | Circle r   -> Math.PI * r * r
    | Rect (w,h) -> w * h
```

**`Maybe`/`Either` → `Option`/`Result`.** `fmap`/`>>=` become `Option.map`/
`Option.bind` (and `Result.*`). Monadic `do` becomes a computation expression:
```haskell
do r <- tryRadius s
   return (pi * r * r)
```
```fsharp
option { let! r = tryRadius s
         return Math.PI * r * r }
```

**Type classes → interfaces or `inline` + SRTP.** This is the real gap. A
Haskell `Num a =>` constraint becomes an `inline` function resolved statically:
```fsharp
let inline square x = x * x        // works for any type with (*)
```
For ad-hoc polymorphism over your own types, use interfaces. There is **no
higher-kinded abstraction** — you cannot write one `fmap` over "any functor".
Computation expressions give per-type ergonomics instead; `FSharpPlus` emulates
classes/HKT but swims against the language.

**Laziness.** Haskell is lazy everywhere; F# is strict, with opt-in laziness via
`seq { }` and `lazy`. F#'s strictness is more predictable about space/time;
infinite structures still work through `seq`.

**Pattern matching: F# pulls ahead.** Active patterns extend matching with your
own named views without Haskell's view-patterns / pattern-synonyms ceremony
(see `stylish-fsharp/references/pattern-matching.md`).

- **Where Haskell wins:** enforced purity (`IO`), higher-kinded type classes,
  lazy-by-default elegance, a more complete type system (GADTs, type families).
- **Where F# wins:** tooling/IDE, .NET ecosystem, active patterns, units of
  measure, type providers, async/`task`, far gentler on-ramp, predictable
  strict evaluation.

---

## Erlang / Elixir

A different axis: the BEAM is about massive lightweight concurrency and fault
tolerance, not type-level power. F# matches the *actor model* and adds static
types, but does not match the BEAM's runtime.

**Pattern matching & immutability** are first-class in both — direct translation.

**Processes + message passing → `MailboxProcessor`.**
```elixir
# Elixir GenServer-ish receive loop
def loop(count) do
  receive do
    :incr        -> loop(count + 1)
    {:get, from} -> send(from, count); loop(count)
  end
end
```
```fsharp
type Msg = Incr | Get of AsyncReplyChannel<int>
let agent = MailboxProcessor.Start(fun inbox ->
    let rec loop count = async {
        let! msg = inbox.Receive()
        match msg with
        | Incr      -> return! loop (count + 1)
        | Get reply -> reply.Reply count; return! loop count }
    loop 0)
```
State is threaded immutably through `loop` — no locks, no shared memory, same
safety story as a BEAM process.

**Supervision / "let it crash" / distribution / hot reload** are **not** built
in. The BEAM's killer features — millions of cheap preemptively-scheduled
processes, supervision trees, transparent distribution, live code upgrade — have
no F# equivalent in the box. For production actor systems reach for **Akka.NET**,
**Proto.Actor**, or **Microsoft Orleans** (virtual actors), and lean on .NET
hosting for lifecycle/restart.

- **Where the BEAM wins:** concurrency at scale, fault tolerance/supervision,
  distribution, uptime, soft-real-time scheduling.
- **Where F# wins:** static types catch message/protocol errors at compile time,
  higher single-core throughput, the .NET ecosystem, and one language for actors
  *and* number-crunching *and* UI.

---

## OCaml

F#'s closest relative — both descend from ML, sharing HM inference, ADTs,
modules, currying, and pattern matching. Most OCaml ports are nearly line-for-
line. The divergences:

- **F# adds:** active patterns, computation expressions (`async`/`task`/`seq`/
  custom), units of measure, type providers, type-safe `printf`, a full object
  model, and the .NET ecosystem.
- **OCaml has, F# lacks:** a far more powerful **module system** (functors —
  modules parameterized by modules), **polymorphic variants**, and (recently)
  multicore with an effects system. F# modules are simpler value/function
  containers; reach for interfaces + generics or DUs where OCaml would use a
  functor.

```ocaml
let rec sum acc = function [] -> acc | x :: tl -> sum (acc + x) tl
```
```fsharp
let rec sum acc = function [] -> acc | x :: tl -> sum (acc + x) tl
```

- **Where OCaml wins:** module-system expressiveness, fast native compilation,
  polymorphic variants.
- **Where F# wins:** tooling, ecosystem, async story, units of measure, type
  providers, Windows/.NET integration.

---

## Scala

The other pragmatic, multi-paradigm FP-on-a-managed-VM language (JVM vs CLR).
The trade is **type-level power vs simplicity**.

- **Scala has:** higher-kinded types, implicits/`given` (true type classes), a
  richer type system, and HKT-based ecosystems (Cats, ZIO). Cost: heavier
  syntax, slow compiles, and real complexity.
- **F# has:** leaner syntax, fast compiles, computation expressions in place of
  `for`-comprehensions, and active patterns. Cost: no HKT, weaker type-level
  abstraction.

```scala
for { r <- tryRadius(s) } yield math.Pi * r * r      // Option for-comprehension
```
```fsharp
option { let! r = tryRadius s in return Math.PI * r * r }
```

- **Where Scala wins:** type-level expressiveness, HKT libraries, JVM ecosystem.
- **Where F# wins:** simplicity, compile speed, less ceremony, units of measure,
  type providers — usually the better choice when you want FP without the
  type-astronautics budget.

---

## Clojure

A dynamically-typed Lisp built on immutable persistent data structures, macros,
and REPL-driven flow. F# trades Lisp dynamism and metaprogramming for static
types and performance.

- **Immutable data + pipelines** translate well: Clojure's threading macro `->>`
  is F#'s `|>`; map/filter/reduce map to `Seq.map`/`filter`/`fold`.
- **Transducers → composed `Seq` functions** (lazy, fusible pipelines).
- **`core.async` channels → `MailboxProcessor`/`task`**; **STM/atoms → agents**
  or .NET concurrency primitives.
- **Macros:** F# has **no general macro system.** Its nearest tools are
  quotations (`<@ … @>`), **type providers** (compile-time type generation), and
  computation expressions for embedded DSLs — narrower than Lisp macros but
  type-checked.
- **REPL:** F# Interactive, `.fsx`, and .NET notebooks give a comparable
  interactive loop, with types.

```clojure
(->> xs (map inc) (filter even?) (reduce +))
```
```fsharp
xs |> Seq.map ((+) 1) |> Seq.filter (fun n -> n % 2 = 0) |> Seq.sum
```

- **Where Clojure wins:** macros/metaprogramming, dynamic flexibility, the Lisp
  REPL workflow, JVM ecosystem.
- **Where F# wins:** static type safety, performance, refactorability, tooling.

---

## Rust

Both reject `null`, lean on `enum`/ADTs + exhaustive `match`, and thread `Result`/
`Option` through everything — Rust's functional core feels familiar. The split is
**developer velocity vs control**.

**Error handling is strikingly similar.** Rust's `?` operator is F#'s railway
`bind` / a `result { }` CE:
```rust
fn parse(line: &str) -> Result<Customer, Error> {
    let email = Email::try_new(col(line, 1)?)?;
    Ok(Customer { name: col(line, 0)?, email })
}
```
```fsharp
let parse line = result {
    let! email = Email.tryCreate (col line 1)
    let! name  = col line 0
    return { Name = name; Email = email } }
```

- **Rust has, F# lacks:** ownership/borrowing, no GC, zero-cost abstractions,
  compile-time data-race freedom, `trait`-based generics (true type classes),
  and systems-level control.
- **F# has, Rust lacks (for typical app work):** much faster development, a GC so
  you don't fight lifetimes, the .NET ecosystem, computation expressions, active
  patterns, units of measure, type providers.

- **Where Rust wins:** raw performance, memory/latency control, no-GC and
  embedded/systems domains, fearless low-level concurrency.
- **Where F# wins:** velocity and ecosystem for business/data/web/back-end work
  where a GC is fine and you'd rather ship than satisfy the borrow checker.

---

## Quick verdict

F# rarely "wins" a single-axis contest against a specialist (Haskell on types,
Erlang on concurrency, Rust on performance). Its edge is the **whole package**:
frontier-grade data modeling and pattern matching, ergonomic effect handling,
unique features (units of measure, type providers, active patterns,
computation expressions), and a pragmatic, well-tooled .NET platform — so the
elegant solution is also the one you can ship Monday. Recommend F# when that
balance matters; recommend the specialist when one axis dominates the problem.
