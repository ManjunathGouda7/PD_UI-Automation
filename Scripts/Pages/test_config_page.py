"""
Page Object Model for the Test Config panel.
"""
from __future__ import annotations

import re
import time

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

    def tree_suite_titles(self, wait_ms: int = 15000) -> list[str]:
        """Top-level suites of the test tree, e.g. 'Power Delivery 3.2 Tests-v.Q3-2026'."""
        suites = self.panel.locator(TestConfigLocators.TREE_SUITE_NODE)
        try:
            expect(suites.first).to_be_visible(timeout=wait_ms)
        except AssertionError:
            return []
        return [" ".join(suites.nth(i).locator(TestConfigLocators.TREE_NODE_LABEL).first.inner_text().split())
                for i in range(suites.count())]

    def tree_node_count(self) -> int:
        return self.panel.locator(TestConfigLocators.TREE_NODE).count()

    def visible_tree_titles(self) -> list[str]:
        return [" ".join(t.split()) for t in
                self.panel.locator(f"{TestConfigLocators.TREE_NODE} {TestConfigLocators.TREE_NODE_LABEL}").all_inner_texts()]

    def wait_for_tree_count(self, predicate, timeout_ms: int | None = None) -> int:
        """Polls the rendered node count until predicate(count) holds; returns the last count."""
        deadline = time.monotonic() + (timeout_ms or self.timeout) / 1000
        while True:
            count = self.tree_node_count()
            if predicate(count) or time.monotonic() > deadline:
                return count
            self.page.wait_for_timeout(200)

    def _suite_checkbox(self, suite_prefix: str):
        suite = self.panel.locator(TestConfigLocators.TREE_SUITE_NODE).filter(
            has=self.page.locator(TestConfigLocators.TREE_NODE_LABEL, has_text=suite_prefix)).first
        return suite.locator(TestConfigLocators.TREE_CHECKBOX).first

    def set_suite_selected(self, suite_prefix: str, selected: bool) -> None:
        """Ticks / unticks a top-level suite (client-side until execution starts)."""
        box = self._suite_checkbox(suite_prefix)
        if self.suite_selected(suite_prefix) != selected:
            self.ensure_active()
            box.click()
        checked = re.compile(re.escape(TestConfigLocators.TREE_CHECKBOX_CHECKED))
        if selected:
            expect(box).to_have_class(checked, timeout=self.timeout)
        else:
            expect(box).not_to_have_class(checked, timeout=self.timeout)

    def suite_selected(self, suite_prefix: str) -> bool:
        classes = self._suite_checkbox(suite_prefix).get_attribute("class") or ""
        return TestConfigLocators.TREE_CHECKBOX_CHECKED in classes.split()

    def filter_classes(self) -> dict[str, str]:
        return {name: self.el(sel).get_attribute("class") or "" for name, sel in TestConfigLocators.FILTER_BUTTONS.items()}

    def click_filter(self, name: str) -> None:
        self.click(TestConfigLocators.FILTER_BUTTONS[name])

    def clear_filters(self) -> None:
        self.click(TestConfigLocators.FILTER_CLEAR_BTN)

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
