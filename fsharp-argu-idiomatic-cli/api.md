# Argu API — parser, results, errors, exiters

## Table of contents
1. Constructing the parser
2. Parse entry points
3. The `ParseResults` query API
4. Post-processing & validation (the seam)
5. Result at the boundary (pure-`Result` core)
6. Exiters (`IExiter`, `ProcessExiter`, `ExceptionExiter`)
7. Errors: `ArguParseException` / `ErrorCode`
8. Help & usage rendering

---

## 1. Constructing the parser

```fsharp
ArgumentParser.Create<'Template>(
    ?programName: string,                 // shown in usage; defaults to process name
    ?helpTextMessage: string,             // banner line above usage
    ?usageStringCharacterWidth: int,      // wrap width for help
    ?errorHandler: IExiter,               // how parse/usage errors are reported (see §6)
    ?checkStructure: bool)                // validate the DU schema at construction (default true)
```
`checkStructure = true` makes Argu throw `ArguException` *eagerly* if the DU is malformed
(e.g. an illegal attribute combination) — keep it on; you want schema errors at startup,
not mid-run.

## 2. Parse entry points

All return `ParseResults<'Template>`.

```fsharp
// argv only (most common). raiseOnUsage=false makes --help a normal path, not an exn.
parser.ParseCommandLine(
    ?inputs: string[],            // defaults to System.Environment args
    ?ignoreMissing: bool,         // suppress Mandatory errors (default false)
    ?ignoreUnrecognized: bool,    // ignore unknown tokens (default false)
    ?raiseOnUsage: bool)          // treat --help as a parse error (default true)

// argv + a configuration source, merged (CLI overrides config unless GatherAllSources).
parser.Parse(
    ?inputs, ?configurationReader, ?ignoreMissing, ?ignoreUnrecognized, ?raiseOnUsage)

// configuration source ONLY (no command line).
parser.ParseConfiguration(configurationReader, ?ignoreMissing)
```

Idiom: `ParseCommandLine(argv, raiseOnUsage = false)`, then check `IsUsageRequested`
before dispatching (see SKILL.md EntryPoint).

## 3. The `ParseResults` query API

Queries take an F# quotation of the case constructor (`<@ Config @>`) — that's how Argu
keeps it type-safe. `[<ReflectedDefinition>]` lets you usually write the bare case name.

```fsharp
r.GetResult(<@ Config @>)                       // value of a Mandatory/single case (throws if absent)
r.GetResult(<@ Log_Level @>, defaultValue = 1)  // value or default  (prefer TryGetResult instead)
r.TryGetResult(<@ From_Scn @>)                  // 'Field option   ← preferred for optional args
r.GetResults(<@ Listener @>)                    // 'Field list  (all occurrences of one case)
r.Contains(<@ Dry_Run @>)                       // bool  (was the flag present?)
r.GetAllResults()                               // 'Template list  (every parsed case, in order)
r.GetSubCommand()                               // 'Template  (the chosen subcommand case)
r.IsUsageRequested                              // bool  (was --help given?)
r.Parser                                        // the ArgumentParser for THIS results level
r.TryGetSubCommand()                            // option form where available
```

`?source: ParseSource` on the getters filters by origin (`CommandLine` | `AppSettings`)
— e.g. read a value only if it came from the command line.

### Cardinality ↔ getter mapping (keep the type honest)
| Case shape | Getter | Returns |
|---|---|---|
| `Mandatory` / `ExactlyOnce` | `GetResult` | value |
| optional single | `TryGetResult` | `option` |
| flag (nullary) | `Contains` | `bool` |
| repeatable | `GetResults` | `list` |
| subcommand | `GetSubCommand` | case |

## 4. Post-processing & validation — the seam

`PostProcessResult` / `TryPostProcessResult` run a function over a parsed field and, on
failure, raise a properly-formatted `ArguParseException` (rendered with usage by the
exiter). This is where you call **smart constructors** to map argv → domain.

