"""
Requirements traceability: Test_Cases_Specification.txt <-> automated tests.

Each specification item gets an ID from its section prefix and number (e.g. "Connection Setup" #7
-> CONN-07). Tests link to items with `@pytest.mark.spec("CONN-07")`; `partial=True` marks tests
that check only part of the item. This script reads both statically (no test imports, no backend)
and writes:

    Reports/traceability/traceability.html   per-section coverage with the linked tests
    Reports/traceability/traceability.csv    one row per specification item

Usage:  python tools/traceability.py [--fail-on-unknown]
"""
from __future__ import annotations

import argparse
import ast
from collections import OrderedDict
import csv
from dataclasses import dataclass, field
import html
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SPEC_FILE = ROOT / "Test_Cases_Specification.txt"
TEST_DIR = ROOT / "Scripts" / "TestCases"
OUT_DIR = ROOT / "Reports" / "traceability"

SECTION_PREFIX = OrderedDict([
    ("General & Environment", "GEN"),
    ("Connection Setup", "CONN"),
    ("VIF & DUT Roles", "VIF"),
    ("Product Capability & Browser", "PCB"),
    ("Get Caps & Trace", "CAPS"),
    ("Test Config & MOI", "TCM"),
    ("Test Results & Protocol", "RES"),
    ("Configure & E-Load", "CFG"),
    ("EPR Emulation (REST API)", "EPR"),
    ("Report Generation", "RPT"),
    ("LoopBack", "LB"),
    ("Help & Diagnostics", "HELP"),
    ("Admin & Debug Mode", "ADM"),
    ("5-Port Testing", "P5"),
    ("VIF Mode & General", "VIFM"),
    ("License & MOI Filtering", "LIC"),
])


@dataclass
class SpecItem:
    id: str
    section: str
    text: str
    full: list[str] = field(default_factory=list)
    partial: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "Automated" if self.full else ("Partial" if self.partial else "Not automated")


def load_spec() -> OrderedDict[str, SpecItem]:
    items: OrderedDict[str, SpecItem] = OrderedDict()
    section = None
    for line in SPEC_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        cols = line.split("\t")
        if len(cols) < 3 or not cols[1].strip().isdigit():
            continue
        if cols[0].strip():
            section = cols[0].strip()
        prefix = SECTION_PREFIX.get(section)
        if prefix is None:
            raise SystemExit(f"Unknown specification section {section!r}: add it to SECTION_PREFIX")
        item_id = f"{prefix}-{int(cols[1]):02d}"
        items[item_id] = SpecItem(item_id, section, cols[2].strip())
    return items


def _spec_marks(decorators: list[ast.expr]) -> list[tuple[list[str], bool]]:
    marks = []
    for dec in decorators:
        if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == "spec"
                and isinstance(dec.func.value, ast.Attribute) and dec.func.value.attr == "mark"):
            ids = [a.value for a in dec.args if isinstance(a, ast.Constant)]
            partial = any(k.arg == "partial" and isinstance(k.value, ast.Constant) and k.value.value
                          for k in dec.keywords)
            marks.append((ids, partial))
    return marks


def load_links() -> list[tuple[str, list[str], bool]]:
    """[(test node id, spec ids, partial)] read from the test files."""
    links = []
    for path in sorted(TEST_DIR.glob("test_*.py")):
        rel = f"Scripts/TestCases/{path.name}"
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            functions = []
            if isinstance(node, ast.ClassDef):
                functions = [(f"{rel}::{node.name}::{fn.name}", fn) for fn in node.body if isinstance(fn, ast.FunctionDef)]
            elif isinstance(node, ast.FunctionDef):
                functions = [(f"{rel}::{node.name}", node)]
            for node_id, fn in functions:
                for ids, partial in _spec_marks(fn.decorator_list):
                    links.append((node_id, ids, partial))
    return links


def build() -> tuple[OrderedDict[str, SpecItem], list[str]]:
    items = load_spec()
    unknown = []
    for node_id, ids, partial in load_links():
        for spec_id in ids:
            if spec_id not in items:
                unknown.append(f"{spec_id} (in {node_id})")
                continue
            (items[spec_id].partial if partial else items[spec_id].full).append(node_id)
    return items, unknown


