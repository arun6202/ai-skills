---
name: idiomatic-powershell
description: >-
  Write, refactor, or review idiomatic, professional PowerShell (.ps1, .psm1,
  .psd1). Use this whenever you produce PowerShell — scripts, modules, advanced
  functions/cmdlets, automation, CI steps — even a quick "write a PowerShell
  script to…". Steers toward PowerShell's real idiom: the object pipeline (not
  text munging), advanced functions with proper parameters and validation,
  approved Verb-Noun names, robust error handling, structured object output over
  Write-Host, and safe-by-default scripting (ShouldProcess, credentials,
  PSScriptAnalyzer). Counters the reflexes of writing PowerShell like cmd/bash or
  transliterated C#, and alias-laden one-liners. Targets PowerShell 7.x while
  flagging Windows PowerShell 5.1 differences.
---

# Idiomatic PowerShell

PowerShell is an **object-pipeline automation language**, not a text-processing
shell and not C# with `$` signs. Its power is that cmdlets pass rich .NET objects
— not strings — down the pipeline, so you filter, transform, and shape *typed
data* instead of parsing text. Write to that grain and scripts become short,
composable, and robust.

The enemy is muscle memory from other shells and languages: aliases everywhere,
`for` loops with indexes, string-building output, `Write-Host`, swallowed errors.
Default to the idiomatic form below; reach for the imperative escape hatch only
with a reason.

> **Part of the `idiomatic-code` family** (the automation/outlier member — shares immutability, pipelines, structured output, fail-loudly errors; not the ADT/type-driven core).
>
> Targets **PowerShell 7.x** (cross-platform `pwsh`) as the modern default, and
> calls out **Windows PowerShell 5.1** differences where they bite (5.1 lacks the
> 7.x operators — see `references/modern-and-portable.md`). If you know the target
> runtime, write to it; otherwise prefer portable constructs.

## Break the muscle memory (reflex → idiomatic)

When your instinct fires the left column, write the right column instead.

