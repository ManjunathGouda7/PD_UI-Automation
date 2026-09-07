"""
Unified CLI & Automation Entrypoint for GRL USB PD C2 (V-DPWR-EPR).
Provides intuitive execution modes for API, Smoke, Full, Smart, and GUI workflows.
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


def run_tests(args: argparse.Namespace) -> int:
    """Executes pytest with configured options."""
    pytest_cmd = [sys.executable, "-m", "pytest", "-c", "Configurations/pytest.ini"]

    # Headless toggle
    if args.headless is not None:
        os.environ["HEADLESS"] = "true" if args.headless else "false"

    # Mock server flag
    if args.mock:
        os.environ["MOCK_SERVER"] = "true"

    # Selection mode
    if args.smart:
        from Scripts.Helpers.smart_test_selector import select_tests
        selected = select_tests()
        print(f"[SMART SELECT] Selected {len(selected)} test suite(s): {', '.join(selected)}")
        pytest_cmd.extend(selected)
    elif args.mode == "api":
        print("[RUNNER] Executing REST API Test Suite (Headless)...")
        pytest_cmd.extend(["Scripts/TestCases/test_09_api.py", "-m", "api"])
    elif args.mode == "smoke":
        print("[RUNNER] Executing Smoke Test Suite (UI + API)...")
        pytest_cmd.extend(["Scripts/TestCases", "-m", "smoke"])
    elif args.mode in ("full", "regression"):
        print("[RUNNER] Executing Complete 8-Panel Compliance Suite...")
        pytest_cmd.extend(["Scripts/TestCases"])

    # Parallel workers
    if args.workers and args.workers > 1:
        pytest_cmd.extend(["-n", str(args.workers), "--dist=loadfile"])

    # Retries for flaky tests
    if args.retries and args.retries > 0:
        pytest_cmd.extend(["--reruns", str(args.retries), "--reruns-delay", "2"])

    # Allure reporting
    if args.allure:
        pytest_cmd.extend(["--alluredir=allure-results"])

    pytest_cmd.append("-v")
    print("[COMMAND] " + " ".join(pytest_cmd))

    return subprocess.call(pytest_cmd, cwd=str(ROOT_DIR))


def launch_gui() -> int:
    """Launches the PyQt6 Desktop Test Runner."""
    print("[RUNNER] Launching PyQt6 Desktop GUI Test Runner...")
    gui_script = ROOT_DIR / "MainGUI.py"
    return subprocess.call([sys.executable, str(gui_script)], cwd=str(ROOT_DIR))


def start_mock() -> int:
    """Runs the standalone mock server in foreground."""
    from Scripts.Helpers.mock_server import MockC2Server
    print("[MOCK] Starting GRL USB PD C2 Mock Server on http://localhost:5003 ...")
    server = MockC2Server(port=5003)
    if server.start():
        print("[MOCK] Server running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.stop()
            print("[MOCK] Server stopped.")
        return 0
    else:
        print("[ERROR] Port 5003 is already in use. A live C2 server or another process is running.")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="GRL USB PD C2 (V-DPWR-EPR) Test Automation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py --mode api           # Run ultra-fast REST API test suite (<1s)
  python run.py --mode smoke         # Run quick UI & API sanity suite
  python run.py --mode full          # Run complete compliance test suite
  python run.py --smart              # Run test suites selected from git diff
  python run.py --gui                # Launch PyQt6 Desktop Runner
  python run.py --mock               # Start offline mock server on port 5003
  python run.py --mode smoke -w 2    # Run smoke tests across 2 parallel workers
        """
    )

    parser.add_argument(
        "--mode",
        choices=["api", "smoke", "full", "regression"],
        default="smoke",
        help="Test execution profile (default: smoke)"
    )
    parser.add_argument(
        "--smart",
        action="store_true",
        help="Smart test selection based on changed files in git diff"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the desktop PyQt6 GUI Runner"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Start the offline C2 Mock Server or force mock mode in tests"
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=1,
        help="Parallel pytest-xdist worker count (default: 1)"
    )
    parser.add_argument(
        "-r", "--retries",
        type=int,
        default=0,
        help="Number of reruns for failed tests (default: 0)"
    )
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Toggle headless browser execution"
    )
    parser.add_argument(
        "--allure",
        action="store_true",
        help="Generate Allure report results in allure-results/"
    )

    args = parser.parse_args()

    # Route commands
    if args.gui:
        sys.exit(launch_gui())

    # If user passed only --mock without --mode or other flags
    if args.mock and len(sys.argv) == 2:
        sys.exit(start_mock())

    sys.exit(run_tests(args))


if __name__ == "__main__":
    main()
