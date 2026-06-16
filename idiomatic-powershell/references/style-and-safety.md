# Style & safety

Professional PowerShell is readable, analyzable, and safe-by-default. These are
the conventions that make a script reviewable and keep it from doing damage.

## Naming & layout

- **No aliases in scripts.** `Get-ChildItem`, not `gci`/`ls`; `Where-Object`, not
  `?`; `ForEach-Object`, not `%`; `Get-Content`, not `cat`. Aliases are for
  interactive typing; in saved code they hurt readability and portability
  (aliases differ across hosts/platforms). Likewise use full parameter names in
  scripts.
- **Approved Verb-Noun** for functions (`Get-Verb`), singular noun, `PascalCase`
  (see `functions-and-parameters.md`).
- **`PascalCase`** for function and parameter names; `$camelCase` or `$PascalCase`
  for variables (be consistent); avoid cryptic abbreviations.
- **One True Brace Style (OTBS)**: opening brace on the same line, `else`/`catch`
  on the same line as the closing brace. 4-space indent.
- **Long pipelines**: one stage per line, `|` at the end of the line.
- Prefer `-eq`/`-ne`/`-gt` (not `==`), and put **`$null` on the left** of
  comparisons: `if ($null -eq $x)` — `$x -eq $null` misbehaves when `$x` is a
  collection (and PSScriptAnalyzer flags it).

## Set-StrictMode & #Requires

Start scripts/modules defensively:

```powershell
#Requires -Version 7.0                 # refuse to run on older engines
#Requires -Modules Az.Accounts          # declare module dependencies
Set-StrictMode -Version Latest          # error on uninitialized vars, bad refs
$ErrorActionPreference = 'Stop'         # fail fast (a reasonable script default)
```

- **`Set-StrictMode -Version Latest`** turns silent mistakes (referencing an
  undefined variable, calling a non-existent property, indexing wrong) into
  errors. Develop with it on.
- **`#Requires`** statements are enforced by the engine before the script runs —
  declare version and module needs instead of failing cryptically later.

## PSScriptAnalyzer — lint everything

[PSScriptAnalyzer](https://github.com/PowerShell/PSScriptAnalyzer) is the standard
linter; treat it as part of "done". It catches unapproved verbs, aliases,
`$null`-comparison order, unused variables, `Write-Host` misuse, plaintext
secrets, missing `ShouldProcess`, and more.

```powershell
Invoke-ScriptAnalyzer -Path .\script.ps1 -Recurse
Invoke-ScriptAnalyzer -Path . -Settings PSGallery -Recurse
```

Wire it into CI and pre-commit. Use `Invoke-Formatter` (same module) to apply
consistent style automatically. Suppress a specific rule only with a justified
`[Diagnostics.CodeAnalysis.SuppressMessageAttribute(...)]`, not blanket disabling.

## ShouldProcess — make destructive actions safe

Any function that changes state (deletes, overwrites, restarts) should support
`-WhatIf`/`-Confirm`. Declare `SupportsShouldProcess` and gate the mutation:

```powershell
function Remove-OldLog {
    [CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'High')]
    param([Parameter(Mandatory)][string] $Path)

    process {
        if ($PSCmdlet.ShouldProcess($Path, 'Remove file')) {
            Remove-Item -Path $Path -ErrorAction Stop
        }
    }
}

Remove-OldLog -Path huge.log -WhatIf     # "What if: Performing ... Remove file ..."
```

- `-WhatIf` previews without acting; `-Confirm` prompts; `ConfirmImpact = 'High'`
  prompts by default for dangerous actions.
- Free benefit: calls to other ShouldProcess-aware cmdlets inside your function
  honor `-WhatIf` automatically when you pass it through.

## Credentials & secrets — never plaintext

- Take credentials as **`[pscredential]`**, not separate user/password strings:
  ```powershell
  param([Parameter(Mandatory)][pscredential] $Credential)
  ```
  Callers supply `Get-Credential` (interactive) or a stored secret.
- Never hard-code passwords or API keys in scripts. Use the
  **`Microsoft.PowerShell.SecretManagement`** module (with a vault) for stored
  secrets, or environment variables / a secrets manager in CI.
- `SecureString` is the in-memory type for sensitive strings, but note it is **not
  a strong protection at rest** and is platform-limited on non-Windows — prefer a
  real secret store. Don't `ConvertTo-SecureString -AsPlainText` a literal in
  committed code.
- Don't log credentials or full command lines that contain secrets.

## Avoid `Invoke-Expression`

`Invoke-Expression` (`iex`) executes a string as code — an injection risk and
almost never necessary. Alternatives:

- Run an external program with the **call operator** and an argument array /
  splat: `& $exe @arguments`.
- Call a cmdlet/function dynamically with `& $commandName @params`.
- Build parameter sets with **splatting** (`@params`) rather than string-building a
  command line.

```powershell
# Don't:
Invoke-Expression "Get-Service -Name $name"
# Do:
Get-Service -Name $name
# Dynamic command name:
$cmd = 'Get-Service'; & $cmd -Name $name
```

## Modules & structure

- Group related functions into a **module** (`.psm1`) with a **manifest**
  (`.psd1`) declaring version, `RequiredModules`, and `FunctionsToExport` (export
  explicitly — don't `*`).
- Keep one public concern per file when the module grows; dot-source or use a
  build step to assemble.
- Provide comment-based help on every public function.

## Checklist

- [ ] No aliases / no abbreviated parameters in saved code.
- [ ] `Set-StrictMode -Version Latest`; `#Requires` for version/modules.
- [ ] PSScriptAnalyzer-clean (run in CI).
- [ ] State-changing functions support `ShouldProcess` (`-WhatIf`/`-Confirm`).
- [ ] Credentials as `[pscredential]`/secret store; no plaintext secrets.
- [ ] No `Invoke-Expression`; `$null` on the left of comparisons.
