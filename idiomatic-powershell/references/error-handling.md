# Error handling

PowerShell's error model trips up newcomers because many errors are
**non-terminating** by default — the pipeline keeps going after a failure. Robust
scripts make the errors they care about terminating and handle them deliberately;
they don't sprinkle `-ErrorAction SilentlyContinue` to make red text disappear.

## Terminating vs non-terminating

- **Non-terminating** (the default for most cmdlets): the cmdlet writes an error
  to the error stream and **continues**. `try/catch` does **not** catch these
  unless you elevate them.
- **Terminating**: stops execution (or the current pipeline) and *can* be caught.

Elevate a non-terminating error to terminating with **`-ErrorAction Stop`** per
call (preferred — surgical), or script-wide with
`$ErrorActionPreference = 'Stop'`:

```powershell
try {
    $content = Get-Content -Path $Path -ErrorAction Stop   # now catchable
}
catch {
    Write-Error "Could not read $Path : $($_.Exception.Message)"
}
```

## `try` / `catch` / `finally`

```powershell
try {
    $data = Invoke-RestMethod -Uri $url -ErrorAction Stop
    Save-Data $data
}
catch [System.Net.Http.HttpRequestException] {   # specific type first
    Write-Warning "Network failed: $($_.Exception.Message)"
}
catch {                                           # catch-all last
    throw                                         # rethrow what you can't handle
}
finally {
    $stream?.Dispose()                            # cleanup always runs
}
```

- Catch **specific exception types** before a general `catch`.
- In a `catch`, the error is `$_` (or `$PSItem`): `$_.Exception`,
  `$_.Exception.Message`, `$_.ScriptStackTrace`,
  `$_.CategoryInfo`, `$_.TargetObject`.
- **Rethrow with bare `throw`** when you can't meaningfully handle an error —
  don't swallow it.
- `finally` runs whether or not an error occurred — use it to release resources.

## `$ErrorActionPreference` and `-ErrorAction`

`-ErrorAction` (per-cmdlet) overrides `$ErrorActionPreference` (scope-wide). Values:
`Stop`, `Continue` (default), `SilentlyContinue`, `Ignore`, `Inquire`.

- Prefer **per-call `-ErrorAction Stop`** around the operations you guard — it's
  explicit and local.
- Setting `$ErrorActionPreference = 'Stop'` at the top of a script is a reasonable
  "fail fast" default, but know it makes *every* non-terminating error terminating.
- Avoid blanket `SilentlyContinue`/`Ignore` — you're hiding failures, not handling
  them. Use them only when an error is genuinely expected and irrelevant (e.g.
  "delete if exists").

## Collecting errors without stopping

When you intentionally process a batch and want to continue past failures, capture
errors instead of suppressing them:

```powershell
$items | ForEach-Object {
    try   { Process-Item $_ -ErrorAction Stop }
    catch { Write-Warning "Skipped $($_.TargetObject): $($_.Exception.Message)" }
}

# Or collect into a variable for later inspection:
Get-Thing -ErrorAction SilentlyContinue -ErrorVariable failures
if ($failures) { Write-Warning "$($failures.Count) failed" }
```

`$Error` is an automatic array of recent errors (`$Error[0]` is the latest) —
useful for diagnostics, but prefer `-ErrorVariable` for intentional capture.

## `throw` and custom errors

```powershell
throw "Configuration file not found: $Path"        # simple
throw [System.IO.FileNotFoundException]::new($Path) # typed

# Richer control (category, target) from inside an advanced function:
$PSCmdlet.ThrowTerminatingError($errorRecord)
$PSCmdlet.WriteError($errorRecord)                  # non-terminating
```

`throw` produces a terminating error. For library-quality functions, build an
`ErrorRecord` and use `$PSCmdlet.ThrowTerminatingError(...)` so callers get proper
category/target info. Use `Write-Error` for non-terminating errors you want
reported but not fatal (see `output-and-streams.md`).

## Native commands (.exe) — a different beast

External executables don't raise PowerShell errors. Check their **exit code**:

```powershell
& git push
if ($LASTEXITCODE -ne 0) { throw "git push failed ($LASTEXITCODE)" }
```

- `$LASTEXITCODE` holds the last native exit code; `$?` is `$true`/`$false` for the
  success of the last command (cmdlet or native).
- In **PowerShell 7.4+** you can opt into native error handling via
  `$PSNativeCommandUseErrorActionPreference = $true`, so a non-zero exit becomes a
  terminating error under `-ErrorAction Stop`.
- The pipeline-chain operators `&&`/`||` (PS7) run the next command based on
  success/failure — `dotnet build && dotnet test` (see `modern-and-portable.md`).
- Caveat (Windows PowerShell 5.1): redirecting a native command's `stderr` with
  `2>&1` wraps each line in an error record and can flip `$?` to `$false` even on
  exit code 0 — check `$LASTEXITCODE`, don't infer from `$?`.

## Rules of thumb

- Guard real operations with `-ErrorAction Stop` + `try/catch`; rethrow what you
  can't handle.
- Never silence errors to clean up output — capture or handle them.
- For `.exe`, check `$LASTEXITCODE`; don't assume failures throw.
- Clean up in `finally`.
