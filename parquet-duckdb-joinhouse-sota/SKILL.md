---
name: parquet-duckdb-joinhouse-sota
description: >-
  Guidance for converting raw Oracle TSV extracts into typed Parquet, joining
  and shaping data with DuckDB, and producing one-row-per-Elasticsearch-document
  gold datasets at very large scale. Use for bronze/silver/gold lakehouse-style
  stages, join cardinality contracts, Parquet layout, DuckDB tuning, and
  reproducible transformation design.
---

# Parquet DuckDB Joinhouse SOTA

Use this skill for:

`raw TSV -> bronze typed Parquet -> silver joined Parquet -> gold ES document rows`

The goal is not "use DuckDB for everything." The goal is a reproducible local
analytics engine that can turn immutable extracts into auditable Elasticsearch
documents on a large Oracle Linux host.

## Layer rules

Bronze:

- one Parquet dataset per source table;
- no business joins;
- typed columns from schema catalog;
- original source columns plus audit columns: `run_id`, `table_name`,
  `chunk_id`, `source_scn`, `row_ordinal`, `source_hash` if needed.

Silver:

- normalized business entities and relationship tables;
- cleaned types, canonical keys, deduplicated records;
- join quality metrics written beside every output.

Gold:

- exactly one row per target ES document;
- includes `_index`, `_id`, optional `_routing`, and a JSON-ready document
  payload or typed columns used by the NDJSON writer;
- no unresolved business ambiguity.

## TSV to Parquet

Use the schema catalog. Do not infer production schemas from TSV samples.

Conversion requirements:

- decode TSV with the same escaping contract used by extraction;
- parse Oracle types deliberately;
- reject records to a structured reject file with table, chunk, row ordinal,
  column, raw value, and reason;
- write Parquet with compression, normally ZSTD unless benchmark says otherwise;
- target row groups by measured size, not folklore. A common starting point is
  128-512 MB uncompressed row groups or several hundred thousand rows, then tune.

Keep a row-count equality test:

`sum(tsv rows) == sum(bronze parquet rows) + rejects`

## DuckDB operating posture

On a 256 GB / 48 core / 5 TB SSD host:

- start with `PRAGMA threads=32`;
- start with `PRAGMA memory_limit='160GB'`;
- set `temp_directory` to a fast SSD path with ample free space;
- disable preservation of insertion order when it is not semantically required;
- watch spill volume, CPU saturation, and SSD free space before increasing
  threads or memory.

Do not assume max threads is fastest. Joins can become memory- and spill-bound.

## Join contracts

Every join used to create ES documents must declare:

- left and right datasets;
- join keys and normalized key expressions;
- expected cardinality: one-to-one, one-to-many, many-to-one, optional, required;
- orphan policy;
- duplicate policy;
- tie-breaker/order rule;
- output nesting rule;
- quality thresholds.

Examples:

- Required parent missing: fail stage unless explicitly accepted.
- Optional child missing: emit empty array or omit field according to contract.
- Multiple "current" child rows: fail or choose with a documented tie-breaker.
- Duplicate root keys: fail before gold.

## DuckDB SQL style

- Use `CREATE TABLE AS` or `COPY (...) TO` for materialized checkpoints.
- Avoid one giant SQL script for the whole migration. Compose named views/tables
  per business step.
- Keep all normalization expressions in versioned SQL files or generated SQL from
  contracts.
- Use `EXPLAIN` on large joins and record plans for risky transformations.
- Pre-aggregate one-to-many children before joining to roots when that reduces
  explosion.
- For nested ES arrays, build deterministic ordered child lists before JSON
  emission.

## Document shaping

Prefer gold Parquet rows that are still typed rather than giant JSON strings,
unless JSON construction inside DuckDB has been benchmarked and tested. A typed
gold row makes validation easier:

- `_id`
- `_routing`
- document type/version
- scalar fields
- child arrays as structured/list fields or a validated JSON fragment
- lineage fields, if allowed

The NDJSON writer can then serialize with a strict JSON writer and enforce size
limits per document.

## Reproducibility

For every transformation output, write a manifest:

- input dataset paths and hashes;
- SQL/contract version hash;
- DuckDB version;
- PRAGMA settings;
- started/ended timestamps;
- row counts;
- key distinct counts;
- rejects;
- quality report path.

If any input, contract, or code changes, produce a new output path.

## Performance triage

When a transformation is slow:

1. Check whether the join is exploding rows.
2. Check whether keys need normalization/materialization before joining.
3. Check whether the dataset can be partitioned by document root key.
4. Check spill size and memory limit.
5. Check whether a smaller projection reduces I/O.
6. Check whether pre-aggregation of children avoids a large intermediate.
7. Only then tune thread count and Parquet row group size.
