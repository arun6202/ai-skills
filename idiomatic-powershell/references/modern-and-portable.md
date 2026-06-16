# Modern & portable PowerShell

There are two PowerShells, and the difference matters for what you can write:

- **PowerShell 7.x** (`pwsh`) — cross-platform (Windows/Linux/macOS), open source,
  built on modern .NET. The current line is 7.4 (LTS) and 7.5+. This is the modern
  default; write to it when you can.
- **Windows PowerShell 5.1** (`powershell.exe`) — Windows-only, built on .NET
  Framework, in maintenance (no new language features). Still ubiquitous on
  servers and the default on stock Windows — including this machine.

Know your target runtime. Use modern syntax when targeting 7.x; stay on the
common subset when a script must run under 5.1. Gate with `#Requires -Version 7.0`
so a 7-only script fails fast on 5.1 instead of erroring mid-run.

## PowerShell 7-only operators (NOT in 5.1)

These read much better than the 5.1 equivalents — but using any of them makes a
script 7.x-only.

```powershell
# Ternary (PS7):
$status = $ok ? 'pass' : 'fail'
# 5.1 equivalent:
$status = if ($ok) { 'pass' } else { 'fail' }

# Null-coalescing / assignment (PS7):
$name = $input ?? 'default'
$cache ??= @{}
# 5.1 equivalent:
$name = if ($null -ne $input) { $input } else { 'default' }

# Null-conditional (PS7.1+): NOTE the required braces around the variable,
# because '?' is a legal character in variable names.
$len = ${obj}?.Name?.Length          # $obj?.Name would mean a variable named 'obj?'
$first = ${arr}?[0]

# Pipeline chain operators (PS7): run next based on success/failure
dotnet build && dotnet test
Test-Path $p || Write-Warning 'missing'
# 5.1 equivalent: check $? / $LASTEXITCODE with if
```

The brace rule for `?.`/`?[]` is the one easy-to-miss detail: always
`${variable}?.Member`, never `$variable?.Member`.

## Parallelism (PS7)

`ForEach-Object -Parallel` runs script blocks on multiple threads — great for
I/O-bound work (web calls, file ops). Two things to remember:

```powershell
$results = $urls | ForEach-Object -Parallel {
    Invoke-RestMethod -Uri $_                 # $_ is the current item
    # outer variables are NOT in scope by default — import with $using:
    # Write-Verbose $using:logPrefix
} -ThrottleLimit 5
```

- Each parallel runspace is **isolated**: reference outer variables with the
  `$using:` prefix; you can't mutate shared state without thread-safe types
  (`[System.Collections.Concurrent.*]`).
- **Throttle** with `-ThrottleLimit` so you don't spawn unbounded work.
- It has real per-item runspace overhead — worth it for I/O-bound or heavy CPU
  work, not for trivial loops over small collections.
- 5.1 has no `-Parallel`; use `Start-Job`/`Start-ThreadJob`, runspaces, or
  workflow-era approaches there.

`Start-ThreadJob` (module, available cross-version) is a lighter alternative to
`Start-Job` for background work without separate processes.

## Cross-platform hygiene (7.x)

If a script should run on Linux/macOS as well as Windows:

- **Paths**: build with `Join-Path` / `[System.IO.Path]`, not hard-coded `\`. Use
  `[System.IO.Path]::DirectorySeparatorChar` when you must; prefer `/` which works
  on Windows too.
- **OS checks**: `$IsWindows`, `$IsLinux`, `$IsMacOS` automatic variables (7.x).
- **Avoid Windows-only cmdlets** in portable code: `Get-CimInstance`/WMI, the
  registry provider, `*-Service`/`*-EventLog` (some are Windows-only or behave
  differently). Guard with `if ($IsWindows)` when unavoidable.
- **Environment**: `$env:HOME` vs `$env:USERPROFILE`; case-sensitive filesystems
  on Linux; line endings.
- **Encoding**: 7.x defaults to UTF-8 (no BOM); 5.1 often defaults to UTF-16/ANSI.
  Be explicit (`-Encoding utf8`) when writing files other tools will read.

## Classes (PowerShell 5.0+)

PowerShell has `class` (and `enum`) since 5.0 — useful for DSC resources, custom
exception types, and structured types with methods. But for ordinary "return
structured data", prefer `[pscustomobject]` (lighter, pipeline-friendly). Reach
for a `class` when you need methods, inheritance, constructors with validation, or
a typed contract — not as the default container.

```powershell
class Server {
    [string] $Name
    [int]    $Port = 443
    [string] ToString() { return "$($this.Name):$($this.Port)" }
}
```

## Targeting guidance

- **New automation, you control the runtime** → write for 7.x; use ternary,
  `??`, `-Parallel`, `&&`/`||` freely; `#Requires -Version 7.0`.
- **Must run on stock Windows / 5.1 (like this machine's default shell)** → avoid
  the 7-only operators and `-Parallel`; test under `powershell.exe`; watch the
  encoding and `2>&1`/native-stderr gotchas (see `error-handling.md`).
- **Must run on both** → stick to the common subset, gate OS- or
  version-specific branches with `$IsWindows` / `$PSVersionTable.PSVersion`.

`$PSVersionTable.PSVersion` tells you the running engine — branch on it when a
script genuinely must adapt.
