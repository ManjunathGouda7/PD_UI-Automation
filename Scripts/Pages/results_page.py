"""
Page Object Model for Results Panel.
"""
from typing import Any
from playwright.sync_api import Page
from Scripts.Pages.base_page import BasePage
from Scripts.Helpers.Locators import NavigationLocators, ResultsLocators


class ResultsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def open_panel(self) -> None:
        self.switch_tab(NavigationLocators.TAB_RESULTS)

    def is_chart_visible(self) -> bool:
        return self.is_visible(ResultsLocators.CHART_CONTAINER, timeout=3000)

    def zoom_in(self) -> None:
        if self.is_visible(ResultsLocators.ZOOM_IN_BTN):
            self.click(ResultsLocators.ZOOM_IN_BTN)

    def zoom_out(self) -> None:
        if self.is_visible(ResultsLocators.ZOOM_OUT_BTN):
            self.click(ResultsLocators.ZOOM_OUT_BTN)

    def reset_plot(self) -> None:
        if self.is_visible(ResultsLocators.RESET_PLOT_BTN):
            self.click(ResultsLocators.RESET_PLOT_BTN)

    def toggle_horizontal_marker(self) -> bool:
        if self.is_visible(ResultsLocators.HORIZONTAL_MARKER):
            self.click(ResultsLocators.HORIZONTAL_MARKER)
            return True
        return False

    def toggle_vertical_marker(self) -> bool:
        if self.is_visible(ResultsLocators.VERTICAL_MARKER):
            self.click(ResultsLocators.VERTICAL_MARKER)
            return True
        return False

    def get_results_summary(self) -> dict[str, str]:
        passed = self.get_text(ResultsLocators.PASSED_COUNTER) if self.is_visible(ResultsLocators.PASSED_COUNTER, 2000) else "0"
        failed = self.get_text(ResultsLocators.FAILED_COUNTER) if self.is_visible(ResultsLocators.FAILED_COUNTER, 2000) else "0"
        return {"passed": passed, "failed": failed}

    def cross_validate_with_api(self, api_client) -> dict[str, Any]:
        """
        Cross-validates UI result indicators against backend REST API summary.
        Returns a dict with UI counts, API counts, and validation match status.
        """
        import re
        ui_summary = self.get_results_summary()
        api_results = api_client.get_test_results()
        api_summary = api_results.get("summary", {})

        ui_pass_match = re.search(r"\d+", ui_summary.get("passed", "0"))
        ui_pass_count = int(ui_pass_match.group(0)) if ui_pass_match else 0

        ui_fail_match = re.search(r"\d+", ui_summary.get("failed", "0"))
        ui_fail_count = int(ui_fail_match.group(0)) if ui_fail_match else 0

        api_pass_count = int(api_summary.get("passCount", 0))
        api_fail_count = int(api_summary.get("failCount", 0))

        return {
            "ui_passed": ui_pass_count,
            "ui_failed": ui_fail_count,
            "api_passed": api_pass_count,
            "api_failed": api_fail_count,
            "passed_match": ui_pass_count == api_pass_count,
            "failed_match": ui_fail_count == api_fail_count,
        }

