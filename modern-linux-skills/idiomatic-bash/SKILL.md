---
name: idiomatic-bash
description: >-
  Write, refactor, or review idiomatic, safe shell scripts (.sh, bash) — even a
  quick "write a bash script for this" or a startup/CI snippet. Steers from the
  cheat-sheet's naive `#!/bin/bash` toward production shell: strict mode
  (`set -euo pipefail`), `trap`-based cleanup with `mktemp`, quoting and `[[ ]]`
  discipline, arrays over word-splitting, `$()` over backticks, `getopts` for
  flags, ShellCheck + shfmt in CI, and structured streams (process substitution,
  `jq`/`jc`/`yq`) instead of fragile text scraping. Also says *when not to use
  bash* — past ~100 lines or real data structures, reach for Python/Go. Reach for
  it on any shell script, pipe/redirection question (stdin/stdout/stderr), "parse
  this command output", glue/automation, or "make this script not break".
---

# Idiomatic Bash

Bash is the cheat-sheet's `#!/bin/bash`, `NAME="Linux"`, `for`, `if`, `$0`/`$1` —
and that's exactly how scripts end up silently corrupting data. The default shell
*keeps going after an error*, *splits unquoted variables on whitespace*, and
*hides failures in the middle of a pipe*. Idiomatic bash is mostly about turning
those footguns off and treating streams as data, not as text to eyeball.

> **Prime directive: fail loud, quote everything, and prefer structure.** A good
> script stops at the first error, never word-splits a path, cleans up after
> itself, and passes JSON through `jq` rather than `awk`-ing column 3.

> **Part of the `idiomatic-code` family** — the cross-language creed
> (illegal-states-unrepresentable, errors-as-values, pipelines-over-loops) lives
> in `idiomatic-code`. Bash can't enforce types, so it leans hard on *discipline*
> and *external linters* to get the same safety.

## Break the muscle memory (reflex → idiomatic)

| Reflex (cheat-sheet habit)              | Idiomatic bash                                                      |
|-----------------------------------------|--------------------------------------------------------------------|
| `#!/bin/bash` then dive in              | `#!/usr/bin/env bash` + `set -euo pipefail` + `IFS=$'\n\t'`         |
| `rm $file`                              | `rm -- "$file"` — always quote; `--` ends option parsing           |
| `if [ "$x" = foo ]`                     | `if [[ $x == foo ]]` — `[[ ]]` is safer, supports `&&`, globs, `=~` |
| `` x=`cmd` ``                           | `x=$(cmd)` — nests cleanly, no backtick escaping                    |
| `for f in $(ls *.log)`                  | `for f in *.log` (glob) or `find ... -print0 | while IFS= read -r -d ''` |
| `cat file | grep x | wc -l`             | `grep -c x file` — drop the useless `cat`, let tools read files     |
| Temp file at `/tmp/out`                 | `tmp=$(mktemp)` + `trap 'rm -f "$tmp"' EXIT` (cleanup guaranteed)   |
| Positional `$1 $2 $3`                   | `getopts` for flags; validate and default with `${1:?msg}`          |
| Build a list in a string               | use a bash **array**: `files=(); files+=("$f"); "${files[@]}"`      |
| Parse `ip`/`docker`/`systemctl` text   | use `--json`/`-j` + `jq`, or pipe through `jc` to get JSON          |
| `echo $var` (may glob/split)           | `printf '%s\n' "$var"` — predictable, no `-e`/escape surprises      |
| Ship it untested                        | run `shellcheck script.sh` and `shfmt -d script.sh` in CI           |
| 300-line bash with nested data          | stop — rewrite in Python/Go; bash has no real data structures       |

## The creed

1. **Strict mode, always.** `set -euo pipefail`: exit on error (`-e`), error on
   unset variables (`-u`), and make a pipeline fail if *any* stage fails
   (`pipefail`) — not just the last. Set `IFS=$'\n\t'` to stop word-splitting on
   spaces. This single header prevents most real-world shell disasters.
2. **Quote every expansion.** `"$var"`, `"${arr[@]}"`, `"$(cmd)"`. Unquoted
   expansion is word-split and glob-expanded — the source of "it worked until a
   path had a space". Use `--` to stop a filename from being read as a flag.
3. **Clean up with `trap`.** Acquire temp files/dirs with `mktemp` and register
   `trap 'cleanup' EXIT INT TERM` so they're removed even on error or Ctrl-C.
   Idempotent, leak-free scripts are re-runnable scripts.
4. **Test conditions with `[[ ]]`, branch on exit status.** `[[ ]]` is the bash
   conditional (globs, `=~`, no word-split); reserve `[ ]`/`test` for strict POSIX
   sh. Check command success directly (`if mycmd; then`), not `$?` ladders.
5. **Use arrays for lists.** A space-joined string is not a list. Build with
   `arr+=(x)` and expand with `"${arr[@]}"` to preserve elements exactly.
6. **Streams carry data — keep it structured.** Avoid "Useless Use of Cat" and
   column-counting `awk`. Prefer native `--json` output + `jq`; convert legacy
   text tools to JSON with `jc` (`dig … | jc --dig`). See
   `references/streams-and-structured-data.md`.
7. **Let the toolchain enforce it.** `shellcheck` (lint) and `shfmt` (format) in
   CI catch quoting, unset-var, and portability bugs you won't. Treat a
   ShellCheck warning like a compiler error.
8. **Know bash's ceiling.** Bash is glue. The moment you need maps, nested data,
   real error handling, or it crosses ~100 lines, rewrite in Python/Go. Choosing
   *not* to use bash is itself idiomatic.

## The canonical header

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

cleanup() { rm -rf "${tmpdir:-}"; }
trap cleanup EXIT INT TERM

tmpdir=$(mktemp -d)

usage() { printf 'usage: %s -i INPUT [-v]\n' "${0##*/}" >&2; exit 2; }

verbose=0
while getopts ':i:v' opt; do
  case $opt in
    i) input=$OPTARG ;;
    v) verbose=1 ;;
    *) usage ;;
  esac
done
: "${input:?-i INPUT is required}"   # fail fast if unset
```

## Redirection & pipes (cheat-sheet #5, modernized)

The three streams — stdin (0), stdout (1), stderr (2) — and `>`, `>>`, `2>`,
`2>&1` are the foundation. The SOTA additions:

```bash
cmd > out.log 2> err.log        # split streams
cmd &> all.log                  # bash: both to one file (clearer than 2>&1)
cmd 2>&1 | tee run.log          # see output AND capture it
diff <(sort a) <(sort b)        # process substitution: feed cmd output as a file
while IFS= read -r line; do …; done < <(cmd)   # read cmd output without subshell
mapfile -t lines < file         # slurp a file into an array, safely
```

Process substitution (`<(...)`, `>(...)`) and `< <(...)` avoid the classic
"variable set in a piped `while` vanishes" subshell trap. For turning command
output into *data*, see the references file. Full SOTA pipelines for system tools
(`ip -j`, `ss -O`, `journalctl -o json`) appear in their topic skills.
