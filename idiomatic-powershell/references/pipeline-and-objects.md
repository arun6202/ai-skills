# The object pipeline

The single idea that makes PowerShell PowerShell: cmdlets emit **objects**, and
the pipeline passes those objects (not text) to the next stage. You filter,
transform, and shape typed data by its *properties* — never by parsing strings.
Internalize this and most "how do I…" questions answer themselves.

## Objects, not text

Output from a cmdlet is a stream of .NET objects with real properties and methods:

```powershell
Get-Process |
    Where-Object CPU -GT 100 |          # filter on a typed property
    Sort-Object CPU -Descending |
    Select-Object -First 5 Name, CPU    # pick properties
```

Compare to a traditional shell, where you'd `grep`/`awk`/`cut` columns out of
text. In PowerShell, reaching for `-split`/regex on cmdlet output is a smell — the
data you want is already a property. Discover properties with `Get-Member`:

```powershell
Get-Process | Get-Member          # see every property and method available
```

Parse text only at the genuinely untyped edges (a log file, a CLI that returns
strings), and convert to objects as early as possible
(`ConvertFrom-Json`/`-Csv`/`-StringData`, `Import-Csv`, `[regex]` into a
`[pscustomobject]`).

## The core pipeline cmdlets

| Cmdlet            | Does                              | Functional analogue |
|-------------------|----------------------------------|---------------------|
| `Where-Object`    | keep items matching a condition  | filter              |
| `ForEach-Object`  | transform / act on each item     | map / iter          |
| `Select-Object`   | pick or compute properties; `-First/-Last/-Unique` | project / take |
| `Sort-Object`     | order by properties              | sort                |
| `Group-Object`    | bucket by a key                  | groupBy             |
| `Measure-Object`  | count/sum/avg/min/max            | fold / reduce       |
| `Select-Object -ExpandProperty` | unwrap one property to its raw values | map+flatten |

```powershell
Get-ChildItem -File |
    Group-Object Extension |
    Sort-Object Count -Descending |
    Select-Object Name, Count
```

### Filter left, format right

Two rules that keep pipelines fast and useful:

1. **Filter as early (left) as possible** — and prefer a cmdlet's own filtering
   parameter to a later `Where-Object`, because it filters at the source:
   ```powershell
   Get-ChildItem -Filter *.log        # better than: Get-ChildItem | Where Name -like '*.log'
   ```
2. **Format as late (right) as possible, and only for humans.** `Format-Table`/
   `Format-List` emit formatting objects that can't be processed further — they're
   terminal. Never return `Format-*` output from a function; return the objects and
   let the *caller* format at display time.

## `Where-Object` / `ForEach-Object`: two syntaxes

```powershell
# Script-block form (general): $_ (or $PSItem) is the current item
$procs | Where-Object { $_.CPU -gt 100 -and $_.Name -like 'pwsh*' }
$files | ForEach-Object { $_.Length / 1KB }

# Comparison form (simple single condition, very readable):
$procs | Where-Object CPU -GT 100
$svcs  | Where-Object Status -EQ 'Running'
```

Use the simple comparison form for one condition; the script-block form when you
need boolean logic or multiple properties.

## Calculated properties

`Select-Object` (and `Format-*`, `Sort-Object`) accept a hashtable to compute a
column — `Name`/`n` and `Expression`/`e`:

```powershell
Get-ChildItem -File |
    Select-Object Name,
                  @{ Name = 'SizeMB'; Expression = { [math]::Round($_.Length / 1MB, 2) } },
                  @{ Name = 'Age';    Expression = { (Get-Date) - $_.LastWriteTime } }
```

## The `.Where()` and `.ForEach()` methods

Collections expose intrinsic methods that run eagerly (no pipeline overhead) —
handy for in-memory arrays and with extra modes:

```powershell
$running = $services.Where({ $_.Status -eq 'Running' })
$squares = (1..10).ForEach({ $_ * $_ })

# modes: First, Last, SkipUntil, Until, Split
$first = $services.Where({ $_.Status -eq 'Running' }, 'First', 1)
```

Pipeline (`|`) streams item-by-item and is the idiom for cmdlet output and large
or lazy sources; the `.Where()`/`.ForEach()` methods are faster for arrays you
already hold and read cleanly for simple cases.

## Stream — don't accumulate with `+=`

Appending to an array in a loop (`$a += $x`) reallocates the whole array every
time — O(n²). Instead, let the pipeline or loop *output* values and collect once:

```powershell
# Idiomatic: the loop's output becomes the array
$results = foreach ($item in $input) {
    Get-Thing $item
}

# Or pipe straight on without ever materializing:
$input | ForEach-Object { Get-Thing $_ } | Where-Object IsValid

# If you must grow incrementally, use a typed list:
$list = [System.Collections.Generic.List[object]]::new()
$list.Add($x)
```

## Enumerate-or-scalar gotcha

A pipeline that yields one object returns that object, not a 1-element array. If
downstream code assumes an array, force it: `@(Get-Thing)` guarantees an array, and
`($x | Measure-Object).Count` counts safely. With `Set-StrictMode` on, indexing a
scalar as if it were an array will surface the mistake.
