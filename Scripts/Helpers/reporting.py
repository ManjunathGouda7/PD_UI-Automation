"""
Run reporting: per-panel report folders and the pytest plugin that fills them.

Folder layout (one folder per run):
    Reports/<Panel>/<YYYY-MM-DD_HH-MM-SS>/          run of a single panel
        report.html, report.xlsx, summary.json
        fail_*.png, trace_*.zip                      failure artifacts
        downloads/                                   files downloaded by tests
    Reports/All_Panels/<timestamp>/                  run covering every panel
    Reports/Multiple_Panels/<timestamp>/             run covering some panels
        report.html, report.xlsx, summary.json       overall report
        <Panel>/report.html, report.xlsx, artifacts  one sub-folder per panel

Panel names come from the first docstring line of each test module, so the GUI,
CLI and report folders always agree.
"""
from __future__ import annotations

import ast
from datetime import datetime
from functools import cache
import json
import os
from pathlib import Path
import re
import time
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REPORTS_ROOT = ROOT_DIR / "Reports"
TEST_DIR = ROOT_DIR / "Scripts" / "TestCases"

_run_dir: Path | None = None
_multi_panel = False


# ----------------------------------------------------------------------------
# Naming
# ----------------------------------------------------------------------------

def safe_name(text: str) -> str:
    return re.sub(r"[^\w.-]+", "_", text).strip("_") or "run"


def short_name_from_title(title: str) -> str:
    """'Panel 1: Connection Setup' -> 'Connection Setup'; 'REST API: ...' -> 'REST API'."""
    match = re.match(r"Panel \d+:\s*(.+)", title)
    if match:
        return match.group(1)
    head = title.split(":", 1)[0].strip()
    return head[:1].upper() + head[1:]


@cache
def suite_title(module_file: str) -> str:
    """First docstring line of a test module ('Panel 1: Connection Setup')."""
    path = Path(module_file)
    try:
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
    except (OSError, SyntaxError):
        doc = ""
    lines = doc.strip().splitlines()
    return lines[0].rstrip(".") if lines else path.stem


def panel_name(module_file: str | Path) -> str:
    return short_name_from_title(suite_title(str(module_file)))


def humanize_test_name(name: str) -> str:
    """'test_TC_01_tester_info_table_has_all_fields[x]' -> 'TC_01 · Tester info table has all fields [x]'."""
    params = ""
    if "[" in name:
        name, params = name.split("[", 1)
        params = f" [{params}"
    body = name.removeprefix("test_")
    match = re.match(r"(TC_\d+)_(.*)", body)
    tc_id, words = (match.group(1), match.group(2)) if match else ("", body)
    text = words.replace("_", " ").strip()
    text = text[:1].upper() + text[1:]
    for acronym in ("api", "ui", "ip", "dut", "vif", "html", "url"):
        text = re.sub(rf"\b{acronym}\b", acronym.upper(), text, flags=re.IGNORECASE)
    return (f"{tc_id} · {text}" if tc_id else text) + params


# ----------------------------------------------------------------------------
# Folders
# ----------------------------------------------------------------------------

def run_dir() -> Path:
    """Folder of the current run (falls back to Reports/ outside a reporting session)."""
    path = _run_dir or Path(os.environ.get("RUN_REPORT_DIR", REPORTS_ROOT))
    path.mkdir(parents=True, exist_ok=True)
    return path


def current_run_dir() -> Path | None:
    """Folder of the current / most recent run in this process, if any."""
    return _run_dir


def panel_dir(module_file: str | Path) -> Path:
    """Where artifacts of a test from `module_file` go: the run folder, or its panel sub-folder."""
    path = run_dir() / safe_name(panel_name(module_file)) if _multi_panel else run_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def downloads_dir() -> Path:
    path = run_dir() / "downloads"
    path.mkdir(parents=True, exist_ok=True)
    return path


# ----------------------------------------------------------------------------
# Pytest plugin
# ----------------------------------------------------------------------------

