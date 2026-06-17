---
name: elasticsearch-ndjson-bulk-load-sota
description: >-
  Elasticsearch bulk indexing skill for loading about 110 million documents
  from Parquet/gold datasets through NDJSON. Covers index design, mappings,
  aliases, document IDs, routing, NDJSON format, bulk sizing, concurrency,
  backpressure, retries, rejects, refresh/replica settings, verification, and
  cutover.
---

# Elasticsearch NDJSON Bulk Load SOTA

Use this skill for:

`gold ES document rows -> bulk NDJSON files -> Elasticsearch index -> alias cutover`

Elasticsearch is the serving system, not the source of truth. The source of
truth is Oracle plus immutable ETL artifacts and manifests.

## Index design first

Before loading:

- define index names and aliases;
- create explicit mappings and settings;
- disable or tightly constrain dynamic mapping;
- choose shard count from expected index size, query pattern, and cluster size;
- define analyzers/normalizers before data lands;
- decide refresh interval and replica policy for initial load;
- define rollback: normally keep old index behind read alias until validation.

Load into a new versioned index, then atomically switch the read/write alias.
Avoid in-place mutation of a live search index for the initial 110M-document
build.

## Document ID rule

Choose `_id` deliberately:

- Auto-generated IDs are faster for pure one-shot ingestion.
- Deterministic IDs are safer for resumability, idempotence, audit, and reloads.

For this ETL, deterministic IDs are usually worth the indexing cost. Build them
from the document contract, for example a stable business key or canonical hash
of root entity keys. Never use ROWID as document identity.

If custom routing is used, it must be contract-defined and tested for shard
balance. Bad routing creates hot shards.

## NDJSON format

Bulk files must be strict NDJSON:

- action metadata line;
- source document line;
- repeat;
- final newline at end of file;
- `Content-Type: application/x-ndjson`;
- no pretty-printed JSON;
- no embedded raw newlines outside JSON string escaping.

Example shape:

```json
{"index":{"_index":"my-index-v001","_id":"doc-123","routing":"tenant-7"}}
{"field":"value","items":[{"x":1}]}
```

Use a streaming JSON writer. Do not concatenate strings by hand.

## Bulk file sizing

There is no universal best number of docs per bulk request. Benchmark with the
real document shape:

1. Start small: 5-10 MB request bodies or a few thousand docs.
2. Increase until throughput plateaus.
3. Stay below Elasticsearch's HTTP request limit, commonly 100 MB by default.
4. Prefer "a few tens of MB" over huge requests to avoid memory pressure.

Separate file size from request size. A large NDJSON file can be split into many
bulk HTTP requests.

## Loader behavior

The loader must:

- stream from NDJSON or gold Parquet without loading a whole file in memory;
- maintain bounded in-flight requests;
- increase concurrency gradually;
- parse every bulk response item;
- retry transient failures with randomized exponential backoff;
- slow down immediately on 429/rejections;
- write permanent failures to a reject file with action metadata, source path,
  document ID, status, error type, reason, and retry count;
- checkpoint request offsets so a run can resume.

Do not treat HTTP 200 as success. Bulk responses can contain per-document errors.

## Initial-load index settings

For a rebuild where data is durable elsewhere:

- set replicas to `0` during initial load if the risk is accepted;
- set `refresh_interval=-1` during the load when search visibility is not needed;
- restore replicas and refresh interval after load;
- wait for the cluster to recover to the desired health;
- consider force merge only after final load and only if the operational cost is
  acceptable.

Never leave the production index in load-only settings after cutover.

## Validation

Before cutover:

- expected doc count equals ES `_count`;
- sample deterministic IDs fetch the expected documents;
- key field distributions match gold reports;
- mappings are stable, no unexpected dynamic fields appeared;
- rejected docs are zero or explicitly accepted by business/data owners;
- search smoke tests pass against the alias candidate;
- shard sizes and indexing/search latency are acceptable.

## Cutover

Preferred flow:

1. Create `index-vNNN` with mappings/settings.
2. Bulk load.
3. Restore index settings.
4. Validate counts, samples, and searches.
5. Atomically move read alias from old index to new index.
6. Keep old index until signoff and rollback window expire.

If updates must continue after initial load, design a separate CDC or delta load
contract. Do not blur a full rebuild process into an implicit incremental system.
