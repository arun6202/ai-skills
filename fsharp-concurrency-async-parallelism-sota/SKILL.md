---
name: fsharp-concurrency-async-parallelism-sota
description: >-
  Senior F# guidance for concurrency, parallelism, async workflows, task
  workflows, cancellation, bounded fan-out, structured concurrency, and choosing
  Async, Task, AsyncSeq, TaskSeq, Channels, TPL Dataflow, ParallelSeq, Hopac,
  Ply, or IcedTasks. Use when writing, reviewing, or tuning F# code that runs
  many operations at once, especially ETL, I/O, bulk loading, and CPU transforms.
---

# F# Concurrency Async Parallelism SOTA

Use with `stylish-fsharp`. The goal is not "more parallel"; the goal is
controlled throughput, bounded memory, and predictable failure.

## Vocabulary

- Concurrency: multiple operations are in progress.
- Parallelism: multiple operations run at the same time on different cores.
- Async I/O: waiting without blocking a thread.
- CPU parallelism: using cores for computation.
- Backpressure: a slow downstream stage slows upstream producers.
- Structured concurrency: child work is owned, awaited, cancelled, and observed.

Do not mix these up. Most ETL work is I/O-concurrent plus a few CPU-heavy
transform stages.

## Default choice guide

Use `task {}` when:

- calling .NET libraries that return `Task`/`ValueTask`;
- writing services, CLIs, database clients, HTTP clients, Elasticsearch loaders;
- cancellation comes from `CancellationToken`;
- performance and interop matter.

Use `async {}` when:

- working with existing F# `Async` APIs;
- composing older F# libraries;
- you need F# async semantics such as `Async.CancellationToken`.

Use `AsyncSeq`/`TaskSeq` when:

- data is naturally a stream;
- each item is produced asynchronously;
- you need lazy pull-based processing.

Use `Channel<T>` when:

- you need a bounded producer/consumer queue;
- backpressure matters;
- stages have different speeds.

Use TPL Dataflow when:

- you need a graph of stages with per-block bounded capacity and parallelism;
- you want built-in completion, fault propagation, and message passing.

Use `ParallelSeq` or array parallelism when:

- the data is already in memory;
- work is CPU-bound;
- operations are pure and independent.

Use Hopac only deliberately:

- high-volume fine-grained concurrency;
- selective communication/alternatives matter;
- the team is willing to own a less-mainstream concurrency model.

Use Ply/IcedTasks only deliberately:

- hot paths show task-builder allocation overhead;
- benchmarks prove value;
- the team understands the safety and semantics.

## Rules

1. Every fan-out has a limit.
2. Every async operation accepts or is linked to a `CancellationToken`.
3. Every spawned task is awaited, supervised, or explicitly fire-and-forget with
   logging and ownership.
4. Every queue is bounded unless it is mathematically impossible to grow without
   bound.
5. Every failure is observed. No ignored `Task`, no swallowed exception.
6. Do not block on async with `.Result`, `.Wait()`, or `Async.RunSynchronously`
   inside async code.
7. Do not use `Async.Parallel` over huge collections. Use bounded workers.
8. Do not make CPU-heavy work async. Parallelize it or batch it.
9. Do not make I/O-heavy work parallel by burning threads. Await it.
10. Measure throughput, latency, memory, GC, queue depth, and error rate.

## Bounded fan-out pattern

For a list of chunks, prefer:

- a bounded channel with N workers;
- TPL Dataflow `TransformBlock`/`ActionBlock` with `MaxDegreeOfParallelism`;
- a custom semaphore gate around task creation for small/simple cases.

Avoid:

- `chunks |> Seq.map processAsync |> Async.Parallel` for thousands of chunks;
- creating one task per row/document;
- nested unbounded parallelism.

## Cancellation and shutdown

On Ctrl+C or orchestrator cancellation:

1. stop accepting new work;
2. complete input channels/blocks;
3. allow in-flight chunks to finish or time out;
4. persist checkpoints/manifests;
5. cancel remaining work;
6. await all workers;
7. return a non-zero exit code if the run is incomplete.

## Error policy

Model errors as data at the business boundary:

- row reject;
- chunk failed;
- bulk item rejected;
- stage failed;
- run cancelled.

Use exceptions for unexpected infrastructure or library failures, then convert
them to typed errors at the boundary. A failed worker must signal the supervisor.

## ETL-specific posture

For the Oracle -> Parquet/DuckDB -> NDJSON -> Elasticsearch ETL:

- extraction concurrency is DBA-limited, not CPU-limited;
- DuckDB parallelism is engine-level; avoid fighting it with outer parallel SQL;
- NDJSON writing is I/O and serialization bound; batch documents;
- Elasticsearch loading is network/cluster/backpressure bound; adapt concurrency;
- never let one stage produce unbounded files or memory for the next stage.

## Library compass

Known useful ecosystem pieces:

- `FSharp.Control.AsyncSeq`: classic async sequence abstraction.
- `FSharp.Control.TaskSeq`: task-native async sequences.
- `System.Threading.Channels`: built-in bounded channels.
- `System.Threading.Tasks.Dataflow`: built-in pipeline/dataflow blocks.
- `FSharp.Collections.ParallelSeq`: PLINQ-style parallel sequence operations.
- `Hopac`: Concurrent ML style library for advanced F# concurrency.
- `Ply`: low-overhead task/value-task computation expressions.
- `IcedTasks`: cold and cancellable task computation expressions.

Prefer built-in .NET primitives unless a library gives a clear, measured win.
