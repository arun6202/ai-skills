---
name: fsharp-concurrency-library-compass-sota
description: >-
  Library selection compass for F# concurrency and high-throughput data work.
  Use when deciding whether to use built-in Task/Async, System.Threading.Channels,
  TPL Dataflow, FSharp.Control.AsyncSeq, FSharp.Control.TaskSeq, Hopac, Ply,
  IcedTasks, ParallelSeq, FSharpPlus, FsToolkit.ErrorHandling, or other
  ecosystem pieces in production ETL and services.
---

# F# Concurrency Library Compass SOTA

Use this when choosing libraries. The rule is simple: prefer a boring primitive
that the team can operate at 3 a.m. over an elegant primitive nobody can debug.

## Default stack for ETL

Start with:

- F# `task {}` and .NET `Task`/`CancellationToken` for I/O interop.
- `System.Threading.Channels` for bounded queues.
- `System.Threading.Tasks.Dataflow` for multi-stage graphs.
- `System.Text.Json` streaming writer for NDJSON.
- `FsToolkit.ErrorHandling` if the codebase already uses Result/AsyncResult
  helpers.
- BenchmarkDotNet and runtime counters for performance work.

Add specialist libraries only when they solve a named problem.

## Library notes

`FSharp.Control.AsyncSeq`

- Good for classic F# async streams.
- Useful when existing APIs are `Async`.
- Less natural for modern task-heavy .NET libraries.

`FSharp.Control.TaskSeq`

- Good for task-native async streams.
- Better fit for modern .NET interop and ETL streaming.
- Use when pull-based streaming is clearer than channels.

`System.Threading.Channels`

- Best default for bounded producer/consumer.
- Small surface area, high performance, built into .NET.
- Requires you to write completion/fault supervision carefully.

`System.Threading.Tasks.Dataflow`

- Best default for explicit pipeline graphs.
- Has bounded capacity, per-block parallelism, completion, and faults.
- Heavier than channels but easier for non-trivial pipelines.

`FSharp.Collections.ParallelSeq`

- Useful for CPU-bound in-memory sequences.
- Not a streaming/backpressure tool.
- Dangerous for I/O unless carefully bounded.

`Hopac`

- Powerful Concurrent ML style model with jobs, alternatives, channels.
- Consider for fine-grained concurrency or select/choice-heavy coordination.
- Avoid as default ETL infrastructure unless the team already knows it.

`Ply`

- Low-overhead Task/ValueTask computation expressions.
- Consider only after profiling shows task CE overhead matters.
- Beware unsafe/affine builders unless the invariants are understood.

`IcedTasks`

- Cold and cancellable task builders.
- Useful when task-start semantics and cancellation ergonomics matter.
- Add intentionally; do not sprinkle across the codebase casually.

`FSharpPlus`

- Broad functional extensions.
- Useful for teams comfortable with higher abstraction.
- Avoid introducing only to make simple ETL code look clever.

`FsToolkit.ErrorHandling`

- Practical helpers for `Result`, `Async<Result<_,_>>`, and `Task<Result<_,_>>`.
- Often valuable in ETL because failures are domain values.
- Keep error types explicit; helpers do not replace design.

## Selection questions

Ask:

- Is the work I/O-bound or CPU-bound?
- Is the data push-based or pull-based?
- Is bounded buffering required?
- Does ordering matter?
- How does cancellation propagate?
- How are exceptions observed?
- Can operations be retried idempotently?
- What metrics prove the primitive is healthy?
- Can the production team debug this library?

## Approval bar for adding a dependency

Add a library only if:

- it removes real complexity;
- it is actively maintained enough for project risk;
- it works on the target .NET runtime;
- failure/cancellation semantics are understood;
- a small spike proves it under realistic load;
- the dependency is documented in the architecture notes.

For the Oracle -> Elasticsearch ETL, dependency minimalism is a feature.
