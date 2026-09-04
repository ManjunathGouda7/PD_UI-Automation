"""
Smart Test Selection for GRL USB PD C2 UI Automation.
Analyzes Git diff to select relevant test suites based on changed files.
"""
import subprocess

PANEL_MAPPINGS = {
    "connection": ["Scripts/Pages/connection_page.py", "test_01_connection.py"],
    "product_cap": ["Scripts/Pages/product_capability_page.py", "test_02_product_cap.py"],
    "test_config": ["Scripts/Pages/test_config_page.py", "test_03_test_config.py"],
    "results": ["Scripts/Pages/results_page.py", "test_04_results.py"],
    "report": ["Scripts/Pages/report_page.py", "test_05_report.py"],
    "configure": ["Scripts/Pages/configure_page.py", "test_06_configure.py"],
    "loopback": ["Scripts/Pages/loopback_page.py", "test_07_loopback.py"],
    "help": ["Scripts/Pages/help_page.py", "test_08_help.py"],
}

def get_changed_files() -> list[str]:
    try:
        res = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip().splitlines()
    except Exception:
        pass
    return []

def select_tests() -> list[str]:
    changed = get_changed_files()
    if not changed:
        return ["Scripts/TestCases/test_01_connection.py"]

    selected = set()
    for file_path in changed:
        for panel, patterns in PANEL_MAPPINGS.items():
            if any(p in file_path for p in patterns):
                selected.add(f"Scripts/TestCases/{patterns[1]}")

    if not selected:
        return ["Scripts/TestCases/test_01_connection.py"]
    return sorted(list(selected))

if __name__ == "__main__":
    tests = select_tests()
    print(" ".join(tests))
