---
name: fsharp-oracle-data-access
description: >
  Choose and write the correct F# data-access path against Oracle: Donald for
  explicit reads/commands, Dapper.Oracle for provider-specific features
  (array binding, RefCursor, LOB/Fetch tuning), or a raw Oracle.ManagedDataAccess
  reader for billion-row streaming scans. Use this skill WHENEVER an F# task
  touches Oracle persistence — reading rows into records, bulk insert/upsert/MERGE,
  calling PL/SQL packages, streaming a large extract, or deciding between Donald /
  Dapper / raw ADO / EF. Trigger even when the user only says "query Oracle from
  F#", "bulk load", "stream the table", "call the stored proc", or names one of
  Donald, Dapper, Dapper.Oracle, ODP.NET, OracleDataReader, FetchSize. Defaults to
  Functional Core / Imperative Shell discipline and rejects EF Core.
---

# F# ⇄ Oracle Data Access

Picking the right tool per IO shape, with the boundary kept pure. This is the
Imperative Shell: `async`, exceptions, and provider quirks live **here** so the
core stays deterministic (load → decide → apply).

> The core never imports a data-access library. It receives plain records and
> returns a decision DU. Everything below is Shell.

---

## 0. Non-negotiables (the F# law)

1. **Records are immutable.** No `[<CLIMutable>]`, no mutable members, no
   settable-property POCOs to satisfy a mapper. If a tool forces that → ⚠️ wrong tool.
2. **No EF Core.** Change tracker = hidden mutable state; `SaveChanges()` = the
   Black Box; lazy load = IO leaking through field access; no `FetchSize`; DUs
   don't map; `option` needs converters. It is the anti-pattern. Banned. ⚠️
3. **Result over exceptions — at the Shell boundary.** Underlying libs may throw;
   you catch once at the edge and return `Result<'T, DbError>`. The core sees no `exn`.
4. **`buffered: false` / `*Unbuffered*` for anything unbounded.** A buffered query
   over a large table is an OOM, not a query.
5. **Oracle binds by position by default.** Multi-param or array? Set `BindByName`
   (Dapper.Oracle) or keep param order identical to SQL. This is the #1 silent bug. ⚠️
6. **`option ↔ NULL` must be wired explicitly** (see §5). Unwired = runtime cast blow-up.

---

## 1. The decision tree

```
Need to touch Oracle from F#?
│
├─ Writing the CORE domain logic?
│     → STOP. No data access here. Return a decision DU; let the Shell run it.
│
├─ Reading rows → records, or running a parameterised command?
│     → DONALD  (§2)  — explicit reader, SequentialAccess by default, zero reflection.
│        Default choice. Most aligned with the law.
│
├─ Need an Oracle PROVIDER feature?
│     ├─ Bulk DML in one round trip (insert/upsert/MERGE of N rows)
│     │     → DAPPER.ORACLE  (§3)  — OracleDynamicParameters + ArrayBindCount.
│     ├─ PL/SQL package returning a REF CURSOR
│     │     → DAPPER.ORACLE  (§3)  — RefCursor output param.
│     └─ LOB / fetch knobs on a normal query
│           → DAPPER.ORACLE  (§3)  — LOBFetchSize, BindByName.
│
├─ Scanning a BILLION rows (full extract / CDC bulk path)?
│     → RAW ODP.NET READER  (§4)  — FetchSize-tuned, SequentialAccess,
│        true IAsyncEnumerable. The only path that gives FetchSize control.
│
└─ Want a TYPE-SAFE query builder (and accept codegen)?
      → SqlHydra.Oracle  (§8)  — the only F# builder that speaks Oracle.
         Optional. Donald + raw reader remain the spine.
```

One-line rule of thumb: **Donald by default, Dapper.Oracle for provider features,
raw reader for the billion-row stream, EF never.**

---

## 2. Donald — the default read / command path

Explicit `IDataReader → 'T` mapping. No reflection, no "property must match column"
runtime surprise. Donald consumes the reader with `CommandBehavior.SequentialAccess`
by default (forward-only streaming) and throws typed exceptions
(`DbExecutionException`, `DbReaderException`) — caught once at the edge.