```fsharp
// raises ArguParseException (via failwith inside the validator) on bad input,
// formatted exactly like a missing/invalid flag:
let cfg : ConfigPath =
    r.PostProcessResult(<@ Config @>, fun raw ->
        match ConfigPath.parse raw with
        | Ok p    -> p
        | Error e -> failwithf "invalid --config: %s" e)

// option form for non-mandatory fields:
let scn : Scn option =
    r.TryPostProcessResult(<@ From_Scn @>, Scn.ofInt64Validated)
```

Use this rather than getting a raw string and validating later — it keeps validation at
the boundary and gives uniform error UX.

## 5. Result at the boundary (pure-`Result` core)

For a strict `Result`-only core that never relies on exceptions, wrap the parse call and
convert `ArguParseException` to your error type at the edge. The exiter still handles the
*help* path; you intercept *errors*:

```fsharp
let tryParse (parser: ArgumentParser<CliArgs>) (argv: string[])
    : Result<ParseResults<CliArgs>, CliError> =
    try
        // ExceptionExiter turns errors into exceptions instead of exiting the process,
        // so we can catch and convert them to Result.
        let r = parser.ParseCommandLine(argv, raiseOnUsage = false)
        Ok r
    with
    | :? ArguParseException as e ->
        Error (CliError.OfArgu(e.ErrorCode, e.Message))
```
Construct the parser with `errorHandler = ExceptionExiter()` so parse failures raise rather
than calling `exit`. Then your whole pipeline — parse, validate, run — is one `Result`
chain, and the single `match` in `main` decides the exit code. Choose this when the codebase
law is "no exceptions across boundaries"; choose the `ProcessExiter` approach (SKILL.md) when
you're happy to let Argu format+exit on malformed input at the outermost edge.

## 6. Exiters

`IExiter` decides what happens on a parse/usage error: `member Name: string` and
`member Exit: msg: string * errorCode: ErrorCode -> 'T`.

- **`ProcessExiter(?colorizer)`** — prints the message and calls `exit` with a code derived
  from `ErrorCode`. The right default for a real CLI: clean message, correct exit status.
  `colorizer: ErrorCode -> ConsoleColor option` lets you color errors red but leave help
  uncolored:
  ```fsharp
  ProcessExiter(colorizer = function ErrorCode.HelpText -> None | _ -> Some ConsoleColor.Red)
  ```
- **`ExceptionExiter`** — raises `ArguParseException` instead of exiting. Use in **tests**
  and when converting to `Result` (§5), so a bad parse doesn't kill the test host.
- **Custom `IExiter`** — implement the interface to log structured errors, set a specific
  exit code per `ErrorCode`, etc.

## 7. Errors: `ArguParseException` / `ErrorCode`

- **`ArguException`** — base; schema/structure problems (thrown at `Create` when
  `checkStructure`). A *programmer* error: fix the DU.
- **`ArguParseException`** — a *user* input error. Useful members: `.Message`, `.FirstLine`
  (the first error line), `.ErrorCode`.
- **`ErrorCode`** — `HelpText` (user asked for `--help`), `CommandLine` (bad argv),
  `AppSettings` (bad config source), `PostProcess` (a `PostProcessResult` validator failed).
  Map these to process exit codes in a custom exiter if you need distinct statuses.

## 8. Help & usage rendering

```fsharp
parser.PrintUsage(?message)             // full usage string (commands, options, descriptions)
parser.PrintCommandLineSyntax()         // compact one-line syntax summary
results.Parser.PrintUsage()             // usage for the CURRENT (sub)command level
```
Help text is generated entirely from the DU + `Usage` members — never hand-written.
For a subcommand, grab its parser via `subResults.Parser` and `PrintUsage()` to show
context-specific help. Pair with `IsUsageRequested` to print and exit 0 instead of erroring.
