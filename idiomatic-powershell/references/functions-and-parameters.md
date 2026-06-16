# Advanced functions & parameters

Every reusable PowerShell function should be an **advanced function** — one that
behaves like a compiled cmdlet: a proper name, typed and validated parameters,
pipeline support, common parameters (`-Verbose`, `-ErrorAction`, …), and help.
The ceremony is small and pays for itself immediately.

## The anatomy

```powershell
function Get-Widget {
    [CmdletBinding()]                          # makes it an advanced function
    [OutputType([pscustomobject])]             # documents what it returns
    param(
        [Parameter(Mandatory,
                   ValueFromPipeline,
                   ValueFromPipelineByPropertyName)]
        [ValidateNotNullOrEmpty()]
        [string[]] $Name,

        [Parameter()]
        [ValidateRange(1, 100)]
        [int] $Count = 10
    )

    begin   { Write-Verbose "Starting $($MyInvocation.MyCommand)" }
    process {
        foreach ($n in $Name) {                # handle each pipeline item / array element
            [pscustomobject]@{ Name = $n; Count = $Count }
        }
    }
    end     { Write-Verbose 'Done' }
}
```

- **`[CmdletBinding()]`** is what turns a basic function into an advanced one: you
  get `$PSCmdlet`, the common parameters, and strict argument handling for free.
- **`[OutputType()]`** documents (and tooling-checks) the output type. Keep it
  honest.
- **`param()`** declares typed parameters; always type them (`[string]`, `[int]`,
  `[datetime]`, `[string[]]`, …).

## Approved Verb-Noun names

Name functions `Verb-Noun`, singular noun, with an **approved verb** (`Get`, `Set`,
`New`, `Remove`, `Start`, `Stop`, `Test`, `Invoke`, `Export`, …). Run `Get-Verb`
to see the list; PSScriptAnalyzer warns on unapproved verbs. This consistency is
why PowerShell is discoverable — `Get-*` always reads, `Remove-*` always deletes.

```powershell
Backup-Database      # good
Test-Connection      # good
DoBackup / GetData   # bad — non-standard, undiscoverable
```

## Parameter attributes that matter

```powershell
param(
    # Required, accepts pipeline input by value and by property name
    [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
    [string[]] $Path,

    # Belongs to a named parameter set (mutually exclusive option groups)
    [Parameter(ParameterSetName = 'ById', Mandatory)]
    [int] $Id,

    # Optional switch (presence = $true): -Force
    [switch] $Force
)
```

- **`ValueFromPipeline`** binds the whole incoming object to this parameter;
  **`ValueFromPipelineByPropertyName`** binds a same-named property of incoming
  objects — design for both so your function composes in pipelines.
- **Parameter sets** model mutually-exclusive call styles (e.g. by-Id vs by-Name);
  set `[CmdletBinding(DefaultParameterSetName='…')]`.
- **`[switch]`** for flags — never a `[bool] $Force = $false` that forces callers to
  pass `$true`.

## Validation attributes — fail at the boundary

Let the parameter binder reject bad input before your body runs, with clear
messages — don't hand-write `if`-checks:

| Attribute                          | Enforces                                  |
|------------------------------------|-------------------------------------------|
| `[ValidateNotNullOrEmpty()]`       | not `$null`, not empty                     |
| `[ValidateSet('A','B','C')]`       | one of a fixed set (also gives tab-completion) |
| `[ValidateRange(1, 100)]`          | numeric range                              |
| `[ValidatePattern('^\w+$')]`       | regex match                                |
| `[ValidateScript({ Test-Path $_ })]` | arbitrary predicate                      |
| `[ValidateCount(1, 5)]`            | array element count                        |
| `[ValidateLength(1, 50)]`          | string length                             |

```powershell
[Parameter(Mandatory)]
[ValidateSet('Dev','Test','Prod')]
[string] $Environment
```

This is PowerShell's "make illegal arguments unrepresentable" — push correctness
into the parameter declaration.

## `begin` / `process` / `end` — be pipeline-aware

When a function accepts pipeline input, PowerShell calls **`process` once per
incoming item**. Put per-item work there; use `begin` for one-time setup and `end`
for finalization:

```powershell
function Convert-ToUpper {
    [CmdletBinding()]
    param([Parameter(ValueFromPipeline)][string] $Text)
    process { $Text.ToUpper() }      # runs for every piped string
}

'a', 'b', 'c' | Convert-ToUpper      # A B C
```

A function with all its logic in the (implicit) `end` block only sees the *last*
piped item via the parameter — a common bug. If you accept pipeline input, you
need a `process` block.

## Splatting — pass parameters as a hashtable

For calls with many parameters, splat a hashtable instead of a long line of
`-Param value`. It's readable, diffable, and lets you build calls dynamically:

```powershell
$params = @{
    Path        = 'C:\temp'
    Recurse     = $true
    Filter      = '*.log'
    ErrorAction = 'Stop'
}
Get-ChildItem @params            # note @ (splat), not $
```

Use `@splat` for switches too (`Force = $true`). Splatting also keeps optional
parameters out of the call when a value is absent.

## Comment-based help

Document functions with comment-based help so `Get-Help Get-Widget` works:

```powershell
function Get-Widget {
<#
.SYNOPSIS
    Gets widgets by name.
.DESCRIPTION
    Returns a widget object for each supplied name.
.PARAMETER Name
    One or more widget names; accepts pipeline input.
.EXAMPLE
    'a','b' | Get-Widget
.OUTPUTS
    pscustomobject
#>
    [CmdletBinding()]
    param(...)
}
```

Keep at least `.SYNOPSIS`, `.PARAMETER` per parameter, and one `.EXAMPLE`.

## Checklist

- [ ] `[CmdletBinding()]` present; name is approved `Verb-Noun`, singular noun.
- [ ] Every parameter typed; validation via attributes, not manual `if`s.
- [ ] Pipeline input bound (`ValueFromPipeline*`) and handled in a `process` block.
- [ ] `[OutputType]` declared and accurate; returns objects, not text.
- [ ] Comment-based help with at least one example.
- [ ] Long calls use splatting.