```fsharp
open System.Data
open Donald
open Oracle.ManagedDataAccess.Client

type Customer =
    { Id: int64; Name: string; Email: string option; Scn: int64 }
    // The boundary is a proof: parse-don't-validate, column by column.
    static member ofReader (rd: IDataReader) : Customer =
        { Id    = rd.ReadInt64       "ID"        // Oracle returns UPPERCASE
          Name  = rd.ReadString      "NAME"
          Email = rd.ReadStringOption "EMAIL"     // NULL-safe, no converter needed
          Scn   = rd.ReadInt64       "SCN" }

// many
let getActive (conn: OracleConnection) : Customer list =
    conn
    |> Db.newCommand "SELECT id, name, email, scn FROM customer WHERE active = 1"
    |> Db.query Customer.ofReader            // throws on failure — wrap at the edge (§5)

// one
let byId (conn: OracleConnection) (id: int64) : Customer option =
    conn
    |> Db.newCommand "SELECT id, name, email, scn FROM customer WHERE id = :id"
    |> Db.setParams [ "id", SqlType.Int64 id ]   // single param ⇒ position-safe
    |> Db.querySingle Customer.ofReader

// command (no result)
let touch (conn: OracleConnection) (id: int64) : unit =
    conn
    |> Db.newCommand "UPDATE customer SET seen = SYSDATE WHERE id = :id"
    |> Db.setParams [ "id", SqlType.Int64 id ]
    |> Db.exec
```

⚠️ Donald is a generic ADO wrapper: it does not flip `BindByName`. With **multiple**
named params, either list them in SQL order or move to Dapper.Oracle for explicit
`BindByName`. Aliasing in `SELECT` (`id AS Id`) is optional with Donald because you
name the columns yourself in `ofReader`.

---

## 3. Dapper.Oracle — provider-specific shell

Reach for this only when you need an Oracle feature Donald/plain-Dapper can't express.
`OracleDynamicParameters` exposes `ArrayBindCount`, `BindByName`, `LOBFetchSize`,
RefCursor, and array binding.

### 3a. Bulk upsert — true array bind (one round trip, not a per-row loop)

This is the fix for plain Dapper's trap: `conn.Execute(sql, seq)` loops **one execute
per row**. `ArrayBindCount` batches N rows in a single statement execution.

```fsharp
open Dapper
open Dapper.Oracle
open Oracle.ManagedDataAccess.Client

let mergeSql =
    "MERGE INTO customer t
     USING (SELECT :Id id, :Name name, :Scn scn FROM dual) s
     ON (t.id = s.id)
     WHEN MATCHED THEN UPDATE SET t.name = s.name, t.scn = s.scn
        WHERE s.scn > t.scn                       -- SCN guard ⇒ idempotent replay
     WHEN NOT MATCHED THEN INSERT (id, name, scn) VALUES (s.id, s.name, s.scn)"

let bulkUpsert (conn: OracleConnection) (rows: Customer[]) : Task<int> =
    let p = OracleDynamicParameters()
    p.ArrayBindCount <- rows.Length               // ← the lever
    p.BindByName     <- true                      // ← required for :named multi-param
    p.Add("Id",   rows |> Array.map (fun r -> r.Id))
    p.Add("Name", rows |> Array.map (fun r -> r.Name))
    p.Add("Scn",  rows |> Array.map (fun r -> r.Scn))
    conn.ExecuteAsync(mergeSql, p)
```

Feed it from the streaming source (§4) via byte-budget chunks:
`scan ... |> TaskSeq.chunkBySize budget |> ... bulkUpsert`.

### 3b. PL/SQL package returning a REF CURSOR

```fsharp
let fromPackage (conn: OracleConnection) : Task<Customer seq> =
    let p = OracleDynamicParameters()
    p.Add("p_cursor", dbType = OracleMappingType.RefCursor,
                      direction = ParameterDirection.Output)
    conn.QueryAsync<Customer>("pkg_customer.get_active", p,
                              commandType = CommandType.StoredProcedure)
```

⚠️ `QueryAsync` here is **buffered**. Only acceptable for bounded result sets.
For an unbounded cursor, stream instead (§4) or use `QueryUnbufferedAsync`.

---

## 4. Raw ODP.NET reader — the billion-row streaming scan

The only path with `FetchSize` control. This is what the bulk extract / CDC path uses.
Produces a true `IAsyncEnumerable<'T>` so the downstream chunker gets backpressure:
the reader only advances as the sink pulls.

```fsharp
open System.Data
open System.Threading
open Oracle.ManagedDataAccess.Client
open FSharp.Control                                 // FSharp.Control.TaskSeq

let scan (conn: OracleConnection) (sql: string) (ct: CancellationToken)
        : IAsyncEnumerable<Customer> =
    taskSeq {
        use cmd = new OracleCommand(sql, conn)
        cmd.FetchSize <- 16L * 1024L * 1024L         // 16 MB array fetch, NOT 128 KB default
        // precise alt (after open): reader.FetchSize <- reader.RowSize * int64 rowsPerTrip
        use! reader = cmd.ExecuteReaderAsync(CommandBehavior.SequentialAccess, ct)
        let mutable go = true
        while go do
            let! has = reader.ReadAsync(ct)
            if has then
                yield { Id    = reader.GetInt64 0     // typed getters, zero boxing
                        Name  = reader.GetString 1
                        Email = if reader.IsDBNull 2 then None else Some (reader.GetString 2)
                        Scn   = reader.GetInt64 3 }
            else go <- false
    }
```