class RunReporter:
    """Creates the run folder after collection and writes HTML/Excel/JSON reports at the end."""

    def __init__(self, config):
        self.config = config
        self.results: dict[str, dict[str, Any]] = {}
        self.order: list[str] = []
        self.started = time.time()

    # Folder is chosen once the selected tests are known.
    def pytest_collection_finish(self, session):
        global _run_dir, _multi_panel
        modules = {str(item.path) for item in session.items}
        all_modules = {str(p) for p in TEST_DIR.glob("test_*.py")}
        if len(modules) == 1:
            label = safe_name(panel_name(next(iter(modules))))
        elif modules and modules >= all_modules:
            label = "All_Panels"
        else:
            label = "Multiple_Panels"
        _multi_panel = len(modules) > 1
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        _run_dir = REPORTS_ROOT / label / stamp
        _run_dir.mkdir(parents=True, exist_ok=True)
        self.order = [item.nodeid for item in session.items]
        for item in session.items:
            self.results[item.nodeid] = {
                "panel": panel_name(item.path),
                "title": humanize_test_name(item.name),
                "result": "NOT RUN", "duration": 0.0, "remarks": "",
            }

    def pytest_runtest_logreport(self, report):
        entry = self.results.get(report.nodeid)
        if entry is None:
            return
        entry["duration"] += report.duration
        if report.skipped:
            if hasattr(report, "wasxfail"):
                entry["result"], entry["remarks"] = "XFAIL", report.wasxfail
            else:
                entry["result"] = "SKIPPED"
                entry["remarks"] = str(report.longrepr[2]) if isinstance(report.longrepr, tuple) else ""
        elif report.failed:
            entry["result"] = "FAILED" if report.when == "call" else "ERROR"
            lines = str(report.longrepr).strip().splitlines()
            entry["remarks"] = lines[-1] if lines else "failed"
        elif report.when == "call":
            entry["result"], entry["remarks"] = "PASSED", ""

    def pytest_sessionfinish(self, session, exitstatus):
        if _run_dir is None or not self.results:
            return
        from Scripts.Helpers.config import Config  # local import keeps plugin import cheap
        dut_ip = Config.dut_ip()
        elapsed = time.time() - self.started
        rows = [self.results[n] | {"node_id": n} for n in self.order]
        label = _run_dir.parent.name

        self._write(_run_dir, f"{label} - {_run_dir.name}", rows, dut_ip, elapsed)
        if _multi_panel:
            panels: dict[str, list[dict[str, Any]]] = {}
            for row in rows:
                panels.setdefault(row["panel"], []).append(row)
            for panel, panel_rows in panels.items():
                target = _run_dir / safe_name(panel)
                target.mkdir(exist_ok=True)
                self._write(target, f"{panel} - {_run_dir.name}", panel_rows, dut_ip,
                            sum(r["duration"] for r in panel_rows))
        terminal = self.config.pluginmanager.get_plugin("terminalreporter")
        if terminal:
            terminal.write_line(f"Reports written to: {_run_dir}")

    @staticmethod
    def _write(folder: Path, name: str, rows: list[dict[str, Any]], dut_ip: str, elapsed: float) -> None:
        from Scripts.UI.Excel_Report import generate_excel_report
        from Scripts.UI.HTML_Report import generate_html_report

        counts: dict[str, int] = {}
        for r in rows:
            counts[r["result"]] = counts.get(r["result"], 0) + 1
        hours, rem = divmod(int(elapsed), 3600)
        mins, secs = divmod(rem, 60)
        data = {
            "Report Name": name,
            "DUT_IP": dut_ip,
            "Total Tests": len(rows),
            "Passed": counts.get("PASSED", 0),
            "Failed": counts.get("FAILED", 0) + counts.get("ERROR", 0),
            "Skipped": counts.get("SKIPPED", 0) + counts.get("XFAIL", 0) + counts.get("NOT RUN", 0),
            "Total Time": f"{hours:02d}:{mins:02d}:{secs:02d}",
            "Test Cases": [{
                "TC_ID": f"{r['panel']} | {r['title']}",
                "TC_Result": r["result"],
                "TC_Execution_Duration": f"{r['duration']:.2f}s",
                "TC_Remarks": r["remarks"],
            } for r in rows],
        }
        generate_html_report(data, str(folder / "report.html"))
        generate_excel_report(data, str(folder / "report.xlsx"))
        (folder / "summary.json").write_text(
            json.dumps({k: v for k, v in data.items() if k != "Test Cases"} | {"counts": counts, "tests": rows},
                       indent=2), encoding="utf-8")


def register(config) -> None:
    """Called from conftest.pytest_configure; only the controlling process writes reports."""
    global _run_dir, _multi_panel
    if hasattr(config, "workerinput"):
        return
    _run_dir, _multi_panel = None, False  # the GUI runs several sessions in one process
    config.pluginmanager.register(RunReporter(config), "c2_run_reporter")
