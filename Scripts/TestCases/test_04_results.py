"""
Test cases for Panel 4: Results.
"""
import pytest
from playwright.sync_api import Page
from Scripts.Pages.results_page import ResultsPage


@pytest.mark.results
@pytest.mark.regression
class TestResultsPanel:
    def test_TC_01_verify_results_panel_navigation(self, page: Page):
        results_page = ResultsPage(page)
        results_page.open_panel()

    def test_TC_02_verify_chart_canvas_or_controls(self, page: Page):
        results_page = ResultsPage(page)
        results_page.open_panel()
        results_page.zoom_in()
        results_page.zoom_out()
        results_page.reset_plot()

    def test_TC_03_verify_marker_controls(self, page: Page):
        results_page = ResultsPage(page)
        results_page.open_panel()
        results_page.toggle_horizontal_marker()
        results_page.toggle_vertical_marker()

    def test_TC_04_verify_results_summary_counters(self, page: Page):
        results_page = ResultsPage(page)
        results_page.open_panel()
        summary = results_page.get_results_summary()
        assert "passed" in summary
        assert "failed" in summary
