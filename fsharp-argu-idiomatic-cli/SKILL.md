---
name: argu-cli
description: >-
  Build an idiomatic F# command-line interface with Argu — the declarative,
  DU-driven CLI parser. Use this whenever the task involves turning an F# app
  into a CLI, designing a command/subcommand surface, parsing argv, wiring an
  EntryPoint, exit codes, --help/usage text, or sourcing config from
  appSettings/environment variables in F#. Trigger on any mention of Argu,
  "F# CLI", ArgumentParser, ParseResults, console app entry point, argv parsing,
  or "add a command line to my F# pipeline/tool" — even when Argu is not named
  by name. Prefer this over System.CommandLine / Spectre.Console.Cli /
  CommandLineParser for F#; those are C#-idiom and must be flagged. Embodies
  parse-don't-validate: argv is the dirtiest input in the system, and the CLI
  is the boundary that turns it into domain types.
---

# Argu — idiomatic F# CLI

## The one idea

**The argument DU *is* the command surface, and parsing it is parse-don't-validate
applied to `argv`.** `argv : string[]` is the rawest untyped input a program ever
takes. Argu turns a discriminated union into a parser by reflection; you then map
that parser's output into *domain* types at the edge, so nothing downstream ever
sees a stringly-typed flag. The DU doubles as a machine-readable capability
manifest — for a human reading `--help`, and for an agent reading the `.fsi`.

This is the same discipline as any other typed boundary (Oracle→ES, refined types):
**clean the input at the door; prove well-formedness in the type; never re-check
downstream.**

## When to use / not use

Use Argu for any F# console entry point: tools, pipeline runners, ops utilities,
anything with `[<EntryPoint>] let main argv`. It is the idiomatic choice and the
one that keeps the whole program in one type system.

Do **not** reach for the C#-idiom parsers in F# — flag them with ⚠️:
- ⚠️ **System.CommandLine** (GA since .NET 10, genuinely good for AOT/native + shell
  completions) — but binding-by-convention + handler delegates; in F# you wrap it
  and rebuild Argu's ergonomics by hand. Use *only* when you need native-AOT publish
  or real tab-completion, which a scheduled `pipeline.exe` does not.
- ⚠️ **Spectre.Console.Cli** — attribute + DI + settings-class model. Un-idiomatic.
  (`Spectre.Console` *without* `.Cli` is excellent for output/render — tables,
  progress bars. Good pairing: Argu for input, Spectre for render.)
- ⚠️ **CommandLineParser** — attributes on a mutable POCO. The C#-iest of the lot. Skip.

## Setup

`netstandard2.0` package; runs clean on .NET 6/8/9/10.

```bash
dotnet add package Argu
```

```fsharp
open Argu
```

## Canonical pattern (memorize this shape)

A worked ETL CLI — `pipeline run …` and `pipeline bulk-load …`. Reuse this skeleton.

```fsharp
open Argu

// --- leaf subcommand arg DUs ---------------------------------------------
type RunArgs =
    | [<Mandatory; AltCommandLine("-c")>] Config of path: string
    | [<AltCommandLine("-n")>]            Dry_Run
    | From_Scn of scn: int64
    interface IArgParserTemplate with
        member this.Usage =
            match this with
            | Config _   -> "path to the pipeline config json"
            | Dry_Run    -> "plan only; emit no BulkOps"
            | From_Scn _ -> "resume CDC from this Oracle SCN"

type BulkLoadArgs =
    | [<Mandatory>]            Source of table: string
    | [<AltCommandLine("-w")>] Wave_Bytes of int
    interface IArgParserTemplate with
        member this.Usage = function
            | Source _     -> "fully-qualified Oracle source table"
            | Wave_Bytes _ -> "byte budget per bulk wave (default 8MB)"

// --- top-level command DU (subcommands via CliPrefix.None) ----------------
type CliArgs =
    | [<CliPrefix(CliPrefix.None)>] Run       of ParseResults<RunArgs>
    | [<CliPrefix(CliPrefix.None)>] Bulk_Load of ParseResults<BulkLoadArgs>
    | [<AltCommandLine("-v"); Inherit>] Verbose
    interface IArgParserTemplate with
        member this.Usage = function
            | Run _       -> "run the realtime CDC path"
            | Bulk_Load _ -> "run a bounded bulk load"
            | Verbose     -> "enable verbose logging (inherited by subcommands)"
```

`CliPrefix(CliPrefix.None)` makes the case a bare subcommand word (`run`) rather than
a `--run` flag. `Inherit` lets `Verbose` be supplied to any subcommand. The `.Usage`
strings *are* the help text — there is no separate help to maintain.

## The seam: map the DU into your domain *immediately*

This is the whole point. Do not pass `ParseResults` into your core. Convert each
subcommand's results into a domain value that *proves* the args were well-formed.
Use `PostProcessResult` so failures format like native Argu errors:

```fsharp
// edge: Argu DU -> domain DU. Smart constructors, not raw strings.
let toRunSpec (r: ParseResults<RunArgs>) : RunSpec =
    { Config     = r.PostProcessResult(<@ Config @>, ConfigPath.parseOrRaise)
      DryRun     = r.Contains Dry_Run
      ResumeFrom = r.TryGetResult From_Scn |> Option.map Scn.ofInt64 }
```

