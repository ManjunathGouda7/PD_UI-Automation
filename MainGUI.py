"""
Desktop Application Entrypoint for GRL USB PD C2 UI Automation.
Features real-time Pytest results collection, live logging, and dynamic report generation.
"""
from datetime import datetime
import os
from pathlib import Path
import sys
import time

# Ensure root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from PyQt6.QtCore import QThread, pyqtSignal  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402
import pytest  # noqa: E402

from Scripts.UI.Excel_Report import generate_excel_report  # noqa: E402
from Scripts.UI.HTML_Report import generate_html_report  # noqa: E402
from Scripts.UI.app import MainWindow  # noqa: E402


class PytestExecutionCollector:
    """
    Pytest plugin hook that intercepts real test outcomes during execution.
    """

    def __init__(self, log_callback=None):
        self.test_cases = []
        self.start_time = None
        self.end_time = None
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.log_callback = log_callback

    def pytest_sessionstart(self, session):
        self.start_time = time.time()

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            duration = f"{report.duration:.2f}s"
            status = "PASSED" if report.passed else ("FAILED" if report.failed else "SKIPPED")
            remarks = "Test passed"
            if report.failed:
                self.failed += 1
                remarks = str(report.longrepr).splitlines()[-1] if report.longrepr else "Assertion Error"
                if self.log_callback:
                    self.log_callback(f"[FAIL] {report.nodeid} ({duration}) - {remarks}")
            elif report.passed:
                self.passed += 1
                remarks = "Test passed successfully"
                if self.log_callback:
                    self.log_callback(f"[PASS] {report.nodeid} ({duration})")
            else:
                self.skipped += 1
                remarks = "Test skipped"
                if self.log_callback:
                    self.log_callback(f"[SKIP] {report.nodeid}")

            self.test_cases.append({
                "TC_ID": report.nodeid,
                "TC_Result": status,
                "TC_Execution_Duration": duration,
                "TC_Remarks": remarks,
            })
        elif report.when == "setup" and report.failed:
            self.failed += 1
            duration = f"{report.duration:.2f}s"
            remarks = str(report.longrepr).splitlines()[-1] if report.longrepr else "Fixture setup failed"
            if self.log_callback:
                self.log_callback(f"[ERROR] {report.nodeid} (Setup Failed) - {remarks}")
            self.test_cases.append({
                "TC_ID": report.nodeid,
                "TC_Result": "FAILED (Setup)",
                "TC_Execution_Duration": duration,
                "TC_Remarks": remarks,
            })

    def pytest_sessionfinish(self, session, exitstatus):
        self.end_time = time.time()

    def get_report_data(self, report_name="USB_PD_C2_Run", dut_ip="192.168.102.76"):
        total_seconds = int(self.end_time - self.start_time) if (self.start_time and self.end_time) else 0
        mins, secs = divmod(total_seconds, 60)
        hours, mins = divmod(mins, 60)
        total_time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"

        total_tests = len(self.test_cases)
        return {
            "Report Name": report_name,
            "DUT_IP": dut_ip,
            "Total Tests": total_tests,
            "Passed": self.passed,
            "Failed": self.failed,
            "Total Time": total_time_str,
            "Test Cases": self.test_cases if self.test_cases else [
                {"TC_ID": "No_Tests_Executed", "TC_Result": "SKIPPED", "TC_Execution_Duration": "0.0s", "TC_Remarks": "No test items collected"}
            ],
        }


class TestRunnerThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()

    def __init__(self, test_args, dut_ip="192.168.102.76"):
        super().__init__()
        self.test_args = test_args
        self.dut_ip = dut_ip

    def run(self):
        self.log_signal.emit("[INFO] Launching pytest with arguments: " + " ".join(self.test_args))
        collector = PytestExecutionCollector(log_callback=self.log_signal.emit)

        exit_code = pytest.main(self.test_args, plugins=[collector])
        self.log_signal.emit(f"[INFO] Pytest completed with exit code: {exit_code}")
        self.progress_signal.emit(90)

        # Generate Real Dynamic Reports
        reports_dir = ROOT_DIR / "Reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_out = reports_dir / f"PD_Report_{ts}.html"
        excel_out = reports_dir / f"PD_Report_{ts}.xlsx"

        report_data = collector.get_report_data(
            report_name=f"USB_PD_C2_Run_{ts}",
            dut_ip=self.dut_ip,
        )

        try:
            generate_html_report(report_data, str(html_out))
            generate_excel_report(report_data, str(excel_out))
            self.log_signal.emit(f"[SUCCESS] Real-time HTML report: {html_out}")
            self.log_signal.emit(f"[SUCCESS] Real-time Excel report: {excel_out}")
        except Exception as e:
            self.log_signal.emit(f"[WARNING] Report generation failed: {e}")

        self.progress_signal.emit(100)
        self.finished_signal.emit()


class GUIController:
    def __init__(self, window: MainWindow):
        self.window = window
        self.runner = None

    def start_execution(self):
        workers = self.window.workers_combo.currentText()
        retries = self.window.retries_combo.currentText()
        is_headless = self.window.headless_chk.isChecked()
        dut_ip = self.window.ip_input.text().strip()

        os.environ["HEADLESS"] = "true" if is_headless else "false"

        args = ["-c", "Configurations/pytest.ini", "Scripts/TestCases"]
        if int(workers) > 1:
            args.extend(["-n", workers, "--dist=loadfile"])
        if int(retries) > 0:
            args.extend(["--reruns", retries, "--reruns-delay", "2"])

        self.runner = TestRunnerThread(args, dut_ip=dut_ip)
        self.runner.log_signal.connect(self.window.log_view.append)
        self.runner.progress_signal.connect(self.window.progress_bar.setValue)
        self.runner.finished_signal.connect(lambda: self.window.run_btn.setEnabled(True))

        self.window.run_btn.setEnabled(False)
        self.window.progress_bar.setValue(10)
        self.runner.start()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    controller = GUIController(window)
    window.controller = controller
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
