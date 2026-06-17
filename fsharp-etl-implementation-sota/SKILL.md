---
name: fsharp-etl-implementation-sota
description: >-
  F# implementation guide for high-volume ETL from Oracle 19c to Parquet/DuckDB
  to Elasticsearch NDJSON. Use when writing, refactoring, or reviewing F# code
  for extraction, transformation orchestration, file manifests, bulk loading,
  retry, metrics, typed configuration, and error handling.
---

# F# ETL Implementation SOTA

Use with `stylish-fsharp` and `functional-domain-modeling`. The code should be
functional at the core, imperative at the I/O shell, and explicit about failure.

## Core model

Represent stages and states with types:

```fsharp
type Stage =
    | ExtractRaw
    | ConvertBronze
    | BuildSilver
    | BuildGold
    | WriteNdjson
    | BulkLoad
    | Reconcile

type ChunkStatus =
    | Planned
    | Running of startedAt: DateTimeOffset
    | Succeeded of rowCount: int64 * bytes: int64 * hash: string
    | Failed of error: EtlError

type EtlError =
    | ConfigError of string
    | SourceError of table: string * message: string
    | DecodeError of table: string * chunk: string * row: int64 * message: string
    | TransformError of step: string * message: string
    | ElasticsearchError of status: int * reason: string
```

Keep raw strings at the boundary. Parse them into constrained types before the
pipeline core sees them.

## Project shape

A practical F# solution layout:

- `Domain`: contracts, manifests, IDs, errors, stage states.
- `Contracts`: YAML/JSON readers and validators.
- `OracleExtract`: Oracle connection, chunk planning, TSV encoder.
- `Parquet`: TSV decoder, type conversion, Parquet writer/reader.
- `DuckDb`: SQL execution, PRAGMAs, transform manifests.
- `Ndjson`: strict JSON/NDJSON writer.
- `Elastic`: bulk client, retries, response parser.
- `Quality`: counts, checksums, join reports, sample validation.
- `Cli`: commands such as `plan`, `extract`, `bronze`, `silver`, `gold`,
  `ndjson`, `load`, `reconcile`.

## Streaming and backpressure

Use bounded channels or MailboxProcessor where they clarify ownership:

- source reader produces rows;
- encoder/serializer writes bytes;
- hasher observes bytes;
- manifest writer commits after successful close/rename.

Every queue must be bounded. Unbounded queues hide memory leaks until the 110M
document load is already in pain.

Rules:

- Pass `CancellationToken` through all async boundaries.
- Use `use`/`use!` for disposable connections, readers, streams.
- Avoid `Async.Parallel` over huge collections. Work from bounded chunk streams.
- Prefer `Task` interop at .NET library boundaries; keep domain functions pure.
- Do not materialize full tables, full NDJSON files, or full bulk responses in
  memory.

## Config and contracts

Load configuration once, validate it fully, then pass typed config through:

- no magic paths in code;
- no table-specific business logic hidden in functions when it belongs in a
  contract;
- no environment-specific constants in transformation SQL;
- secrets come from environment/secret store, not config files.

Use generated or strongly typed accessors where possible so table/document names
are not scattered as string literals.

## Error handling

Use `Result` for expected failures and exceptions only at I/O boundaries:

- config validation returns all errors, not just the first;
- per-row decode errors go to reject streams when the contract allows rejects;
- source connection or file system failures fail the chunk;
- ES transient failures retry with backoff;
- ES permanent per-document failures are rejects and must be reconciled.

Never swallow an exception and continue without recording it in the run ledger.

## Serialization

TSV:

- one encoder and one decoder;
- property tests for escaping round-trip;
- UTF-8, invariant culture, explicit null sentinel.

JSON/NDJSON:

- use `System.Text.Json.Utf8JsonWriter` or an equivalent streaming writer;
- ensure final newline;
- test that every action line is followed by one source line;
- reject documents over the configured byte-size limit before sending to ES.

## Observability in code

Emit structured logs and metrics with these dimensions:

- run id
- stage
- table or document type
- chunk id
- source path
- row count
- bytes
- rows/sec and MB/sec
- retry count
- reject count
- ES status/error type

Logs should be useful after the process exits. Console-only progress bars are
not enough.

## Testing strategy

- Unit test encoders/decoders, ID generation, null handling, and type parsing.
- Golden-sample tests for each document contract.
- Property tests for TSV round-trip and deterministic IDs.
- Integration tests with small Oracle-like fixtures or exported TSV fixtures.
- DuckDB SQL tests on tiny Parquet fixtures.
- ES loader tests against a local/test index, including partial bulk failures.

Every transformation change updates a golden sample or explains why not.