`PostProcessResult` runs your validator and, on failure, raises an `ArguParseException`
that the exiter renders with usage — so a bad `--config` reads exactly like a missing
flag. `RunSpec` is now a proof: nothing downstream re-validates. (For a pure-`Result`
core instead of raising, see `references/api.md` → "Result at the boundary".)

## FC/IS EntryPoint — the imperative shell, and nothing more

```fsharp
[<EntryPoint>]
let main argv =
    let parser =
        ArgumentParser.Create<CliArgs>(
            programName = "pipeline",
            errorHandler = ProcessExiter(colorizer =
                function ErrorCode.HelpText -> None | _ -> Some ConsoleColor.Red))

    // raiseOnUsage=false: '--help' is not an error; we handle it as exit 0.
    let res = parser.ParseCommandLine(argv, raiseOnUsage = false)
    if res.IsUsageRequested then
        printfn "%s" (parser.PrintUsage()); 0
    else
        match res.GetSubCommand() with
        | Run a       -> a |> toRunSpec      |> Core.run      |> exitOf
        | Bulk_Load a -> a |> toBulkLoadSpec |> Core.bulkLoad |> exitOf
        | Verbose     -> printfn "%s" (parser.PrintUsage()); 1   // no bare subcommand

// the ONLY effects: argv in, int out. Core stays pure and returns Result.
and exitOf : Result<RunSummary, PipelineError> -> int = function
    | Ok summary -> eprintfn "%s" (Lineage.render summary); 0
    | Error e    -> eprintfn "%s" (PipelineError.render e); 1
```

Three layers, one language: **argv → typed spec (edge) → pure core (`Result`) →
exit code (shell).** The `ProcessExiter` formats parse/usage errors and exits with the
right code; it lives at the process boundary where effects belong. Your *domain*
errors travel as `Result` and funnel to an exit code in `exitOf`. That split — Argu's
exiter for malformed *input*, your `Result` for failed *work* — is the idiomatic line.

## Best practices (the officer's checklist)

- **Model absence in types, not defaults.** Prefer `TryGetResult |> Option.map` over
  `GetResult(..., defaultValue = …)`. An optional flag is an `option` in the spec, not
  a magic sentinel. Use `GetResult` only when the arg is `Mandatory` (so it can't be absent).
- **One DU per command level.** Leaf args → leaf DU; the command set → top DU of
  `ParseResults<_>` cases. Never flatten subcommands into one giant flag soup.
- **Validate at the edge with `PostProcessResult`/`TryPostProcessResult`**, feeding smart
  constructors (`ConfigPath.parse`, `Scn.ofInt64`). Past the edge, types are proofs.
- **`raiseOnUsage = false`** so `--help` is a normal exit-0 path, not an exception.
- **Let the exiter format input errors; keep domain errors in `Result`.** Don't try/catch
  `ArguParseException` deep in the core — that's mixing the two error models.
- **Expose `.fsi` signatures** for the arg modules: the signature file is the disclosure
  summary (an agent learns the surface without the bodies); the `.fs` is the detail.
- **Subcommand help is free** — every subcommand's `Parser.PrintUsage()` works; no manual
  help strings beyond the `.Usage` members.

## Anti-patterns to flag (⚠️)

- ⚠️ **Stringly-typed flow past the parse boundary** — the cardinal sin. If a `string`
  flag value reaches your core unconverted, the seam failed.
- ⚠️ **Mutable settings/POCO binding** (CommandLineParser / Spectre.Cli style) — defeats
  parse-don't-validate; absence becomes `null`, validation becomes runtime.
- ⚠️ **`GetResult` with defaults everywhere** — hides optionality the type should carry.
- ⚠️ **Catching `ArguParseException` in domain code** — let it surface to the exiter at
  the edge; convert to `Result` only if you deliberately want a pure boundary (see api.md).
- ⚠️ **Passing `ParseResults<_>` into the core** — couples the domain to the CLI library.
  Map to a domain spec first.

## Reference files

Read these as needed — they are the nuts-and-bolts detail under the pattern above:

- **`references/attributes.md`** — the complete attribute catalog (`Mandatory`,
  `AltCommandLine`, `CliPrefix`, `Unique`, `ExactlyOnce`, `First`/`Last`, `Inherit`,
  `EqualsAssignment` family, `MainCommand`, `Rest`, `Hidden`, `GatherUnrecognized`,
  `CustomCommandLine`, `AppSettings`/`CustomAppSettings`, `NoCommandLine`,
  `GatherAllSources`). Read when choosing how to shape a specific arg.
- **`references/api.md`** — `ArgumentParser` construction, `Parse`/`ParseCommandLine`/
  `ParseConfiguration`, the full `ParseResults` query API, `PostProcessResult`,
  exiters (`ProcessExiter`/`ExceptionExiter`/custom `IExiter`), `ArguParseException`/
  `ErrorCode`, help/usage rendering, and "Result at the boundary". Read when wiring
  parsing, errors, exit behavior, or pure-Result conversion.
- **`references/integration.md`** — config sources (appSettings, env vars,
  `ConfigurationReader`, precedence/merging), testing the parser (incl. property-based),
  and a complete end-to-end ETL CLI program tying it all together. Read when sourcing
  config beyond argv, writing tests, or wanting the full assembled example.
