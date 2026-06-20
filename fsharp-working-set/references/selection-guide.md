# Selection guide

The lens for turning a need into a recommendation. Read this alongside
`catalogue.json`.

## The lens (strict-functional bias)

- **Idiomatic F# over thin C# interop.** When an F#-native option exists and is
  healthy, prefer it (FsHttp over `HttpClient` ceremony; Argu over raw argv;
  NodaTime over `DateTime`). Reach into the C# ecosystem when the F# layer is
  thin (TorchSharp, Npgsql, ML.NET) and say so plainly.
- **Parse-don't-validate at the boundary.** Favor tools that return typed
  results (Validus, FSharp.Data type providers, FsConfig -> `Result`) over ones
  that mutate-and-throw.
- **Result over exceptions; DUs over class hierarchies.** Score a library up if
  it composes with `Result`/`Option` and models with unions; down if it forces
  exception-driven control flow or inheritance into otherwise pure code.
- **Pure core, effect at the edge.** Prefer libraries that keep computation pure
  and confine I/O (Expecto tests-as-values; Equinox deciders; Propulsion's
  scheduler) over ones that thread side effects through everything.
- **One honest caveat beats three features.** If a pick has a real cost (a C#
  fluent layer in the middle of a pure pipeline, an unmaintained stretch, a
  serializer that leans on reflection), name it.

## Currency — verify before asserting

Treat "best / active / maintained / latest version" as **time-sensitive
claims**. The web-framework corner especially has moved: Giraffe went dormant
and came back under new maintenance; Oxpecker emerged as its successor; Falco
shipped a major release with HTMX + OpenAPI. Before stating any such claim,
web-search to confirm the current state, then say it. The catalogue captures a
snapshot, not a live feed.

## Type-signature marks are stylized

The `sig` on each entry is an *identifying mark* — it telegraphs the shape of
the library's central idea (e.g. `result { } : Result<'ok,'err>`,
`HttpHandler = HttpContext -> Task`). It is **not** a compilable type
definition and should never be presented as one. It exists so a reader who
thinks in signatures can recognize a tool at a glance.

## Kinds

- `package` — a normal NuGet `PackageReference`.
- `tool` — installed as a dotnet tool (`dotnet tool install`) or run as CLI /
  build task, not referenced as a library (e.g. Fantomas, SqlHydra,
  .NET Interactive). Say this when recommending, so the person doesn't add a
  package reference by mistake.
- `pattern` — roll-your-own discipline, not a dependency (e.g. a `Refined<'T,'P>`
  phantom-type wrapper). Recommend the *approach*, not an install.

## Honest gaps (don't oversell)

Where Python still wins outright, and reaching for .NET interop is a compromise:

- **Exploratory data science** — pandas/seaborn muscle memory and notebook
  density. Deedle + Plotly.NET are good; the surrounding ecosystem is not.
- **The scientific stack** — scipy/statsmodels breadth. Math.NET and FSharp.Stats
  cover the common path, not the long tail.
- **Pretrained-model ecosystems** — grab-a-model-and-go. TorchSharp/ML.NET work,
  but the model zoo and tutorials live in Python.
- **Glue-script velocity** — throwaway one-file scripts. `.fsx` is real, but the
  dynamic-glue corner is Python's home turf.

State the trade: F# wins when the pipeline itself must be typed, total, and
provable. Direct the person there rather than claiming parity everywhere.

## Recommendation shape (what a good answer looks like)

> For HTTP from F#, use **FsHttp** (`FsHttp`, package). Its `http { }` CE makes
> requests genuinely pleasant and returns `Async<Response>`, so it composes with
> your Result pipeline. If you only need a one-off call inside existing
> ASP.NET-style code, the raw `HttpClient` is fine — but for anything you'll
> maintain, FsHttp is the idiomatic pick.

Name, exact id, kind, the use-when, one honest caveat. No marketing.
