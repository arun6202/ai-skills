# Objects, async & performance

F# is functional-first, not functional-only. Objects, concurrency, and manual
performance tuning are all available — reach for them deliberately, for the
reasons below, not as the default shape of your code.

## When objects earn their place

Default to modules of functions over records/DUs. Choose a **class** when you
genuinely need one of:

- **.NET interop** — implementing a framework interface, subclassing a base
  class, or exposing a C#-friendly API surface.
- **Encapsulated identity / mutable state with invariants** — e.g. a ring buffer
  (Listing 8-14) where mutation is the point and must stay internally consistent.
- **`IDisposable` resources** — wrapping an unmanaged/`disposable` handle
  (Listing 8-5).

```fsharp
type Counter(start : int) =                 // primary constructor (Listing 8-1/8-2)
    let mutable count = start               // private field
    member _.Value = count                  // read-only member  (Listing 8-10)
    member _.Increment() = count <- count + 1
```

### Interfaces & object expressions

Define behavior contracts as interfaces; you usually don't need a named class to
implement one — an **object expression** creates a one-off implementation inline,
which is the idiomatic F# substitute for a tiny strategy class (Listing 8-21):

```fsharp
let comparer =
    { new IComparer<int> with
        member _.Compare(a, b) = compare a b }
```

### Resources: `use`, not manual dispose

`use` binds an `IDisposable` and disposes it at scope exit — F#'s `using`
(Listing 8-7). Prefer it to `try/finally`:

```fsharp
let read path =
    use reader = new StreamReader(path : string)   // disposed automatically
    reader.ReadToEnd()
```

### Equality & comparison for classes

Records/DUs get structural equality free; **classes default to reference
equality**, so two "equal" classes compare unequal (Listings 7-9, 8-24). If a
class is a value, implement equality deliberately — override `Equals` and
`GetHashCode` together, and `IComparable` if it needs ordering (Listings 8-26,
8-29). Often the simpler fix is: make it a record instead.

## Async & concurrency

F# has two CEs for asynchronous work:

- **`task { }`** — produces a `System.Threading.Tasks.Task`; the right default
  for .NET interop and most app code today (Listing 10-24).
- **`async { }`** — F#'s original cold, composable async; values don't start
  until run (`Async.RunSynchronously`, `Async.Start`). Still great for
  cancellation-friendly composition.

Inside either, `let!` awaits and binds, `do!` awaits a unit-returning op, `return`
/`return!` yield the result:

```fsharp
let tryDownloadAsync (localPath : string) (fileUri : Uri) =
    task {
        use client = new WebClient()
        try
            do! client.DownloadFileTaskAsync(fileUri, filePath)
            return Ok fileName
        with e ->
            return Error e.Message            // failures as values, even here
    }
```

### Parallelism with a throttle

Don't fire unbounded concurrent work. Limit the degree of parallelism and gather
results (Listing 10-24):

```fsharp
task {
    let! results =
        links
            .AsParallel().WithDegreeOfParallelism(5)
            .Select(fun uri -> tryDownloadAsync localPath uri)
        |> Task.WhenAll
    return results
}
```

(`Async.Parallel` is the idiomatic equivalent on the `async` side; pass a
`maxDegreeOfParallelism` to throttle.)

### Actors: `MailboxProcessor`

For state owned by one logical thread and updated via messages — counters,
in-memory caches, serialized access to a resource — use `MailboxProcessor`
(a.k.a. `Agent`). It's F#'s built-in actor: an isolated mailbox with an async
message loop, the same model that makes Erlang/Elixir concurrency safe.

```fsharp
type Msg = Incr | Get of AsyncReplyChannel<int>

let agent = MailboxProcessor.Start(fun inbox ->
    let rec loop count = async {
        let! msg = inbox.Receive()
        match msg with
        | Incr     -> return! loop (count + 1)
        | Get reply -> reply.Reply count
                       return! loop count }
    loop 0)

agent.Post Incr
let n = agent.PostAndReply Get
```

State lives in the loop's parameter (immutably threaded through `return! loop`),
never shared — so there are no locks and no data races. See `fsharp-vs-frontier`
for how this compares to Erlang processes (no built-in supervision trees; pair
with .NET hosting for restart/lifecycle).

## Performance — measure, then tune

Idiomatic F# is usually fast enough. When a profiler points at a hot path:

- **Pick the right collection** (`flow-and-collections.md`): `array` for indexed
  numeric work, `list` for prepend/recursion, `seq` to avoid materializing
  intermediates. The wrong type is the most common F# perf bug (ch. 12).
- **Avoid intermediate allocations** — fuse passes, prefer `choose` over
  `map |> filter`, and consider `seq` so a long pipeline streams rather than
  building each stage.
- **`[<Struct>]`** on small, short-lived records/DUs and `ValueOption` cut heap
  allocation and GC pressure (Listings 7-13, 3-25).
- **`inline`** removes call overhead for tiny generic helpers (`functions.md`).
- **Contained local mutation** — a `mutable` accumulator or array buffer that
  never escapes the function — is legitimate here. Keep the function observably
  pure; the immutability that matters is at the API surface.

Order of operations: write it clean and immutable first, profile, then tune the
proven hot spot — not before.
