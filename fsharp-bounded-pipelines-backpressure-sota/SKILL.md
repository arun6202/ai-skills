---
name: fsharp-bounded-pipelines-backpressure-sota
description: >-
  F# skill for building bounded producer/consumer pipelines with backpressure
  using System.Threading.Channels, TPL Dataflow, MailboxProcessor, AsyncSeq, and
  TaskSeq. Use for ETL stages, file processing, database extraction, NDJSON
  generation, Elasticsearch bulk loaders, and any workflow where memory must not
  grow with input size.
---

# F# Bounded Pipelines Backpressure SOTA

Use this when data flows through stages at different speeds. In large ETL, the
pipeline must bend under load, not balloon.

## Pipeline law

Every edge between stages has:

- a bounded capacity;
- a documented overflow behavior;
- completion semantics;
- fault propagation;
- cancellation;
- metrics for depth, throughput, and latency.

If you cannot name these, the pipeline is unfinished.

## Choose the primitive

Use `Channel<T>` for:

- simple producer/consumer;
- custom worker loops;
- minimal dependencies;
- high-throughput ETL where you want direct control.

Use TPL Dataflow for:

- multi-stage graphs;
- per-stage `MaxDegreeOfParallelism`;
- per-stage `BoundedCapacity`;
- built-in completion/fault propagation.

Use `MailboxProcessor` for:

- state ownership and serialized mutation;
- coordinators, ledgers, progress trackers;
- not for high-volume row transport unless measured.

Use `AsyncSeq`/`TaskSeq` for:

- pull-based streaming;
- composing asynchronous item streams;
- low ceremony where backpressure follows from the consumer pulling.

Avoid unbounded `ResizeArray`, `ConcurrentQueue`, `BlockingCollection` defaults,
or accumulating `Task list` for large inputs.

## ETL stage map

Oracle extraction:

- chunk planner produces chunk descriptors;
- bounded worker pool reads Oracle chunks;
- each chunk writes a `.partial` file;
- manifest writer observes committed chunks.

TSV to Parquet:

- file reader streams decoded rows;
- parser/validator emits typed rows or rejects;
- writer batches row groups;
- bounded reject writer prevents logging from exploding.

NDJSON:

- gold rows stream in;
- serializer batches by bytes and document count;
- file/request writer enforces max body size.

Elasticsearch bulk:

- request producer reads NDJSON batches;
- bounded HTTP workers send requests;
- response parser emits successes/rejects;
- controller adjusts concurrency on 429/rejections.

## Completion rules

For Channels:

- producers call `Complete` exactly once;
- consumers drain until completion;
- exceptions complete the channel with error;
- supervisor awaits all worker tasks.

For Dataflow:

- link with completion propagation where appropriate;
- call `Complete` on the head block;
- await terminal block `Completion`;
- inspect faulted blocks and preserve original errors.

Never let process exit before terminal completion has been awaited.

## Backpressure rules

- Prefer `WaitToWriteAsync`/`WriteAsync` over `TryWrite` unless dropping is a
  deliberate policy.
- Use byte-based limits for NDJSON/HTTP, not only item counts.
- Use separate capacities for memory-heavy and memory-light messages.
- Make capacities configuration values with safe defaults.
- Emit queue depth metrics.

## Ordering

Do not preserve order unless needed:

- source chunk order rarely matters;
- row order inside files may matter only for reproducibility;
- ES bulk requests can complete out of order if IDs are deterministic;
- preserving global order often destroys throughput.

When order matters, declare it and pay the cost deliberately.

## Failure behavior

Define per stage:

- fail-fast: stop all work on first critical error;
- best-effort with rejects: continue and record bad records;
- retry: transient I/O with bounded attempts and backoff;
- quarantine: move bad chunk/file to a review state.

Do not mix these policies inside ad hoc catch blocks.

## Metrics

At minimum:

- input/output rows per second;
- bytes per second;
- active workers;
- queue depth;
- retry count;
- reject count;
- per-stage latency percentile;
- memory and GC counters for long runs.