def write_reports(items: OrderedDict[str, SpecItem]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "traceability.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Spec ID", "Section", "Requirement", "Status", "Automated by", "Partially by"])
        for it in items.values():
            w.writerow([it.id, it.section, it.text, it.status, "; ".join(it.full), "; ".join(it.partial)])

    sections: OrderedDict[str, list[SpecItem]] = OrderedDict()
    for it in items.values():
        sections.setdefault(it.section, []).append(it)

    def pct(n: int, d: int) -> str:
        return f"{round(100 * n / d)}%" if d else "-"

    summary_rows, detail = [], []
    for name, its in sections.items():
        full = sum(1 for i in its if i.full)
        part = sum(1 for i in its if not i.full and i.partial)
        summary_rows.append(
            f"<tr><td>{html.escape(name)}</td><td>{len(its)}</td><td class='ok'>{full}</td>"
            f"<td class='part'>{part}</td><td class='none'>{len(its) - full - part}</td>"
            f"<td><div class='meter'><div style='width:{pct(full, len(its))}' class='m-ok'></div>"
            f"<div style='width:{pct(part, len(its))}' class='m-part'></div></div></td></tr>")
        rows = []
        for i in its:
            cls = {"Automated": "ok", "Partial": "part"}.get(i.status, "none")
            tests = "<br>".join(html.escape(t.split("::")[-1]) for t in i.full + i.partial)
            rows.append(f"<tr><td>{i.id}</td><td>{html.escape(i.text)}</td>"
                        f"<td class='{cls}'>{i.status}</td><td class='tests'>{tests}</td></tr>")
        detail.append(f"<h2>{html.escape(name)}</h2><table><tr><th>ID</th><th>Requirement</th>"
                      f"<th>Status</th><th>Tests</th></tr>{''.join(rows)}</table>")

    total = len(items)
    full = sum(1 for i in items.values() if i.full)
    part = sum(1 for i in items.values() if not i.full and i.partial)
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Spec traceability</title>
<style>
body {{ font-family:'Segoe UI',Roboto,sans-serif; background:#0a0b0f; color:#f8fafc; padding:24px; }}
h1 {{ color:#ff7800; }} h2 {{ color:#ff7800; margin-top:28px; font-size:18px; }}
table {{ border-collapse:collapse; width:100%; background:#131622; }}
th, td {{ border-bottom:1px solid #232936; padding:8px 10px; text-align:left; vertical-align:top; }}
th {{ color:#ff7800; font-size:12px; text-transform:uppercase; }}
.ok {{ color:#10b981; font-weight:700; }} .part {{ color:#f59e0b; font-weight:700; }} .none {{ color:#94a3b8; }}
.tests {{ font-family:Consolas,monospace; font-size:12px; color:#94a3b8; }}
.meter {{ display:flex; width:220px; height:10px; background:#232936; border-radius:5px; overflow:hidden; }}
.m-ok {{ background:#10b981; }} .m-part {{ background:#f59e0b; }}
.kpi {{ font-size:15px; margin-bottom:16px; }}
</style></head><body>
<h1>Specification traceability</h1>
<div class="kpi">{total} requirements &nbsp;|&nbsp; <span class="ok">{full} automated ({pct(full, total)})</span>
 &nbsp;|&nbsp; <span class="part">{part} partially ({pct(part, total)})</span>
 &nbsp;|&nbsp; <span class="none">{total - full - part} not automated</span></div>
<table><tr><th>Section</th><th>Items</th><th>Automated</th><th>Partial</th><th>Not automated</th><th>Coverage</th></tr>
{''.join(summary_rows)}</table>
{''.join(detail)}
</body></html>"""
    out = OUT_DIR / "traceability.html"
    out.write_text(page, encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fail-on-unknown", action="store_true", help="exit 1 if a test references an unknown spec ID")
    args = parser.parse_args()
    items, unknown = build()
    out = write_reports(items)
    total = len(items)
    full = sum(1 for i in items.values() if i.full)
    part = sum(1 for i in items.values() if not i.full and i.partial)
    print(f"{total} requirements: {full} automated, {part} partial, {total - full - part} not automated")
    print(f"Report: {out}")
    if unknown:
        print("Unknown spec IDs referenced by tests:\n  " + "\n  ".join(unknown))
        return 1 if args.fail_on_unknown else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
