"""
Desktop entry point for GRL USB PD C2 UI Automation.
Runs the selected tests in a worker thread, streams results live, and writes HTML/Excel reports.
"""
import os
from pathlib import Path
import sys
import time

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from PyQt6.QtCore import QThread, pyqtSignal  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402
import pytest  # noqa: E402

from Scripts.Helpers import reporting  # noqa: E402
from Scripts.Helpers.config import Config  # noqa: E402
from Scripts.UI.app import MainWindow  # noqa: E402


class PytestExecutionCollector:
    """Pytest plugin that records the real outcome of every test (setup, call and teardown)."""

    def __init__(self, log_callback=None, status_callback=None, progress_callback=None):
        self.results: dict[str, dict] = {}
        self.start_time = None
        self.end_time = None
        self.log_callback = log_callback
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        self.total = 0
        self.done = 0

    def _log(self, msg: str) -> None:
        if self.log_callback:
            self.log_callback(msg)

    def _status(self, node_id: str, status: str) -> None:
        if self.status_callback:
            self.status_callback(node_id, status)

    def pytest_sessionstart(self, session):
        self.start_time = time.time()

    def pytest_collection_finish(self, session):
        self.total = len(session.items)

    def pytest_runtest_logstart(self, nodeid, location):
        self._status(nodeid, "RUNNING")

    def pytest_runtest_logfinish(self, nodeid, location):
        self.done += 1
        if self.progress_callback and self.total:
            self.progress_callback(5 + int(90 * self.done / self.total))

    def pytest_runtest_logreport(self, report):
        entry = self.results.setdefault(report.nodeid, {
            "TC_ID": report.nodeid, "TC_Result": "PASSED", "duration": 0.0, "TC_Remarks": "",
        })
        entry["duration"] += report.duration

        if report.skipped:
            xfail = hasattr(report, "wasxfail")
            entry["TC_Result"] = "XFAIL" if xfail else "SKIPPED"
            if xfail:
                entry["TC_Remarks"] = report.wasxfail
            elif isinstance(report.longrepr, tuple):
                entry["TC_Remarks"] = str(report.longrepr[2])
            self._log(f"[{entry['TC_Result']}] {report.nodeid} - {entry['TC_Remarks']}")
            self._status(report.nodeid, entry["TC_Result"])
        elif report.failed:
            phase = "" if report.when == "call" else f" ({report.when})"
            entry["TC_Result"] = "FAILED" if report.when == "call" else "ERROR"
            entry["TC_Remarks"] = (str(report.longrepr).splitlines() or ["failed"])[-1] + phase
            self._log(f"[{entry['TC_Result']}] {report.nodeid} - {entry['TC_Remarks']}")
            self._status(report.nodeid, entry["TC_Result"])
        elif report.when == "call":
            self._log(f"[PASS] {report.nodeid} ({report.duration:.2f}s)")
            self._status(report.nodeid, "PASSED")

    def pytest_sessionfinish(self, session, exitstatus):
        self.end_time = time.time()

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.results.values():
            out[r["TC_Result"]] = out.get(r["TC_Result"], 0) + 1
        return out


class TestRunnerThread(QThread):
    __test__ = False
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str, str)
    progress_signal = pyqtSignal(int)
    report_dir_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, test_args: list[str], dut_ip: str):
        super().__init__()
        self.test_args = test_args
        self.dut_ip = dut_ip

    def run(self):
        self.log_signal.emit("[INFO] pytest " + " ".join(self.test_args))
        collector = PytestExecutionCollector(log_callback=self.log_signal.emit,
                                             status_callback=self.status_signal.emit,
                                             progress_callback=self.progress_signal.emit)
        exit_code = pytest.main(self.test_args, plugins=[collector])
        self.log_signal.emit(f"[INFO] pytest finished with exit code {int(exit_code)}: {collector.counts()}")
        folder = reporting.current_run_dir()
        if folder:
            self.report_dir_signal.emit(str(folder))
            self.log_signal.emit(f"[SUCCESS] Reports: {folder}")
        self.progress_signal.emit(100)
        self.finished_signal.emit()


class GUIController:
    def __init__(self, window: MainWindow):
        self.window = window
        self.runner = None

    def start_execution(self, node_ids: list[str]):
        if not node_ids:
            self.window.log_view.append("[WARN] No tests selected.")
            return

        os.environ["HEADLESS"] = "true" if self.window.headless_chk.isChecked() else "false"
        dut_ip = self.window.ip_input.text().strip() or Config.dut_ip()
        os.environ["DUT_IP"] = dut_ip

        args = [*node_ids, "-p", "no:cacheprovider"]
        retries = int(self.window.retries_combo.currentText())
        if retries > 0:
            args.extend(["--reruns", str(retries), "--reruns-delay", "3"])
        if self.window.hw_actions_chk.isChecked():
            args.append("--allow-hw-actions")

        self.runner = TestRunnerThread(args, dut_ip=dut_ip)
        self.window.reset_statuses()
        self.runner.log_signal.connect(self.window.log_view.append)
        self.runner.status_signal.connect(self.window.set_test_status)
        self.runner.progress_signal.connect(self.window.progress_bar.setValue)
        self.runner.report_dir_signal.connect(self.window.set_last_report_dir)
        self.runner.finished_signal.connect(lambda: self.window.set_running(False))

        self.window.set_running(True)
        self.window.progress_bar.setValue(10)
        self.runner.start()


def main():
    os.chdir(ROOT_DIR)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.controller = GUIController(window)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