| Reflex (other shells / C# / habit)                  | Idiomatic PowerShell                                                  |
|-----------------------------------------------------|----------------------------------------------------------------------|
| Aliases in scripts: `ls`, `gci`, `%`, `?`, `cat`, `echo` | Full cmdlet names: `Get-ChildItem`, `ForEach-Object`, `Where-Object`, `Get-Content`, `Write-Output` |
| Parse command *text* with `-split`/regex            | Use the **objects** and their properties                             |
| `for ($i=0; $i -lt $a.Count; $i++) { $a[$i] }`      | Pipeline / `foreach ($x in $a)` / `$a.ForEach{ }`                    |
| Build a string and print it                         | Emit a `[pscustomobject]` (structured output)                       |
| `$arr = @(); $arr += $x` inside a loop              | Output to the pipeline and collect: `$arr = foreach (…) { $x }`      |
| `Write-Host`                                         | `Write-Output` (data) / `Write-Verbose`,`Write-Information` (messages)|
| `function DoBackup { }`                              | Approved **Verb-Noun**: `function Backup-Database { }`               |
| `param($x)` with no validation                      | `[Parameter()]` + `[Validate*]` attributes                          |
| Swallow errors / `-ErrorAction SilentlyContinue`    | `-ErrorAction Stop` + `try/catch`                                   |
| Plaintext passwords in script                       | `[pscredential]` / `SecureString`, `Get-Credential`                 |
| `Invoke-Expression $cmd`                            | Call operator `& $exe @args` + splatting                            |
| Return `Format-Table` output from a function        | Return **objects**; format only at the final display                |
| `if ($x -eq $null)`                                  | `if ($null -eq $x)` (null on the **left**)                          |
| Global variables for state                          | Parameters in, objects out                                          |

If you truly need imperative loops, in-place mutation, or `Write-Host` for an
interactive banner — fine. Make it a decision, not a default.

## The creed

1. **Objects, not text.** Keep data as objects through the whole pipeline; parse
   text only at the untyped edges, and emit `[pscustomobject]`, never preformatted
   strings.
2. **Pipeline-first.** Express transforms as `… | Where-Object | ForEach-Object |
   Select-Object`. Write pipeline-aware functions with a `process` block.
3. **Functions are cmdlets.** Every reusable function is an *advanced function*:
   `[CmdletBinding()]`, a typed `param()` with validation, an approved Verb-Noun
   name, and comment-based help.
4. **Fail loudly, handle deliberately.** Turn errors terminating with
   `-ErrorAction Stop` and `try/catch`; don't silently continue.
5. **Structured output.** Return rich objects so callers can filter/sort/format.
   Use the right stream for messages (`Verbose`/`Warning`/`Information`).
6. **Safe by default.** `Set-StrictMode`, `#Requires`, `ShouldProcess` for
   destructive actions, real credential types, and PSScriptAnalyzer-clean code.
7. **Readable.** Full cmdlet/parameter names, splatting for long calls, one stage
   per line in long pipelines.

## Quick reach-for guide

| You need to…                              | Reach for…                                                       |
|-------------------------------------------|------------------------------------------------------------------|
| Filter items                              | `Where-Object { $_.Prop -gt 1 }` (or simple `Where-Object Prop -GT 1`) |
| Transform each item                       | `ForEach-Object { … }` or the `.ForEach{ }` method               |
| Pick / compute columns                    | `Select-Object Name, @{ n='X'; e={ … } }`                        |
| Return structured data                    | `[pscustomobject]@{ Name = …; Value = … }`                      |
| A reusable, pipeline-aware function       | advanced function with `begin/process/end`                       |
| Long command with many params             | **splatting**: `Cmd @params`                                     |
| Destructive operation                     | `[CmdletBinding(SupportsShouldProcess)]` + `$PSCmdlet.ShouldProcess(...)` |
| Parallel work (PS7)                       | `… | ForEach-Object -Parallel { … } -ThrottleLimit n`           |
| Conditional value (PS7)                   | ternary `$cond ? $a : $b`; default `$x ?? $fallback`            |

## Reference files — read on demand

- **`references/pipeline-and-objects.md`** — the object pipeline, `Where-Object`/
  `ForEach-Object`/`Select-Object`/`Sort-Object`/`Group-Object`/`Measure-Object`,
  calculated properties, `.Where()`/`.ForEach()` methods, "filter left, format
  right", and avoiding text parsing. *Read for any data processing.*
- **`references/functions-and-parameters.md`** — advanced functions:
  `[CmdletBinding()]`, `param()`, parameter + validation attributes, pipeline
  binding, `begin/process/end`, approved verbs, `[OutputType]`, splatting,
  comment-based help. *Read when writing any function/cmdlet.*
- **`references/error-handling.md`** — terminating vs non-terminating errors,
  `$ErrorActionPreference`, `-ErrorAction`/`-ErrorVariable`, `try/catch/finally`,
  `throw`, `$?`/`$LASTEXITCODE`, native-command errors. *Read for robust scripts.*
- **`references/output-and-streams.md`** — the output/error/warning/verbose/debug/
  information streams, `Write-Output` vs `Write-Host`, return semantics,
  `[pscustomobject]`, redirection. *Read when a function produces output.*
- **`references/style-and-safety.md`** — naming, PSScriptAnalyzer, `Set-StrictMode`,
  `#Requires`, `ShouldProcess`/`-WhatIf`/`-Confirm`, credentials/SecureString,
  avoiding `Invoke-Expression`. *Read for production-quality, safe scripts.*
- **`references/modern-and-portable.md`** — PowerShell 7.x vs Windows PowerShell
  5.1: ternary, `??`/`??=`, null-conditional `${x}?.`, `&&`/`||`,
  `ForEach-Object -Parallel`, cross-platform paths, `$IsWindows`. *Read when
  targeting a specific runtime or writing portable code.*

## A taste

```powershell
#Requires -Version 7.0
Set-StrictMode -Version Latest

function Get-LargeFile {
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [ValidateNotNullOrEmpty()]
        [string[]] $Path,

        [ValidateRange(1, [long]::MaxValue)]
        [long] $MinimumBytes = 1MB
    )
    process {
        Get-ChildItem -Path $Path -File -Recurse -ErrorAction Stop |
            Where-Object Length -GT $MinimumBytes |
            Sort-Object Length -Descending |
            Select-Object FullName,
                          @{ Name = 'SizeMB'; Expression = { [math]::Round($_.Length / 1MB, 2) } }
    }
}
```

Objects in, objects out; validated parameters; pipeline-aware; errors terminate;
no aliases, no `Write-Host`, no text parsing. That is the target for all
PowerShell here.
