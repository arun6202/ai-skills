---
name: etl-data-quality-observability-sota
description: >-
  Data quality, reconciliation, observability, and runbook skill for the Oracle
  19c to Elasticsearch ETL. Use to design checks, manifests, dashboards,
  failure handling, restartability, audit reports, data contracts, and signoff
  gates across raw TSV, Parquet/DuckDB, NDJSON, and Elasticsearch stages.
---

# ETL Data Quality Observability SOTA

Use this skill to make the ETL trustworthy. At this scale, correctness is not a
feeling; it is a trail of manifests, counts, samples, and reconciliations.

## Quality dimensions

Track quality at every stage:

- completeness: expected rows/docs arrived;
- uniqueness: keys and IDs are unique where required;
- validity: values parse and satisfy domain constraints;
- consistency: joins match declared cardinality;
- accuracy: golden samples and source spot checks match;
- timeliness: run stages complete within operational windows;
- lineage: every output can be traced to inputs, contracts, code, and SCN.

## Required reports

Source table report:

- Oracle count;
- TSV count;
- bronze Parquet count;
- rejects;
- chunk count;
- min/max key;
- null counts for critical columns;
- hash/checksum policy result.

Join report:

- left count;
- right count;
- output count;
- unmatched left;
- unmatched right;
- duplicate join keys;
- max child count per root;
- rows dropped by filters with reason.

Document report:

- gold document count;
- distinct `_id` count;
- duplicate `_id` count;
- document size percentiles;
- required-field null/missing count;
- nested array size percentiles;
- mapping compatibility check.

Elasticsearch load report:

- attempted docs;
- successful docs;
- failed docs by status/error type;
- retried docs;
- final `_count`;
- sample fetch validation;
- alias/cutover status.

## Reconciliation math

The pipeline must explain:

`1B source rows across 50 tables -> 110M ES documents`

That ratio is not self-evident. For each document type, record:

- root table and root row count;
- filters applied to roots;
- grouping keys;
- expected documents per root;
- child table rollups;
- reasons rows do not become documents.

If the document count changes after a logic change, the report must say which
contract/rule changed.

## Manifest schema

Every stage output writes a manifest with:

- `run_id`
- `stage`
- `contract_version`
- `code_version`
- `input_paths`
- `input_hashes`
- `output_paths`
- `output_hashes`
- `started_at`
- `ended_at`
- `status`
- `row_count`
- `byte_count`
- `reject_count`
- `metrics_path`
- `errors_path`

Manifests are append-only evidence. Do not edit old manifests except to mark a
documented correction with a new correction record.

## Failure taxonomy

Classify failures:

- retryable infrastructure: network timeout, transient ES 429, temporary file
  lock, Oracle session interruption;
- retryable data chunk: failed chunk with no committed final output;
- permanent data quality: parse error, duplicate key, missing required parent;
- contract error: unspecified null policy, missing mapping, ambiguous join;
- operator error: wrong run id/path/index/alias.

Only retry retryable failures. Permanent data and contract failures require a
decision, not a loop.

## Restart rules

- A stage output is committed only after final file rename and manifest write.
- `.partial` files are never inputs to the next stage.
- A succeeded chunk is not rewritten unless the run is explicitly invalidated.
- Retrying a chunk must produce the same hash for deterministic stages.
- Bulk loader resumes from request/file offsets and still checks duplicate IDs.

## Dashboards and logs

Minimum operational views:

- per-stage throughput rows/sec and MB/sec;
- active chunks and backlog;
- reject rate;
- ES bulk latency, 429 rate, and error mix;
- DuckDB spill/temp usage;
- disk free space;
- Oracle extraction sessions and wait profile if available;
- ETA by stage.

Logs must be structured. Every log event includes `run_id`, `stage`, and
`chunk_id` or document/bulk file identifier.

## Signoff pack

Before production cutover, produce a signoff bundle:

- run manifest summary;
- source-to-bronze reconciliation;
- silver/gold join reports;
- ES load report;
- rejected rows/docs with disposition;
- golden sample results;
- performance summary;
- open risks and accepted deviations;
- rollback instructions.

If a stakeholder cannot answer "why are there 110M docs?" from this pack, the
pipeline is not yet governed.
