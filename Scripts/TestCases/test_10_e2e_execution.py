"""
End-to-End: execute a compliance test and verify results and report.

Drives the tester (runs a real compliance test, clears previous results), so it is marked
`hardware` + `requires_tester` and only runs with --allow-hw-actions. The test case is taken
from jsons/test_data.json "e2e_execution" (override with env E2E_TEST_KEY); choose one that
suits the DUT connected to the bench.
"""
import os
import time

from playwright.sync_api import Page
import pytest

from Scripts.Data.test_data_manager import test_data_manager
from Scripts.Helpers.api_client import C2ApiClient
from Scripts.Helpers.logger import logger
from Scripts.Pages.report_page import ReportPage
from Scripts.Pages.results_page import ResultsPage

E2E = test_data_manager.section("e2e_execution")
FINAL_RESULTS = {"PASS", "FAIL", "INCOMPLETE", "WARNING", "SKIPPED", "NA", "ABORTED", "NOT_EXECUTED"}


def _leaf_keys(nodes) -> list[str]:
    keys = []
    for n in nodes:
        keys += _leaf_keys(n["children"]) if n.get("children") else [n["key"]]
    return keys


def _wait_for_app_state(api: C2ApiClient, wanted: str, timeout_s: float) -> str:
    deadline = time.monotonic() + timeout_s
    state = ""
    while time.monotonic() < deadline:
        state = api.get_app_state().get("appState", "")
        if state == wanted:
            return state
        time.sleep(2)
    return state


def _flatten(results) -> list[dict]:
    out = []
    for r in results:
        out.append(r)
        out += _flatten(r.get("children") or [])
    return out


@pytest.fixture
def executed_run(page: Page, api_client: C2ApiClient):
    """Runs the configured test case via the API and waits for it to finish; always stops on exit."""
    key = os.environ.get("E2E_TEST_KEY") or E2E["test_key"]
    available = _leaf_keys(api_client.get_test_case_list())
    if key not in available:
        pytest.fail(f"E2E test key {key!r} not offered by this tester/license set ({len(available)} available)")

    if api_client.get_app_state().get("appState") != "READY":
        pytest.skip("App is busy with another execution")
    api_client.clear_test_results()
    logger.info(f"E2E: executing {key!r}")
    api_client.post_test_list_to_execute([key], rerun_count=0)
    try:
        started = _wait_for_app_state(api_client, "BUSY", E2E["start_timeout_s"])
        assert started == "BUSY", f"Execution did not start within {E2E['start_timeout_s']}s (state {started})"
        finished = _wait_for_app_state(api_client, "READY", E2E["run_timeout_s"])
        assert finished == "READY", f"Execution did not finish within {E2E['run_timeout_s']}s (state {finished})"
        yield key, api_client.get_test_results()
    finally:
        if api_client.get_app_state().get("appState") == "BUSY":
            logger.warning("E2E: stopping execution left running")
            api_client.stop_test_execution()


@pytest.mark.hardware
@pytest.mark.requires_tester
@pytest.mark.spec("TCM-20", "RES-03", "RES-16", "RPT-09", partial=True)
def test_TC_01_execute_test_and_verify_results_and_report(executed_run, page: Page, api_client: C2ApiClient):
    key, results = executed_run

    # API: a final verdict exists for the executed test
    entries = _flatten(results.get("testResults", []))
    assert entries, "No test results returned after execution"
    verdicts = {e.get("result") for e in entries}
    assert verdicts & FINAL_RESULTS, f"No final verdict in results: {verdicts}"
    summary = results["summary"]
    assert sum(summary[k] for k in ("passCount", "failCount", "incompleteCount", "otherCount")) >= 1, summary

    # UI: Results panel counters equal the API summary
    check = ResultsPage(page).open().cross_validate_with_api(api_client)
    assert check["match"], f"Results panel {check['ui']} != API {check['api']}"

    # Report: a report for this run is available
    api_client.post_current_test_report()
    assert api_client.get_report_file_name(), "No report file name after execution"
    assert ReportPage(page).open().report_location(), "Report location not shown"
