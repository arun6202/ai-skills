---
name: fsharp-working-set
description: >-
  Use when recommending an F# library, finding the F# equivalent of a Python
  library (pandas, numpy, requests, httpx, pydantic, FastAPI, Flask, Django,
  SQLAlchemy, pytest, hypothesis, click, celery, jupyter, sympy, etc.), choosing
  between F# options for a task (web framework, JSON/serialization, validation,
  SQL/ORM, testing, CLI, config, time, logging, concurrency, streaming, data,
  ML), or generating an F# library reference card. Provides a curated,
  discipline-driven Python->F# catalogue with NuGet ids, type-signature marks,
  package/tool/pattern kind, and use-when notes, plus a dark-ink HTML field-guide
  generator. Triggers on "F# library for X", "F# equivalent of <python lib>",
  "batteries for F#", "which F# <web framework / json / orm / test> library",
  "what does F# use instead of <lib>", or building an F# ecosystem reference.
---

# F# Working Set

A curated map of the F# ecosystem against Python's batteries, biased toward
idiomatic, strict-functional choices. The catalogue is the single source of
truth; the HTML card is a rendering of it.

## When this fires

- **Recommend a library** for a need ("what should I use in F# for HTTP / a
  web API / property tests / dataframes / Kafka / config binding").
- **Translate from Python** ("F# equivalent of requests / pandas / pydantic").
- **Choose between options** ("Falco vs Oxpecker vs Giraffe", "Dapper.FSharp vs
  Donald vs SqlHydra").
- **Produce a reference card** the person can keep or share.

## How to answer a recommendation

1. Read `references/catalogue.json`. It holds every entry: `name`, `id`
   (NuGet/tool id), `kind` (`package` | `tool` | `pattern`), `sig` (a stylized
   identifying type signature), and `use` (the one situation it's for).
2. Give the **name + exact `id` + one-line use-when**. Name the `kind` when it
   matters (a `tool` installs as a dotnet tool, not a package reference; a
   `pattern` is roll-your-own, not a dependency).
3. Apply the selection lens in `references/selection-guide.md`: favor idiomatic
   F# over thin C# interop, prefer Result/DUs/parse-don't-validate, and be
   honest about gaps instead of overselling.
4. **Verify currency before asserting "best", "active", or "maintained"**,
   especially for web frameworks and anything fast-moving — maintenance status
   shifts. Web-search to confirm, then state it.
5. The `sig` fields are **stylized marks, not compilable signatures**. Don't
   present them as exact type definitions.

## How to build the reference card

Run the build script; it injects the catalogue into the template and writes a
standalone, dependency-free HTML file (webfonts aside):

```
python3 scripts/build_card.py OUTPUT.html
```

Then present `OUTPUT.html`. The card is the person's dark-ink field-guide
system: specimen rows with copy-to-clipboard NuGet ids, the type-signature
mark, the use-when line, a kind tag, `/`-to-filter, and an inverted
"where Python still wins" doctrine block. It degrades gracefully on mobile and
respects reduced motion.

## How to extend or correct

Edit `references/catalogue.json` only — never hand-edit the generated HTML.
Each item is:

```json
{ "name": "Display Name", "id": "Exact.Nuget.Id", "kind": "package|tool|pattern",
  "sig": "stylized -> mark", "use": "the one situation it's for." }
```

Add or move items, then rebuild with the script. To add a whole category, append
an object with `cat`, `anchor` (the Python libraries it stands in for), and
`items`.

## Honesty contract

This is a field reference, not a leaderboard. Surface the real gaps (exploratory
data science, the deep scientific stack, pretrained-model ecosystems, glue-script
velocity) rather than pretending parity. F#'s win is typed, total, provable
pipelines — point there.
