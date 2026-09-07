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
    "api": ["api_client.py", "test_09_api.py", "Inputs.json"],
}


def get_changed_files() -> list[str]:
    """Inspects Git status for modified files in working directory or latest commit."""
    files = set()
    try:
        # 1. Check uncommitted / staged working changes
        res_work = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            check=False
        )
        if res_work.returncode == 0 and res_work.stdout.strip():
            files.update(res_work.stdout.strip().splitlines())

        # 2. Check untracked files
        res_untracked = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False
        )
        if res_untracked.returncode == 0 and res_untracked.stdout.strip():
            for line in res_untracked.stdout.strip().splitlines():
                parts = line.strip().split()
                if len(parts) >= 2:
                    files.add(parts[-1])

        # 3. Fallback to latest commit diff
        if not files:
            res_commit = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                capture_output=True,
                text=True,
                check=False
            )
            if res_commit.returncode == 0 and res_commit.stdout.strip():
                files.update(res_commit.stdout.strip().splitlines())
    except Exception:
        pass
    return list(files)


def select_tests() -> list[str]:
    """Returns list of test file paths matching recent changes."""
    changed = get_changed_files()
    if not changed:
        return ["Scripts/TestCases/test_01_connection.py", "Scripts/TestCases/test_09_api.py"]

    selected = set()
    for file_path in changed:
        normalized_path = file_path.replace("\\", "/")
        for panel, patterns in PANEL_MAPPINGS.items():
            if any(p.lower() in normalized_path.lower() for p in patterns):
                selected.add(f"Scripts/TestCases/{patterns[1]}")

    if not selected:
        return ["Scripts/TestCases/test_01_connection.py", "Scripts/TestCases/test_09_api.py"]
    return sorted(list(selected))


if __name__ == "__main__":
    tests = select_tests()
    print(" ".join(tests))
