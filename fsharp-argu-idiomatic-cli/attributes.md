# Argu attribute catalog

Every attribute lives in `Argu` (open `Argu`). Apply them to DU cases to shape the
generated parser. Grouped by what they control. Default CLI name derivation:
`Working_Directory` → `--working-directory` (underscore → dash, lowercased,
double-dash prefix).

## Table of contents
1. Naming & prefixes
2. Arity & occurrence constraints
3. Position constraints
4. Assignment syntax (`--key=value`)
5. Subcommands & inheritance
6. Main/positional arguments
7. Help & visibility
8. Unrecognized capture
9. Configuration sources (appSettings / XML)

---

## 1. Naming & prefixes

**`AltCommandLine("-c", "--cfg")`** — extra CLI aliases in addition to the derived name.
Add short forms here.
```fsharp
| [<AltCommandLine("-c")>] Config of path: string   // matches --config or -c
```

**`CustomCommandLine("listener")`** — replace the derived name entirely with explicit
token(s). Use when the derived name is wrong (e.g. you want `ip` not `i-p`).
```fsharp
| [<CustomCommandLine("listener")>] Listener of host: string * port: int
```

**`CliPrefix(prefix)`** — override the `--` prefix for the *derived* name.
`CliPrefix.Dash` → single `-`; `CliPrefix.DoubleDash` → `--` (default);
`CliPrefix.None` → no prefix (the case becomes a bare word — this is how you make
**subcommands** and bare positional verbs).
```fsharp
| [<CliPrefix(CliPrefix.None)>] Run of ParseResults<RunArgs>   // bare word "run"
```
Can be applied at the *DU type* level to set a default prefix for all cases.

## 2. Arity & occurrence constraints

**`Mandatory`** — the argument must be supplied; absence is a parse error. Lets you use
`GetResult` safely (the value can't be missing).
```fsharp
| [<Mandatory>] Config of path: string
```

**`Unique`** — may appear at most once (duplicates are an error). Good for flags that
shouldn't be repeated.

**`ExactlyOnce`** — must appear exactly once (`Mandatory` + `Unique`). Strongest single-
occurrence guarantee; pairs with `GetResult`.

> Without these, a case is **multiple-allowed** by default — `GetResults` returns the
> list, `GetAllResults` includes every occurrence. Choose the attribute that makes the
> type tell the truth about cardinality.

## 3. Position constraints

**`First`** — must appear at the *start* of the command line. For a required leading verb
or sentinel.

**`Last`** — must appear at the *end*. Common for a trailing positional like a path or a
`-- passthrough`.

```fsharp
| [<First>] Mode of string
| [<Last>]  Target of path: string
```

## 4. Assignment syntax (`--key=value`)

By default Argu accepts space separation (`--config foo`). These force/allow `=` or `:`:

**`EqualsAssignment`** — *requires* `--key=value` form (single-parameter cases only).
**`EqualsAssignmentOrSpaced`** — accepts either `--key=value` or `--key value`.
**`ColonAssignment`** — *requires* `--key:value`.
**`ColonAssignmentOrSpaced`** — accepts `--key:value` or `--key value`.

```fsharp
| [<EqualsAssignment>] Define of key: string * value: string   // --define=k=v
```
Useful for key/value pairs and for values that could be mistaken for the next token.

## 5. Subcommands & inheritance

**Subcommand** = a case carrying `ParseResults<'SubArgs>`, conventionally marked
`CliPrefix(CliPrefix.None)`. Argu recurses into the nested DU.
```fsharp
| [<CliPrefix(CliPrefix.None)>] Bulk_Load of ParseResults<BulkLoadArgs>
```

**`SubCommand`** — explicitly mark a **nullary** case (no `ParseResults`, no fields) as a
subcommand verb rather than a flag.
```fsharp
| [<SubCommand; CliPrefix(CliPrefix.None)>] Status
```

**`Inherit`** — make a top-level argument available *inside* all subcommands too
(e.g. a global `--verbose`). Without it, a top-level flag can't be passed after the
subcommand word.
```fsharp
| [<Inherit; AltCommandLine("-v")>] Verbose
```

Retrieve the chosen subcommand with `results.GetSubCommand()` and pattern-match.

## 6. Main / positional arguments

**`MainCommand`** — the case that captures *positional* (prefix-less) arguments — values
given without any `--flag`. At most one per command. Use for the primary operand(s).
```fsharp
| [<MainCommand; ExactlyOnce; Last>] Sources of tables: string list   // pipeline run a b c
```

**`Rest`** — capture *all remaining* tokens after this point verbatim (no further parsing),
e.g. arguments to forward to a child process.
```fsharp
| [<Rest>] Passthrough of string
```

## 7. Help & visibility

**`Hidden`** — valid argument, but omitted from `--help`/usage output. For deprecated or
internal flags you still accept but don't advertise.
```fsharp
| [<Hidden>] Legacy_Mode
```

The help text itself comes from the `IArgParserTemplate.Usage` member — there is no help
attribute; the type member is the source of truth.

## 8. Unrecognized capture

**`GatherUnrecognized`** — collect tokens Argu doesn't recognize into this case instead of
erroring (must be a `string`-carrying case). Combine with `ignoreUnrecognized = true` on
the parse call. For plugin-style passthrough or lenient front-ends.
```fsharp
| [<GatherUnrecognized>] Unrecognized of string
```

## 9. Configuration sources (appSettings / XML)

These let the *same* DU be sourced from `app.config`/`appSettings.json`/env, not just argv
(see `integration.md` for readers and precedence).

**`AppSettings("key")`** / default key derivation — bind the case to a configuration key.
**`CustomAppSettings("credentials:username")`** — explicit (possibly nested, colon-
separated) config key.
**`NoCommandLine`** — the case is sourced *only* from configuration, never the command line
(e.g. secrets you don't want on argv).
**`GatherAllSources`** — merge values from *all* sources (CLI + config) rather than letting
CLI override; you get every value found.

```fsharp
| [<CustomAppSettings "credentials:password"; NoCommandLine>] Password of string
```

---

### Choosing attributes — quick guidance

- Required single value → `Mandatory` (or `ExactlyOnce`), then `GetResult`.
- Optional value → no attribute, then `TryGetResult |> Option.map`.
- Subcommand verb → `CliPrefix(CliPrefix.None)` on a `ParseResults<_>` (or `SubCommand` if nullary).
- Global flag usable after the verb → `Inherit`.
- Primary positional operand → `MainCommand`.
- Short alias → `AltCommandLine`.
- Secret from config only → `NoCommandLine` + `CustomAppSettings`.

The guiding rule: pick the attribute that makes the **type's cardinality and source match
reality**, so the parsed value can be mapped to a domain spec without re-checking.
