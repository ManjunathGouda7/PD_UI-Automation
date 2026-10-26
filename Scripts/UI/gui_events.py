"""
Pytest plugin used by the desktop runner (loaded with `-p Scripts.UI.gui_events`).

The GUI runs pytest in a child process so a run can be stopped at any time. This plugin
streams machine-readable events on stdout, one JSON object per line prefixed with
EVENT_PREFIX; every other stdout line is ordinary pytest output for the live log.
"""
from __future__ import annotations

import json
import sys
from typing import Any

EVENT_PREFIX = "@@C2EVENT@@ "


def _emit(event: dict[str, Any]) -> None:
    out = sys.__stdout__
    if out is None:
        return
    out.write(EVENT_PREFIX + json.dumps(event, default=str) + "\n")
    out.flush()


def pytest_collection_finish(session) -> None:
    _emit({"type": "collected", "total": len(session.items)})


def pytest_runtest_logstart(nodeid, location) -> None:
    _emit({"type": "start", "nodeid": nodeid})


def pytest_runtest_logreport(report) -> None:
    result = None
    message = ""
    if report.skipped:
        if hasattr(report, "wasxfail"):
            result, message = "XFAIL", report.wasxfail
        else:
            result = "SKIPPED"
            message = str(report.longrepr[2]) if isinstance(report.longrepr, tuple) else ""
    elif report.failed:
        result = "FAILED" if report.when == "call" else "ERROR"
        message = report.longreprtext or "failed"
    elif report.when == "call":
        result = "PASSED"

    artifacts = {k: v for k, v in report.user_properties if k in ("screenshot", "trace")}
    if result:
        _emit({"type": "result", "nodeid": report.nodeid, "when": report.when, "result": result,
               "duration": round(report.duration, 2), "message": message[-6000:], **artifacts})
    elif report.when == "teardown" and artifacts:
        _emit({"type": "artifacts", "nodeid": report.nodeid, **artifacts})


def pytest_runtest_logfinish(nodeid, location) -> None:
    _emit({"type": "finish", "nodeid": nodeid})


def pytest_sessionfinish(session, exitstatus) -> None:
    from Scripts.Helpers import reporting

    folder = reporting.current_run_dir()
    _emit({"type": "session_finish", "exitstatus": int(exitstatus), "report_dir": str(folder) if folder else ""})
