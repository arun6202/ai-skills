#!/usr/bin/env python3
"""Build the F# Working Set reference card.

Injects references/catalogue.json (the `categories` array) into
assets/card-template.html at the __CATALOGUE__ marker and writes a
standalone, dependency-free HTML file.

Usage:
    python3 scripts/build_card.py [OUTPUT_HTML] [--catalogue PATH] [--template PATH]

Defaults resolve relative to the skill root, so from anywhere inside the
skill you can run:  python3 scripts/build_card.py fsharp-working-set.html
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOGUE = SKILL_ROOT / "references" / "catalogue.json"
DEFAULT_TEMPLATE = SKILL_ROOT / "assets" / "card-template.html"
MARKER = "__CATALOGUE__"


def build(catalogue: Path, template: Path, out: Path) -> Path:
    data = json.loads(catalogue.read_text(encoding="utf-8"))
    categories = data["categories"] if isinstance(data, dict) else data
    html = template.read_text(encoding="utf-8")
    count = html.count(MARKER)
    if count != 1:
        sys.exit(f"error: expected exactly 1 {MARKER!r} in {template}, found {count}")
    # json.dumps is valid JS array literal syntax; ensure_ascii keeps it portable.
    injected = json.dumps(categories, ensure_ascii=True)
    html = html.replace(f"const DATA = {MARKER};", f"const DATA = {injected};")
    out.write_text(html, encoding="utf-8")
    n = sum(len(c["items"]) for c in categories)
    print(f"built {out}  ({n} entries, {len(categories)} families, {len(html)} bytes)")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Build the F# Working Set reference card.")
    p.add_argument("output", nargs="?", default="fsharp-working-set.html",
                   help="output HTML path (default: ./fsharp-working-set.html)")
    p.add_argument("--catalogue", default=str(DEFAULT_CATALOGUE))
    p.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    a = p.parse_args()
    build(Path(a.catalogue), Path(a.template), Path(a.output))


if __name__ == "__main__":
    main()
