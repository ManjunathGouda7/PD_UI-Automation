"""
Panel 4: Results.
Spec: Test Results & Protocol, Get Caps & Trace.
"""
from playwright.sync_api import Page
import pytest

from Scripts.Helpers.api_client import C2ApiClient
from Scripts.Helpers.Locators import ResultsLocators
from Scripts.Pages.results_page import ResultsPage


@pytest.fixture
def results(page: Page) -> ResultsPage:
    return ResultsPage(page).open()


@pytest.mark.results
class TestResultsPanel:
    def test_TC_01_summary_has_four_numeric_counters(self, results: ResultsPage):
        summary = results.summary()
        assert list(summary) == list(ResultsPage.SUMMARY_KEYS)
        assert all(v >= 0 for v in summary.values())

    @pytest.mark.smoke
    def test_TC_02_summary_matches_api(self, results: ResultsPage, api_client: C2ApiClient):
        check = results.cross_validate_with_api(api_client)
        assert check["match"], f"UI {check['ui']} != API {check['api']}"

    def test_TC_03_chart_toolbar_buttons_available(self, results: ResultsPage):
        states = results.toolbar_button_states()
        unavailable = [sel for sel, ok in states.items() if not ok]
        assert not unavailable, f"Toolbar buttons hidden/disabled: {unavailable}"

    @pytest.mark.parametrize("button", [
        ResultsLocators.H_ZOOM_IN_BTN, ResultsLocators.H_ZOOM_OUT_BTN,
        ResultsLocators.V_ZOOM_IN_BTN, ResultsLocators.V_ZOOM_OUT_BTN,
        ResultsLocators.FIT_BTN, ResultsLocators.PAN_LEFT_BTN, ResultsLocators.PAN_RIGHT_BTN,
    ])
    def test_TC_04_chart_navigation_buttons_respond(self, results: ResultsPage, button: str, popup_guard):
        results.click_toolbar(button)
        assert results.is_active()
        assert not [p for p in popup_guard.seen if "error" in p.message.lower()], popup_guard.seen

    def test_TC_05_plot_area_offers_file_load_when_empty(self, results: ResultsPage, api_client: C2ApiClient):
        if api_client.get_total_pd_message_count():
            pytest.skip("Capture data present; empty-state placeholder not shown")
        assert "Drag & drop file here" in results.plot_placeholder_text()

    def test_TC_06_start_execution_disabled_when_idle(self, results: ResultsPage, api_client: C2ApiClient):
        if api_client.get_app_state().get("appState") != "READY":
            pytest.skip("App is not idle")
        assert not results.is_enabled(ResultsLocators.START_EXECUTION_BTN)
