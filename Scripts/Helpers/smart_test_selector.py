"""
Smart test selection: picks test suites affected by the files changed in git.
"""
import subprocess

SUITES = "Scripts/TestCases"

# Changing any of these affects every suite.
GLOBAL_PATTERNS = [
    "Scripts/conftest.py", "Scripts/Pages/base_page.py", "Scripts/Pages/app_page.py",
    "Scripts/Helpers/Locators.py", "Scripts/Helpers/config.py", "Scripts/Helpers/popups.py",
    "Scripts/Helpers/reporting.py", "Scripts/Helpers/waits.py",
    "pyproject.toml", "requirements.txt",
]

PANEL_MAPPINGS = {
    "test_00_app_shell.py": ["app_page.py", "test_00_app_shell.py"],
    "test_01_connection.py": ["connection_page.py", "test_01_connection.py"],
    "test_02_product_cap.py": ["product_capability_page.py", "test_02_product_cap.py"],
    "test_03_test_config.py": ["test_config_page.py", "test_03_test_config.py"],
    "test_04_results.py": ["results_page.py", "test_04_results.py"],
    "test_05_report.py": ["report_page.py", "test_05_report.py"],
    "test_06_configure.py": ["configure_page.py", "test_06_configure.py"],
    "test_07_loopback.py": ["loopback_page.py", "test_07_loopback.py"],
    "test_08_help.py": ["help_page.py", "test_08_help.py"],
    "test_10_e2e_execution.py": ["test_10_e2e_execution.py"],
    "test_09_api.py": ["api_client.py", "swagger_contract.py", "mock_server.py", "test_09_api.py", "Inputs.json"],
}
FALLBACK = [f"{SUITES}/test_00_app_shell.py", f"{SUITES}/test_09_api.py"]


def _git_lines(*args: str) -> list[str]:
    try:
        res = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    except OSError:
        return []
    return res.stdout.splitlines() if res.returncode == 0 else []


def get_changed_files() -> list[str]:
    """Uncommitted + untracked changes; falls back to the last commit when the tree is clean."""
    files = set(_git_lines("diff", "--name-only", "HEAD"))
    files.update(_git_lines("ls-files", "--others", "--exclude-standard"))
    if not files:
        files.update(_git_lines("diff", "--name-only", "HEAD~1", "HEAD"))
    return sorted(f.replace("\\", "/") for f in files if f.strip())


def select_tests() -> list[str]:
    changed = get_changed_files()
    if any(any(g in f for g in GLOBAL_PATTERNS) for f in changed):
        return [SUITES]

    selected = {
        f"{SUITES}/{suite}"
        for f in changed
        for suite, patterns in PANEL_MAPPINGS.items()
        if any(p.lower() in f.lower() for p in patterns)
    }
    return sorted(selected) or FALLBACK


if __name__ == "__main__":
    print(" ".join(select_tests()))
