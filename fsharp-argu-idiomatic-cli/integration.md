# Argu integration — config sources, testing, full example

## Table of contents
1. Configuration sources & precedence
2. Environment variables
3. appSettings / nested keys
4. Custom configuration readers
5. Testing the parser (incl. property-based)
6. Full end-to-end ETL CLI

---

## 1. Configuration sources & precedence

The *same* argument DU can be sourced from argv **and** a configuration reader. With
`parser.Parse(argv, configurationReader = reader)`, results are **merged with command-line
args overriding** configuration values — argv wins. Mark a case `GatherAllSources` to
collect from every source instead of letting CLI override, or `NoCommandLine` to source a
case *only* from configuration (good for secrets you don't want on argv).

```fsharp
let parser = ArgumentParser.Create<Args>(programName = "rutta")
let results = parser.Parse(argv, configurationReader = reader)   // argv overrides reader
```

Precedence summary: **command line > configuration reader > (defaults you supply in code)**,
unless `GatherAllSources` opts a case out of override.

## 2. Environment variables

```fsharp
let reader = EnvironmentVariableConfigurationReader() :> IConfigurationReader
let results = parser.Parse(argv, configurationReader = reader)
```
The reader looks up environment variables by the argument's config key. Combine with
`CustomAppSettings "MY_KEY"` to control the exact variable name. Pattern: ops sets
`PIPELINE_CONFIG` in the environment; a developer overrides with `--config` on the CLI.

## 3. appSettings / nested keys

`ConfigurationReader.FromAppSettings(assembly)` sources from the process's
`app.config`/`appSettings`. Default key derivation matches the arg name; use
`CustomAppSettings` with **colon-separated** paths for nested keys:

```fsharp
type Args =
    | [<CustomAppSettings "credentials:username">] Username of string
    | [<CustomAppSettings "credentials:password"; NoCommandLine>] Password of string
```
```json
{ "credentials": { "username": "johndoe", "password": "p455w0rd" } }
```
(For full `Microsoft.Extensions.Configuration` / hosted-app integration there's the
`Argu.MicrosoftExtensions` package, which injects `ParseResults<'T>` into DI and reads from
`appSettings.json`. Use it only if you're already in a generic-host app; otherwise plain
readers are simpler.)

## 4. Custom configuration readers

`IConfigurationReader` is tiny — `Name: string` and `GetValue: string -> string`. Build one
from a function for tests or bespoke sources:

```fsharp
let reader = ConfigurationReader.FromFunction(fun key ->
    match key with
    | "config" -> "prod.json"
    | _        -> null)
let results = parser.Parse(argv, configurationReader = reader)
```
`ConfigurationReader.FromFunction` is the cleanest way to inject a fake config in tests, and
to wire a `.env` or vault lookup without writing a class.

## 5. Testing the parser

Because the DU *is* the surface, tests are pure and fast. Construct the parser with
`ExceptionExiter` so a bad parse raises instead of killing the test host.

```fsharp
let parser = ArgumentParser.Create<CliArgs>(errorHandler = ExceptionExiter())

// happy path: assert the parsed/mapped domain spec
let spec =
    parser.ParseCommandLine([| "run"; "--config"; "prod.json"; "-n" |])
    |> fun r -> match r.GetSubCommand() with Run a -> toRunSpec a | _ -> failwith "expected run"
test <@ spec.DryRun = true @>
test <@ spec.Config = ConfigPath.parseOrRaise "prod.json" @>

// failure path: a missing Mandatory raises ArguParseException
raises<ArguParseException> <@ parser.ParseCommandLine([| "run" |]) @>
```

### Property-based (FsCheck) — round-trip the surface
Generate domain specs, render them back to an argv, parse, and assert you recover the spec.
This pins the *isomorphism* between your spec type and its CLI encoding — the same round-trip
discipline used for ETL validation, applied to the command surface:

```fsharp
let ``run spec round-trips through argv`` (spec: RunSpec) =
    let argv = RunSpec.toArgv spec               // your encoder: spec -> string[]
    let parsed =
        parser.ParseCommandLine(Array.append [| "run" |] argv)
        |> fun r -> match r.GetSubCommand() with Run a -> toRunSpec a | _ -> failwith "run"
    parsed = spec
// Check.QuickThrowOnFailure ``run spec round-trips through argv``
```
Constrain generators so `RunSpec` only contains values your encoder can represent (e.g. SCNs
≥ 0); that constraint belonging in the *generator* is itself a parse-don't-validate signal.

## 6. Full end-to-end ETL CLI

The whole thing assembled — arg DUs, the edge mapping, the FC/IS EntryPoint. Drop-in
skeleton for an Oracle→ES pipeline runner.

```fsharp
module Pipeline.Cli

open System
open Argu

// ---- domain (smart constructors elsewhere) -------------------------------
type ConfigPath = private ConfigPath of string
module ConfigPath =
    let parse (s: string) =
        if IO.File.Exists s then Ok (ConfigPath s) else Error $"no such file: {s}"
    let parseOrRaise s = match parse s with Ok p -> p | Error e -> failwith e

type Scn = Scn of int64
module Scn = let ofInt64 (n: int64) = Scn n

type RunSpec      = { Config: ConfigPath; DryRun: bool; ResumeFrom: Scn option }
type BulkLoadSpec = { Source: string; WaveBytes: int }
type RunSummary   = { Rows: int64 }
type PipelineError = Failed of string
module PipelineError = let render (Failed m) = $"pipeline error: {m}"
module Lineage      = let render (s: RunSummary) = $"ok: {s.Rows} rows"

// ---- pure core (returns Result; no effects beyond what you inject) --------
module Core =
    let run (s: RunSpec)      : Result<RunSummary, PipelineError> = Ok { Rows = 0L }
    let bulkLoad (s: BulkLoadSpec) : Result<RunSummary, PipelineError> = Ok { Rows = 0L }

// ---- CLI surface ----------------------------------------------------------
type RunArgs =
    | [<Mandatory; AltCommandLine("-c")>] Config of path: string
    | [<AltCommandLine("-n")>]            Dry_Run
    | From_Scn of scn: int64
    interface IArgParserTemplate with
        member this.Usage = function
            | Config _   -> "path to the pipeline config json"
            | Dry_Run    -> "plan only; emit no BulkOps"
            | From_Scn _ -> "resume CDC from this Oracle SCN"

type BulkLoadArgs =
    | [<Mandatory>]            Source of table: string
    | [<AltCommandLine("-w")>] Wave_Bytes of int
    interface IArgParserTemplate with
        member this.Usage = function
            | Source _     -> "fully-qualified Oracle source table"
            | Wave_Bytes _ -> "byte budget per bulk wave"

type CliArgs =
    | [<CliPrefix(CliPrefix.None)>] Run       of ParseResults<RunArgs>
    | [<CliPrefix(CliPrefix.None)>] Bulk_Load of ParseResults<BulkLoadArgs>
    | [<Inherit; AltCommandLine("-v")>] Verbose
    interface IArgParserTemplate with
        member this.Usage = function
            | Run _       -> "run the realtime CDC path"
            | Bulk_Load _ -> "run a bounded bulk load"
            | Verbose     -> "verbose logging (inherited by subcommands)"

// ---- edge: ParseResults -> domain spec (parse-don't-validate) -------------
let private toRunSpec (r: ParseResults<RunArgs>) : RunSpec =
    { Config     = r.PostProcessResult(<@ Config @>, ConfigPath.parseOrRaise)
      DryRun     = r.Contains Dry_Run
      ResumeFrom = r.TryGetResult From_Scn |> Option.map Scn.ofInt64 }

let private toBulkLoadSpec (r: ParseResults<BulkLoadArgs>) : BulkLoadSpec =
    { Source    = r.GetResult Source
      WaveBytes = r.GetResult(Wave_Bytes, defaultValue = 8 * 1024 * 1024) }

// ---- imperative shell -----------------------------------------------------
let private exitOf : Result<RunSummary, PipelineError> -> int = function
    | Ok s    -> eprintfn "%s" (Lineage.render s); 0
    | Error e -> eprintfn "%s" (PipelineError.render e); 1

[<EntryPoint>]
let main argv =
    let parser =
        ArgumentParser.Create<CliArgs>(
            programName = "pipeline",
            errorHandler = ProcessExiter(colorizer =
                function ErrorCode.HelpText -> None | _ -> Some ConsoleColor.Red))

    let res = parser.ParseCommandLine(argv, raiseOnUsage = false)
    if res.IsUsageRequested then printfn "%s" (parser.PrintUsage()); 0
    else
        match res.GetSubCommand() with
        | Run a       -> a |> toRunSpec      |> Core.run      |> exitOf
        | Bulk_Load a -> a |> toBulkLoadSpec |> Core.bulkLoad |> exitOf
        | Verbose     -> printfn "%s" (parser.PrintUsage()); 1
```

Invocations this accepts:
```
pipeline run --config prod.json
pipeline run -c prod.json -n --from-scn 90734512
pipeline -v bulk-load --source SCOTT.ORDERS -w 16777216
pipeline run --help          # exit 0, prints run usage
pipeline                     # exit 1, prints top usage (no subcommand)
```
Every value that reaches `Core` is a domain type. The CLI library never crosses the seam.
