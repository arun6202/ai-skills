---
name: etl-source-basis-sota
description: >-
  Reference compass for applying data-engineering and data-intensive-system
  principles to the Oracle 19c to Elasticsearch ETL. Use when reviewing design
  decisions, tradeoffs, or governance against lifecycle thinking, reliability,
  scalability, maintainability, derived data, and vendor guidance.
---

# ETL Source Basis SOTA

Use this as a compact decision compass when the design gets fuzzy.

## From data engineering lifecycle thinking

Apply the whole lifecycle, not just code:

- generation/source system: Oracle semantics, keys, SCN, consistency, privileges;
- storage: immutable raw TSV, typed Parquet, versioned outputs;
- ingestion: chunking, retry, durability, throughput, source safety;
- transformation: explicit contracts, join cardinality, repeatable SQL;
- serving: Elasticsearch mapping, query behavior, aliases, cutover;
- undercurrents: security, governance, orchestration, DataOps, observability.

Practical implication: a fast loader without contracts, reconciliation, and
operational runbooks is not production-ready.

## From data-intensive systems thinking

Use tradeoffs explicitly:

- reliability: every stage is restartable and every output is verifiable;
- scalability: partition work by chunks/files/docs, benchmark bottlenecks, avoid
  central mutable state;
- maintainability: keep business rules in contracts and small named transforms;
- derived data: Elasticsearch is a derived serving view, so rebuildability and
  lineage matter more than pretending it is canonical;
- observability: derived state must be inspectable from source to index.

Practical implication: favor deterministic rebuilds and alias cutover over
manual mutation of a live index.

## Vendor-grounded reminders

Oracle 19c:

- use explicit column lists and bind variables;
- coordinate snapshot/SCN and parallelism with the DBA;
- use chunking deliberately, including DBMS_PARALLEL_EXECUTE concepts when
  useful for ROWID or key-range task planning;
- remember that source consistency and undo pressure are operational limits.

DuckDB/Parquet:

- use typed Parquet as the workhorse format;
- set thread, memory, and temp directory deliberately;
- benchmark row group size/compression with real data;
- materialize checkpoints between major transformations.

Elasticsearch:

- use bulk requests, not single-document indexing;
- benchmark bulk request size and worker count;
- keep bulk requests below HTTP request limits and usually in the tens of MB;
- parse per-item bulk responses;
- use backoff on 429/rejections;
- disable refresh and replicas only for controlled initial loads and restore them;
- use explicit mappings and alias cutover.

## Questions Claude should ask early

- What is the required consistency point across the 50 Oracle tables?
- Which table or entity is the root for each ES document type?
- What deterministic `_id` rule is acceptable?
- Which joins are required versus optional?
- How should null, empty string, tabs/newlines, and LOBs be represented?
- What are the ES query patterns that drive mapping and nested/object choices?
- What data is sensitive and should never reach Elasticsearch?
- What downtime/cutover/rollback constraints exist?

If these are unanswered, implementation can proceed only on scaffolding, not on
business transformation logic.
