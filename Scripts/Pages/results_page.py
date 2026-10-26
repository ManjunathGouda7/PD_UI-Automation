"""
Page Object Model for the Results panel.
"""
from __future__ import annotations

import re
from typing import Any

from playwright.sync_api import Page, expect

from Scripts.Helpers.Locators import ResultsLocators
from Scripts.Pages.base_page import BasePage


class ResultsPage(BasePage):
    PANEL_NAME = "Results"

    #: Order of the counters in the "Test Summary" row and the matching API summary keys.
    SUMMARY_KEYS = ("pass", "fail", "incomplete", "warning")
    API_SUMMARY_KEYS = {"pass": "passCount", "fail": "failCount", "incomplete": "incompleteCount",
                        "warning": "otherCount"}

    def __init__(self, page: Page):
        super().__init__(page)

    def summary(self) -> dict[str, int]:
        """Test Summary counters of the Results panel (other panels repeat this widget)."""
        counters = self.panel.locator(ResultsLocators.SUMMARY_COUNTS)
        expect(counters).to_have_count(len(self.SUMMARY_KEYS), timeout=self.timeout)
        for i in range(len(self.SUMMARY_KEYS)):  # counters are briefly empty while re-rendering
            expect(counters.nth(i)).to_have_text(re.compile(r"\d"), timeout=self.timeout)
        values = []
        for raw in counters.all_inner_texts():
            match = re.search(r"\d+", raw)
            if not match:
                raise AssertionError(f"Non-numeric Test Summary counter: {raw!r}")
            values.append(int(match.group(0)))
        return dict(zip(self.SUMMARY_KEYS, values, strict=True))

    def test_status(self) -> str:
        return self.text(ResultsLocators.TEST_STATUS) if self.el(ResultsLocators.TEST_STATUS).count() else ""

    def toolbar_button_states(self) -> dict[str, bool]:
        """{selector: visible-and-enabled} for every chart toolbar button."""
        states = {}
        for sel in ResultsLocators.TOOLBAR_BUTTONS:
            loc = self.el(sel)
            states[sel] = loc.is_visible() and loc.is_enabled()
        return states

    def click_toolbar(self, selector: str) -> None:
        self.click(selector)

    def plot_placeholder_text(self) -> str:
        return self.text(ResultsLocators.PLOT_CONTAINER)

    def cross_validate_with_api(self, api_client) -> dict[str, Any]:
        """UI counters vs /api/Results/GetTestResults summary."""
        ui = self.summary()
        api_summary = api_client.get_test_results().get("summary", {})
        api = {k: int(api_summary.get(v, 0)) for k, v in self.API_SUMMARY_KEYS.items()}
        return {"ui": ui, "api": api, "match": ui == api}
