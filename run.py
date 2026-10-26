"""
Unified CLI for the GRL USB PD C2 (V-DPWR-EPR) automation suite.

Examples:
  python run.py                       # smoke suite (read-only, UI + API)
  python run.py --mode api            # REST API suite only (no browser)
  python run.py --mode full           # everything that is safe to run (read-only)
  python run.py --mode full --allow-hw-actions --strict-hardware   # include tests that drive the tester
  python run.py --smart               # suites affected by your git changes
  python run.py --mode api --mock     # API suite against the offline mock
  python run.py --serve-mock          # just run the mock API server on :5003
  python run.py --gui                 # PyQt6 desktop runner
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

REPORTS_DIR = ROOT_DIR / "Reports"


def build_pytest_cmd(args: argparse.Namespace) -> list[str]:
    cmd = [sys.executable, "-m", "pytest"]
    marker_parts: list[str] = []

    if args.smart:
        from Scripts.Helpers.smart_test_selector import select_tests
        selected = select_tests()
        print(f"[SMART] {len(selected)} suite(s): {', '.join(selected)}")
        cmd.extend(selected)
    elif args.mode in ("api", "smoke"):
        marker_parts.append(args.mode)
    # full / regression: everything under testpaths

    if args.markers:
        marker_parts.append(f"({args.markers})")
    if marker_parts:
        cmd.extend(["-m", " and ".join(marker_parts)])
    if args.keyword:
        cmd.extend(["-k", args.keyword])
    if args.workers > 1:
        # The UI shares one physical tester; parallel browsers would race on its state.
        print("[WARN] UI tests share one tester - parallel workers are only safe for API tests.")
        cmd.extend(["-n", str(args.workers), "--dist=loadfile"])
    if args.retries > 0:
        cmd.extend(["--reruns", str(args.retries), "--reruns-delay", "3"])
    if args.mock:
        cmd.append("--mock")
    if args.allow_hw_actions:
        cmd.append("--allow-hw-actions")
    if args.strict_hardware:
        cmd.append("--strict-hardware")
    if args.allure:
        cmd.append("--alluredir=allure-results")

    REPORTS_DIR.mkdir(exist_ok=True)
    cmd.extend([f"--junitxml={REPORTS_DIR / 'junit.xml'}", "-v"])
    return cmd


def run_tests(args: argparse.Namespace) -> int:
    if args.headless is not None:
        os.environ["HEADLESS"] = "true" if args.headless else "false"
    cmd = build_pytest_cmd(args)
    print("[COMMAND] " + " ".join(cmd))
    return subprocess.call(cmd, cwd=str(ROOT_DIR))


def launch_gui() -> int:
    return subprocess.call([sys.executable, str(ROOT_DIR / "MainGUI.py")], cwd=str(ROOT_DIR))


def serve_mock() -> int:
    from Scripts.Helpers.mock_server import MockC2Server
    server = MockC2Server(port=5003)
    if not server.start():
        print("[ERROR] Port 5003 is in use - the real C2 software is probably running.")
        return 1
    print("[MOCK] C2 API mock on http://127.0.0.1:5003 - Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GRL USB PD C2 (V-DPWR-EPR) test automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--mode", choices=["api", "smoke", "full", "regression"], default="smoke",
                        help="test selection profile (default: smoke)")
    parser.add_argument("--smart", action="store_true", help="select suites from git changes")
    parser.add_argument("-m", "--markers", help="extra pytest marker expression")
    parser.add_argument("-k", "--keyword", help="pytest -k expression")
    parser.add_argument("-w", "--workers", type=int, default=1, help="pytest-xdist workers (API tests only)")
    parser.add_argument("-r", "--retries", type=int, default=0, help="reruns for failed tests")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=None,
                        help="run the browser headless (default from HEADLESS env / config)")
    parser.add_argument("--mock", action="store_true", help="run against the offline API mock")
    parser.add_argument("--allow-hw-actions", action="store_true",
                        help="enable tests that change tester state (connect, apply config, ...)")
    parser.add_argument("--strict-hardware", action="store_true",
                        help="fail instead of skip when a needed tester is not connected")
    parser.add_argument("--allure", action="store_true", help="write Allure results to allure-results/")
    parser.add_argument("--gui", action="store_true", help="launch the PyQt6 desktop runner")
    parser.add_argument("--serve-mock", action="store_true", help="run the mock API server in the foreground")
    args = parser.parse_args()

    if args.gui:
        sys.exit(launch_gui())
    if args.serve_mock:
        sys.exit(serve_mock())
    sys.exit(run_tests(args))


if __name__ == "__main__":
    main()
