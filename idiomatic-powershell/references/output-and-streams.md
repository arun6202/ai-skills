# Output & streams

A function's job is to **emit objects** to the pipeline. Messages for the human
(progress, warnings, diagnostics) go to *other* streams, not mixed into the data.
Getting this right is what lets your functions compose — and is the single most
common thing that separates idiomatic PowerShell from "scripts that print."

## The streams

PowerShell has six numbered streams; keep data and chatter separate:

| # | Stream       | Write with…           | For…                                         |
|---|--------------|-----------------------|----------------------------------------------|
| 1 | Success/Output | `Write-Output` / just emit | the **data** the function returns       |
| 2 | Error        | `Write-Error` / `throw` | failures (see `error-handling.md`)         |
| 3 | Warning      | `Write-Warning`       | something’s off but not fatal                |
| 4 | Verbose      | `Write-Verbose`       | opt-in detail (shown with `-Verbose`)        |
| 5 | Debug        | `Write-Debug`         | opt-in dev diagnostics (`-Debug`)            |
| 6 | Information   | `Write-Information` / `Write-Host` | human-facing messages          |

Only stream 1 flows down the pipeline as data. The others are for humans and are
controlled by preferences/switches — so a caller can capture your data clean while
still seeing (or suppressing) messages.

## How to return data

Just produce the object — an explicit `Write-Output` is rarely needed; any value
not captured becomes pipeline output:

```powershell
function Get-Stats {
    [CmdletBinding()]
    param([int[]] $Numbers)

    [pscustomobject]@{                # this is the return value
        Count   = $Numbers.Count
        Sum     = ($Numbers | Measure-Object -Sum).Sum
        Average = ($Numbers | Measure-Object -Average).Average
    }
}
```

- `return $x` in PowerShell means "emit `$x` and stop the function" — it is **not**
  the only way to return, and not required. Every uncaptured expression is emitted.
  Use bare `return` for early exit, `return $x` for clarity when helpful.
- Beware **accidental output**: a method call or assignment that leaves a value on
  the pipeline pollutes your function's output. Silence it with `$null = …`,
  `[void](…)`, or `… | Out-Null`:
  ```powershell
  $null = $list.Add($item)          # .Add returns the index — suppress it
  ```

## `[pscustomobject]` — your output type

Return structured objects, never preformatted strings. `[pscustomobject]@{…}`
creates one with ordered properties:

```powershell
[pscustomobject]@{
    Name      = $name
    Status    = $status
    Timestamp = Get-Date
}
```

Now the caller can `Where-Object`, `Sort-Object`, `Export-Csv`, `ConvertTo-Json`,
or format it — none of which is possible if you returned a string or a
`Format-Table`.

## The `Write-Host` problem

`Write-Host` writes to the host (the information stream in modern PowerShell) — it
is **not pipeline data**. Using it to "return" values is the classic anti-pattern:
the caller can't capture, filter, or reuse anything.

- **Returning data?** → emit an object (stream 1). Never `Write-Host`.
- **Telling the user something during a long operation?** → `Write-Verbose`
  (opt-in) or `Write-Information`. These can be captured/redirected and respect
  preferences.
- **Genuinely want colored, human-only console text** (an interactive tool's
  banner)? → `Write-Host` is acceptable *for that*, and `-ForegroundColor` is its
  one advantage. But in a function meant to be composed, prefer `Write-Information`.

```powershell
# Don't:
Write-Host "Found $($items.Count) items"; Write-Host $items     # uncapturable

# Do:
Write-Verbose "Found $($items.Count) items"                     # opt-in message
$items                                                          # the data
```

## Verbose / Warning / Debug are free with `[CmdletBinding()]`

Because advanced functions inherit the common parameters, `Write-Verbose` output
appears only when the caller passes `-Verbose` (or sets `$VerbosePreference`).
This gives you tunable logging without polluting normal output:

```powershell
function Sync-Data {
    [CmdletBinding()]
    param([string] $Source)
    Write-Verbose "Reading from $Source"      # silent unless -Verbose
    Write-Warning "Source is large"           # shown by default, but on stream 3
    # ... emit result objects ...
}
```

## Redirection & capture

Streams can be redirected by number; data is captured by assignment:

```powershell
$data = Get-Stuff                 # captures stream 1 (data) only
Get-Stuff *> output.txt           # all streams to a file
Get-Stuff 2> errors.txt           # just errors
Get-Stuff 3>$null                 # discard warnings
$data = Get-Stuff 2>&1            # merge errors into the captured output (use sparingly)
```

## Rules of thumb

- Functions emit **objects** on stream 1; everything human goes to verbose/
  warning/information.
- Never use `Write-Host` to return data; reserve it for intentional interactive
  console text.
- Wrap output in `[pscustomobject]` so callers can process it.
- Suppress accidental output with `$null = …`.
