# CLAUDE.md

Engineering constitution for this repository. Read once; applies every turn.
This is the only context that pays rent on every turn — keep it minimal.

## Identity
- **F# is the engineering surface.** Write idiomatic F#, not F# shaped like C#.
- ⚠️ Flag any C#-ism that leaks into F# output: `null`, mutable scaffolding,
  exceptions as control flow, a class where a DU or record suffices, an
  imperative loop where a fold or recursion reads truer.

## Discipline floor (non-negotiable)
- Parse, don't validate. Make illegal states unrepresentable.
- Types are the specification. Give the signature before the implementation.
- DUs over class hierarchies. Records over bags of mutable fields.
- `Result` / `Option` over exceptions. No partial functions on public
  boundaries — total, or it doesn't ship.
- Property tests (FsCheck / Expecto) are the proof obligation, not an extra.
- Pure core, effectful shell. Lineage and telemetry via Writer, not side-channels.

## How to work here
- Smallest correct change. No speculative abstraction.
- If a constraint can be encoded in a type, encode it — don't document it.
- When unsure, ask for the signature, not the feature.

## Where deep context lives — pull these, do not inline
- Oracle → ES type / constraint mapping  →  skill `oracle-es-mapping`
- ES CDC sink (BulkOp DU algebra)         →  skill `es-sink`
- ES bulk load (byte-budget chunk, 429)   →  skill `es-bulk-load`
- F# / .NET 10 language + library guide   →  skill `fsharp-field-guide`
- Triage when something breaks            →  workflow `/the-descent`

## Do not restate
Stack, project layout, and dependencies are declared in the repo and are
inferable. Do not copy them here. This file holds only what the code cannot
tell you.
