---
name: oracle19c-to-elasticsearch-etl-sota
description: >-
  Governance and architecture guide for a large Oracle 19c to Elasticsearch ETL:
  around 1 billion Oracle rows across 50 tables, extracted as TSV on Oracle
  Linux, converted and joined through Parquet/DuckDB, emitted as Elasticsearch
  bulk NDJSON, implemented in F#. Use whenever planning, reviewing, or building
  this migration/indexing workflow, especially when business logic is too large
  for LLM context and must be externalized into contracts, manifests, and tests.
---

# Oracle 19c to Elasticsearch ETL SOTA

Use this as the top-level governance skill for the full pipeline:

`Oracle 19c -> raw TSV -> bronze Parquet -> silver joined Parquet/DuckDB -> gold ES docs -> NDJSON -> Elasticsearch bulk load`

Target scale: 50 Oracle tables, about 1 billion source rows, about 110 million ES
documents, Oracle Linux host with 256 GB RAM, 48 cores, 5 TB SSD, no network
bandwidth constraint, F# implementation.

The central rule: **business meaning lives outside the LLM**. Claude can write
code, tests, SQL, and runbooks, but it must not invent or remember table meaning
from chat. Encode the meaning in versioned contracts and make the pipeline read
them.

## Non-negotiable artifacts

Before implementation, create or update these repository artifacts:

1. `etl-manifest.yaml`: tables, extraction mode, chunk key, expected row counts,
   SCN/snapshot policy, TSV path, Parquet path, owner, SLA, PII class.
2. `schema-catalog/`: one file per Oracle table with column order, Oracle type,
   nullable flag, PK/UK/FK notes, LOB policy, timestamp/timezone policy.
3. `document-contracts/`: one file per ES document type with source tables,
   join cardinality, deterministic ID rule, routing rule, null/missing policy,
   nested arrays, analyzers, and example documents.
4. `mapping/`: Elasticsearch index templates/settings/mappings. No dynamic
   mapping for production loads.
5. `quality-rules/`: source, join, and document invariants.
6. `run-ledger/`: append-only run manifests with code version, contract version,
   source SCN or cutoff, chunk ranges, file hashes, counts, rejects, timings.
7. `golden-samples/`: small representative rows and expected docs for every
   document type and edge case.

Do not proceed on a table or document type until its contract exists.

## Architecture principles

- Prefer boring, restartable batch stages over clever streaming. Each stage writes
  durable files and a manifest before the next stage reads it.
- Treat each file as immutable. If logic changes, write a new versioned output
  path. Never patch old raw extracts.
- Separate layers:
  - `raw`: TSV exactly as decoded from Oracle with sidecar schema and counts.
  - `bronze`: typed Parquet per source table/chunk, no business joins.
  - `silver`: normalized/joined Parquet with business keys and audit columns.
  - `gold`: one row per target ES document plus `_id`, `_routing`, index name.
  - `bulk`: NDJSON files sized for Elasticsearch bulk ingestion.
- Optimize for evidence: every row count, join drop, duplicate key, reject, and
  ES failure must be explainable from manifests.
- Assume failure. Every stage must be idempotent or resumable by chunk/file.
- Design for backpressure. The ES loader must slow itself on 429/rejections
  instead of pushing a fixed firehose.

## Planning checklist

For each of the 50 tables:

- Identify primary key or stable extraction key. If none exists, use ROWID chunks
  only for one snapshot and never as business identity.
- Decide snapshot consistency: one global SCN for all tables is the default for a
  consistent rebuild. If impossible, document the accepted inconsistency.
- Estimate raw TSV, Parquet, silver, gold, and NDJSON sizes. 5 TB SSD is large
  but not infinite when raw and derived layers coexist.
- Classify data sensitivity. Mask or omit fields before gold if ES users should
  not see them.
- Define type conversions: NUMBER precision/scale, dates, timestamps with time
  zone, CLOB/BLOB handling, empty string vs null, Oracle char semantics.

For each ES document type:

- Define the owning root entity and deterministic document ID.
- Define one-to-one, one-to-many, and many-to-one joins explicitly.
- Decide whether child rows become nested arrays, denormalized scalar fields, or
  separate documents.
- Define conflict behavior: duplicate child keys, multiple active records, null
  parents, orphan children.
- Define search behavior before mapping: text vs keyword, analyzers, normalizers,
  date formats, numeric precision, nested fields.

## Stage gates

Use these gates. If a gate fails, fix data/contracts/code before moving on.

1. **Source readiness**: Oracle schema captured, row estimates known, chunking
   plan reviewed with DBA, extraction user has least required privileges.
2. **Raw complete**: all TSV chunks exist, byte hashes recorded, source counts
   reconcile per table and per chunk.
3. **Bronze typed**: Parquet row counts equal TSV row counts, type conversion
   rejects are explainable and below the agreed threshold.
4. **Silver joined**: join cardinality reports match contracts; orphan/duplicate
   reports reviewed by data owner.
5. **Gold document**: document count equals the contract expectation, golden
   samples pass, mapping validation passes.
6. **ES dry run**: small index load passes with mappings/settings, counts, search
   smoke tests, and reject handling.
7. **Full load**: bulk loader reaches steady state without sustained 429s,
   document count and sample hashes reconcile.
8. **Cutover**: alias switch or application pointer change is atomic and
   reversible. Old index is retained until signoff.

## Capacity posture for this machine

- Leave memory for Linux page cache and DuckDB temp files. Do not give all 256 GB
  to a single process.
- Start DuckDB around `threads=32` and `memory_limit=160GB`; benchmark before
  increasing. More threads can increase spill pressure.
- Keep file counts moderate. Prefer chunks large enough for throughput but small
  enough to retry quickly, typically minutes per chunk rather than hours.
- Keep TSV only as long as needed for audit/replay, or move it to cheaper
  storage after Parquet validation. Raw + bronze + silver + gold + NDJSON can
  exceed expectations quickly.
- Use the SSD for active temp and current stage only. Archive completed immutable
  stages if free space drops below the safety threshold.

## LLM working rules

When Claude is asked to implement or change this ETL:

1. Load this skill first, then load the focused skill for the stage.
2. Inspect the relevant manifest/contract files before writing code.
3. Ask for missing business rules instead of guessing.
4. Generate code from contracts, not from remembered chat.
5. Add or update golden samples for any transformation change.
6. Add reconciliation output for every new stage.
7. Keep implementation in F# idioms: typed configs, discriminated unions for
   states/errors, bounded async pipelines, explicit cancellation, streaming I/O.

## Source basis

This skill distills:

- Data lifecycle, governance, architecture, orchestration, quality, and security
  framing from the provided data engineering books.
- Reliability, scalability, maintainability, derived data, and observability
  principles from the provided data-intensive applications book.
- Current vendor guidance from Oracle Database 19c documentation and Elastic
  indexing/bulk API documentation.

Open the focused skills for stage-level mechanics:

- `oracle19c-tsv-extract-sota`
- `parquet-duckdb-joinhouse-sota`
- `elasticsearch-ndjson-bulk-load-sota`
- `fsharp-etl-implementation-sota`
- `etl-data-quality-observability-sota`
