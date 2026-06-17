---
name: oracle19c-tsv-extract-sota
description: >-
  High-throughput Oracle 19c extraction guidance for large ETL jobs that pull
  source tables as TSV on Oracle Linux before Parquet/DuckDB transformation.
  Covers snapshot consistency, chunking, TSV encoding, F# streaming extraction,
  SQL*Plus/SQLcl caveats, manifests, counts, checksums, restartability, and DBA
  safety for billion-row scale exports.
---

# Oracle 19c TSV Extract SOTA

Use this skill for the extraction stage:

`Oracle 19c tables -> immutable raw TSV chunks + schema/count/hash manifests`

Default posture: extract with a purpose-built F# streaming reader using ODP.NET
or Oracle's supported .NET provider. SQL*Plus/SQLcl spooling is acceptable for
small validation runs, but for 1 billion rows it is too easy to lose control of
escaping, typing, retry, metrics, and backpressure.

## Extraction contract

Each table needs an extraction contract:

- owner/schema/table
- stable column order
- Oracle type, precision, scale, length, nullable
- extraction predicate and chunk key
- snapshot policy: global SCN, table SCN, or accepted live-read mode
- null sentinel
- TSV escaping policy
- expected row count query
- PII/security class
- LOB policy
- output path pattern

If the table has no contract, stop and create it.

## Snapshot consistency

For a consistent rebuild across 50 tables, prefer one global SCN:

1. Capture `current_scn` at run start.
2. Extract every table using `AS OF SCN :scn` where practical.
3. Record the SCN in the run ledger and every table manifest.

If undo retention cannot support the full extract at one SCN:

- coordinate with the DBA before increasing parallelism;
- chunk faster, not just wider;
- consider table groups with separate SCNs and document cross-table consistency
  risk;
- record each table's SCN and the business acceptance of that inconsistency.

Do not silently mix live reads and snapshot reads.

## Chunking

Choose chunking by this order:

1. Numeric monotonically distributed PK or surrogate key.
2. Date/time range if it is indexed and matches physical/data distribution.
3. Oracle ROWID chunks for physical tables when business key chunking is absent.
4. Custom SQL chunks for skewed tables.

Record every chunk:

- table
- chunk id
- predicate or start/end key
- start/end ROWID if used
- status
- started/ended timestamps
- row count
- byte count
- output hash
- error, if any

Chunk size should target restartable work units. Prefer chunks that finish in
minutes. Avoid huge chunks that take hours and tiny chunks that create scheduler
overhead.

## TSV format

Plain tab-delimited output is not safe unless the data is proven to contain no
tabs, CR, LF, or sentinel values. For production, define an explicit reversible
encoding:

- UTF-8 without BOM.
- LF line ending.
- Tab separates fields.
- `\N` represents database null.
- Backslash escapes backslash, tab, CR, LF, and the null sentinel inside text.
- Empty string is distinct from null if the source/provider can distinguish it.
- Dates/timestamps use ISO-8601 strings with an explicit timezone policy.
- NUMBER values are culture-invariant.
- BLOBs are omitted, externalized, or base64 encoded only when approved.

Write a decoder test before writing the extractor.

## F# extractor shape

Implement extraction as a bounded streaming pipeline:

- read table contract;
- create chunk plan;
- open one Oracle connection per worker;
- execute parameterized `SELECT column_list FROM table AS OF SCN ... WHERE ...`;
- stream with a forward-only reader;
- encode each row directly to a buffered file stream;
- flush, fsync if required by policy, hash, and atomically rename from `.partial`
  to final name;
- write manifest only after the final file exists and hash is known.

Use bounded concurrency. Start with 8-16 Oracle workers, then increase only with
DBA visibility into wait events, undo pressure, I/O, CPU, and session limits.
The ETL host has 48 cores, but Oracle is shared infrastructure unless proven
otherwise.

## Query rules

- Always name columns explicitly. Never `SELECT *`.
- Preserve source column order from the schema catalog.
- Use bind variables for chunk boundaries and SCN.
- Avoid formatting in SQL except for types that need an agreed canonical text
  representation.
- Avoid expensive source joins in extraction; pull tables as-is.
- Do not use `ORDER BY` unless required for deterministic chunking and supported
  by an index. Sorting 1B rows just to spool is usually wrong.

## SQL*Plus/SQLcl caveat

If a script-based extract is requested:

- use it only after proving escaping and null semantics;
- use `TERMOUT OFF`, large `ARRAYSIZE`, no headings/feedback/pages;
- write table-specific smoke tests with embedded tab/newline/null values;
- treat SQL*Plus output as an operational fallback, not the primary design.

## Validation

For each table:

- row count from Oracle equals sum of TSV chunk rows;
- chunk predicates cover the full intended range with no overlap;
- file hash and byte count are recorded;
- per-column null counts and min/max for key/date columns are sampled or fully
  computed according to the contract;
- any rejected/failed chunk is retryable without rewriting successful chunks.

## DBA questions to ask

- Can we use a global SCN for the expected extract duration?
- What undo retention and flashback limits apply?
- What maximum parallel sessions are acceptable?
- Which tables are partitioned, compressed, IOT, LOB-heavy, or highly skewed?
- Are there source-side resource manager limits?
- Is there a standby/replica preferred for extraction?
