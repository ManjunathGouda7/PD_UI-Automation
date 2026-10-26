"""
Page Object Model for the Test Config panel.
"""
from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from Scripts.Helpers.Locators import TestConfigLocators
from Scripts.Pages.base_page import BasePage


class TestConfigPage(BasePage):
    __test__ = False
    PANEL_NAME = "Test Config"

    def __init__(self, page: Page):
        super().__init__(page)

    # Selection summary -------------------------------------------------------

    def selected_count(self) -> tuple[int, int]:
        """'Selected Tests: X/Y' as (X, Y)."""
        text = self.text(TestConfigLocators.SELECTED_COUNT)
        match = re.search(r"(\d+)\s*/\s*(\d+)", text)
        if not match:
            raise AssertionError(f"Unexpected 'Selected Tests' text: {text!r}")
        return int(match.group(1)), int(match.group(2))

    def start_execution_enabled(self) -> bool:
        return self.is_enabled(TestConfigLocators.START_EXECUTION_BTN)

    # Certification filter ------------------------------------------------------

    def certification(self) -> str:
        return self.dropdown_value(TestConfigLocators.CERTIFICATION_DROPDOWN)

    def certification_options(self) -> list[str]:
        return self.dropdown_options(TestConfigLocators.CERTIFICATION_DROPDOWN)

    # Search / tree ----------------------------------------------------------------

    def search(self, keyword: str) -> None:
        self.fill(TestConfigLocators.SEARCH_INPUT, keyword)

    def clear_search(self) -> None:
        self.fill(TestConfigLocators.SEARCH_INPUT, "")

    def tree_titles(self) -> list[str]:
        return [" ".join(t.split()) for t in self.panel.locator(TestConfigLocators.TREE_NODE_LABEL).all_inner_texts()]

    def tree_node_count(self, wait_ms: int = 10000) -> int:
        """Rendered tree nodes; waits up to `wait_ms` for the first node to appear."""
        nodes = self.panel.locator(TestConfigLocators.TREE_NODE)
        try:
            expect(nodes.first).to_be_visible(timeout=wait_ms)
        except AssertionError:
            return 0
        return nodes.count()

    def set_expand_test_list(self, expanded: bool) -> None:
        self.set_checked(TestConfigLocators.EXPAND_TEST_LIST, expanded)

    # Rerun -----------------------------------------------------------------------

    def rerun_enabled(self) -> bool:
        return self.is_checked(TestConfigLocators.RERUN_SELECTED_CHECKBOX)

    def rerun_count_editable(self) -> bool:
        return self.is_enabled(TestConfigLocators.RERUN_COUNT_INPUT)

    # Report generation inputs ------------------------------------------------------

    def report_inputs(self) -> dict[str, str]:
        return {key: self.value(sel) for key, sel in TestConfigLocators.REPORT_INPUTS.items()}

    def set_report_input(self, key: str, value: str) -> None:
        self.fill(TestConfigLocators.REPORT_INPUTS[key], value)
