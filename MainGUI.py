"""
Desktop entry point for GRL USB PD C2 UI Automation.

Tests run in a child pytest process (QProcess) so a run can be stopped at any time and every
run starts clean. The `Scripts.UI.gui_events` plugin streams results back; reports are written
by the reporting plugin into Reports/<Panel>/<timestamp>/.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from PyQt6.QtCore import QObject, QProcess, QProcessEnvironment  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from Scripts.Helpers.config import Config  # noqa: E402
from Scripts.UI.app import MainWindow  # noqa: E402
from Scripts.UI.gui_events import EVENT_PREFIX  # noqa: E402


class GUIController(QObject):
    """Starts, monitors and stops the pytest child process for the window."""

    def __init__(self, window: MainWindow):
        super().__init__()
        self.window = window
        self.proc: QProcess | None = None
        self._buffer = ""
        self.total = 0
        self.done = 0
        self.stopping = False

    def is_running(self) -> bool:
        return self.proc is not None and self.proc.state() != QProcess.ProcessState.NotRunning

    def start_execution(self, node_ids: list[str]) -> None:
        if self.is_running():
            return
        if not node_ids:
            self.window.append_log("[WARN] No tests selected.")
            return

        w = self.window
        dut_ip = w.ip_input.text().strip() or Config.dut_ip()
        targets = ["Scripts/TestCases"] if set(node_ids) == set(w.all_node_ids()) else node_ids
        args = ["-m", "pytest", *targets, "-p", "Scripts.UI.gui_events", "-p", "no:cacheprovider",
                "-v", "--color=no", "-rA"]
        retries = int(w.retries_combo.currentText())
        if retries > 0:
            args += ["--reruns", str(retries), "--reruns-delay", "3"]
        if w.hw_actions_chk.isChecked():
            args.append("--allow-hw-actions")

        env = QProcessEnvironment.systemEnvironment()
        env.insert("HEADLESS", "true" if w.headless_chk.isChecked() else "false")
        env.insert("DUT_IP", dut_ip)
        env.insert("PYTHONUNBUFFERED", "1")
        env.insert("PYTHONIOENCODING", "utf-8")

        self.proc = QProcess(self)
        self.proc.setProcessEnvironment(env)
        self.proc.setWorkingDirectory(str(ROOT_DIR))
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._on_output)
        self.proc.finished.connect(self._on_finished)
        self.proc.errorOccurred.connect(self._on_error)

        self._buffer, self.total, self.done, self.stopping = "", len(node_ids), 0, False
        w.reset_statuses()
        w.set_last_report_dir("")
        w.log_view.clear()
        w.append_log(f"[INFO] Running {len(node_ids)} test(s) against tester {dut_ip}")
        w.progress_bar.setValue(2)
        w.set_running(True)
        self.proc.start(sys.executable, args)

    def stop(self) -> None:
        if not self.is_running():
            return
        self.stopping = True
        self.window.append_log("[INFO] Stopping test run...")
        pid = int(self.proc.processId())
        if os.name == "nt" and pid:
            # Kill the whole tree: pytest, the Playwright driver and Chrome.
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False)
        else:
            self.proc.kill()

    # ------------------------------------------------------------------

    def _on_output(self) -> None:
        self._buffer += bytes(self.proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        *lines, self._buffer = self._buffer.split("\n")
        for raw in lines:
            line = raw.rstrip("\r")
            # pytest -v prints "<test id> " and the outcome later on the same line, so an event
            # can arrive mid-line: split it off and keep the surrounding text for the log.
            if EVENT_PREFIX in line:
                before, _, payload = line.partition(EVENT_PREFIX)
                try:
                    self._on_event(json.loads(payload))
                except json.JSONDecodeError:
                    self.window.append_log(line)
                    continue
                self._pending_text = getattr(self, "_pending_text", "") + before
                continue
            text = getattr(self, "_pending_text", "") + line
            self._pending_text = ""
            if text.strip():
                self.window.append_log(text)

    def _on_event(self, event: dict) -> None:
        w = self.window
        kind = event.get("type")
        if kind == "collected":
            self.total = event["total"] or self.total
        elif kind == "start":
            w.set_test_status(event["nodeid"], "RUNNING")
        elif kind in ("result", "artifacts"):
            w.record_result(event)
        elif kind == "finish":
            self.done += 1
            if self.total:
                w.progress_bar.setValue(min(99, 2 + int(97 * self.done / self.total)))
        elif kind == "session_finish" and event.get("report_dir"):
            w.set_last_report_dir(event["report_dir"])
            w.append_log(f"[SUCCESS] Reports: {event['report_dir']}")

    def _on_finished(self, exit_code: int, _status) -> None:
        w = self.window
        if self.stopping:
            w.mark_unfinished_as_stopped()
            w.append_log("[INFO] Test run stopped.")
        else:
            w.progress_bar.setValue(100)
            w.append_log(f"[INFO] pytest finished (exit code {exit_code}).")
        w.set_running(False)
        w.update_backend_status()

    def _on_error(self, error) -> None:
        if not self.stopping:
            self.window.append_log(f"[ERROR] Could not run pytest: {error}")
            self.window.set_running(False)


def main():
    os.chdir(ROOT_DIR)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.controller = GUIController(window)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
