---
name: fsharp-etl-runtime-performance-sota
description: >-
  F# and .NET runtime performance skill for high-throughput ETL: memory, GC,
  batching, streaming I/O, ArrayPool/Memory, UTF-8 JSON/TSV writing, file system
  behavior, CPU versus I/O bottlenecks, profiling, BenchmarkDotNet, and
  production-safe optimization. Use with Oracle, Parquet, DuckDB, NDJSON, and
  Elasticsearch ETL implementations.
---

# F# ETL Runtime Performance SOTA

Use this when the code is correct but must move serious volume.

## Optimization order

1. Make the stage correct and measurable.
2. Identify the bottleneck with metrics/profiling.
3. Remove accidental materialization.
4. Batch I/O.
5. Bound concurrency.
6. Reduce allocation in hot loops.
7. Tune runtime/GC only after the code shape is right.

Do not start with clever low-level tricks.

## Memory rules

- Stream rows; do not load tables/files into memory.
- Batch by bytes and row groups, not arbitrary lists.
- Avoid retaining references to large buffers after write.
- Prefer `ArrayPool<byte>`/`Memory<byte>` only in proven hot paths.
- Keep mutable buffers local and unobservable.
- Watch LOH allocations from large strings, JSON blobs, and byte arrays.

In ETL, accidental retention is often worse than allocation.

## File I/O

- Use large buffered streams for TSV/NDJSON.
- Write to `.partial`, flush/close, then atomically rename.
- Hash while streaming, not with a second full-file pass when possible.
- Separate active temp directories from archived immutable outputs.
- Use byte-count metrics per file.
- Keep file counts moderate enough for the filesystem and orchestration.

## Serialization

TSV:

- encode directly to UTF-8 where practical;
- avoid culture-sensitive formatting;
- test escaping round-trip;
- do not build whole rows with repeated string concatenation in hot paths.

JSON/NDJSON:

- use `System.Text.Json.Utf8JsonWriter` or equivalent streaming writer;
- measure document size before/send while batching;
- avoid constructing huge intermediate JSON strings unless required.

## CPU parallelism

Use CPU parallelism only for pure, independent work:

- parsing batches;
- compression;
- hashing;
- JSON serialization if it is CPU-bound;
- validation rules that do not touch shared state.

Avoid parallelizing:

- Oracle queries beyond DBA limits;
- DuckDB SQL from the outside when DuckDB is already parallel;
- Elasticsearch requests beyond cluster acceptance.

## GC and runtime

For long-running ETL CLI processes:

- run on a modern .NET LTS/current runtime agreed by the project;
- capture GC counters under realistic load;
- consider server GC for throughput jobs;
- avoid excessive closure allocation in hot loops;
- avoid per-row logging;
- prefer structured aggregate metrics.

Any GC setting change must be documented with before/after evidence.

## Benchmarking

Use BenchmarkDotNet for microbenchmarks:

- TSV encode/decode;
- JSON write;
- ID generation;
- hash/checksum;
- hot validation functions.

Use stage benchmarks for real throughput:

- rows/sec;
- MB/sec;
- CPU%;
- GC allocation rate;
- max RSS;
- spill/temp bytes;
- downstream reject/retry rate.

Microbenchmarks do not prove the pipeline is fast. They only prove a small part
is not obviously slow.

## Red flags

- `Seq.toList` or `Array.ofSeq` on unbounded inputs.
- `Async.Parallel` over all rows/chunks/files.
- per-row database calls.
- per-row HTTP requests.
- per-row log lines.
- repeated string concatenation for TSV/JSON.
- hidden sorting/grouping of billion-row datasets.
- global locks around hot paths.
- dynamic reflection/serialization inside tight loops.

When one appears, stop and justify it.
