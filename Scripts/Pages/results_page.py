"""
Page Object Model for Results Panel.
"""
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