**Why FetchSize dominates:** ODP.NET default fetch is ~128 KB; at a billion rows that is
an enormous number of network round-trips. Raising it to 8–32 MB amortises round-trips
and is the single biggest throughput knob. Dapper hides the `OracleCommand`, so you can
only set it by owning the command — i.e. here.

⚠️ ODP.NET managed `async` has historically been partly sync-over-async; on a
throughput-bound full scan this barely matters (you saturate anyway), but don't expect
SqlClient-grade thread yielding.

---

## 5. Cross-cutting Oracle laws

**Param prefix:** Oracle uses `:name`, never `@name`. ⚠️ Copy-pasting SQL-Server SQL
silently breaks binding.

**BindByName:** default is positional. Set it true for any multi-param/array case
(Dapper.Oracle exposes it; plain Dapper and Donald do not). Otherwise SQL order must
match param-add order.

**option ↔ NULL:** Donald handles it via `ReadStringOption` etc. If you keep any *plain*
Dapper in the codebase, register once at startup:
```fsharp
Dapper.FSharp.OptionTypes.register()   // global NULL ⇄ option for plain Dapper too
```

**Column case:** Oracle returns `UPPERCASE`. With Donald you name columns in `ofReader`
(no issue). With Dapper constructor-mapping, alias to the record field: `SELECT id AS Id`.

**Error model — catch once, return Result:**
```fsharp
type DbError = Timeout | Transient of string | Fatal of exn

let private classify (ex: OracleException) =
    match ex.Number with
    | 12170 | 3135 | 3113 -> Transient ex.Message     // timeout / lost connection
    | _                   -> Fatal (ex :> exn)

let tryDb (op: unit -> Task<'T>) : Task<Result<'T, DbError>> = task {
    try        let! r = op () in return Ok r
    with
    | :? OracleException as ex         -> return Error (classify ex)
    | :? DbExecutionException as ex    -> return Error (Fatal ex)   // Donald
    | :? TaskCanceledException         -> return Error Timeout
}
```
The core consumes `Result`/decision DUs; it never sees a raw `exn`.

---

## 6. Anti-patterns — ⚠️ stop if you see these

- `entity.Update(); context.SaveChanges()` → EF Black Box. Out. (Whole library out.)
- `conn.QueryAsync(sql)` over a large/unbounded set → buffered list → OOM.
  Use `QueryUnbufferedAsync` or the raw reader.
- `conn.Execute(sql, rowSeq)` for bulk → silent per-row loop. Use `ArrayBindCount`.
- `reader["col"]` / `reader.GetValue n` in a hot loop → boxing. Use typed getters.
- `[<CLIMutable>]` records, settable props, parameterless ctors → mapper appeasement
  in F#. The wrong tool is forcing your model. Reconsider the tool.
- `@param` in Oracle SQL → wrong prefix; use `:param`.
- `try/catch` inside core domain logic → IO leaked into the core. Move it to the edge.

---

## 7. Quick reference

| Need | Tool | Key API |
|---|---|---|
| Read rows → records | Donald | `Db.newCommand` → `Db.query ofReader` |
| Single row | Donald | `Db.querySingle` |
| Param command | Donald | `Db.setParams [ "id", SqlType.Int64 id ]` |
| Bulk insert/upsert/MERGE | Dapper.Oracle | `OracleDynamicParameters` + `ArrayBindCount` + `BindByName` |
| REF CURSOR / PL-SQL pkg | Dapper.Oracle | `OracleMappingType.RefCursor`, `CommandType.StoredProcedure` |
| Billion-row scan | raw ODP.NET | `OracleCommand.FetchSize` + `taskSeq` + typed getters |
| Streaming (bounded-ish) | plain Dapper | `QueryUnbufferedAsync<'T>` → `IAsyncEnumerable` |
| option ↔ NULL (plain Dapper) | Dapper.FSharp | `OptionTypes.register()` once |
| Typed query builder | SqlHydra.Oracle | codegen + query CE (§8) |
| ORM / change tracking | — | ⚠️ none. EF is banned. |

---

## 8. Optional escape hatch — SqlHydra.Oracle

The only F# query-builder ecosystem that supports Oracle: a CLI generates records from
the schema, and `SqlHydra.Query` gives a composable, type-safe query CE over Dapper.
Use it when you want compile-checked column references and accept a codegen step.
It does **not** replace the raw reader for FetchSize-tuned billion-row scans, and it
does **not** loosen any rule in §0. Donald + Dapper.Oracle + raw reader remain the spine.
