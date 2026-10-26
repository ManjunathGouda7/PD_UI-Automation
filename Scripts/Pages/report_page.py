"""
Page Object Model for the Report panel.
"""
from __future__ import annotations

from playwright.sync_api import Page, expect

from Scripts.Helpers.Locators import AppLocators, ReportLocators
from Scripts.Pages.base_page import BasePage


class ReportPage(BasePage):
    PANEL_NAME = "Report"

    BUTTONS = {
        "View Report": ReportLocators.VIEW_REPORT_BTN,
        "Download Current HTML Report": ReportLocators.DOWNLOAD_HTML_BTN,
        "Download Current DUT Report Data": ReportLocators.DOWNLOAD_DUT_BTN,
        "Report Data Management": ReportLocators.REPORT_DATA_MGMT_BTN,
    }

    def __init__(self, page: Page):
        super().__init__(page)

    def report_location(self) -> str:
        """Path printed under 'Test Reports Location'."""
        paragraphs = self.panel.locator(ReportLocators.REPORT_LOCATION)
        expect(paragraphs).to_have_count(2, timeout=self.timeout)
        return paragraphs.nth(1).inner_text().strip()

    def button_labels(self) -> dict[str, str]:
        return {name: self.text(sel) for name, sel in self.BUTTONS.items()}

    def open_download_html_prompt(self) -> dict[str, str]:
        """
        Clicks 'Download Current HTML Report', which opens a 'Download File' prompt with a
        file name field and Ok / Cancel. Returns the prompt details; leaves it open.
        """
        self.click(ReportLocators.DOWNLOAD_HTML_BTN)
        expect(self.page.locator(AppLocators.POPUP_CANCEL)).to_be_visible(timeout=self.timeout)
        return {
            "title": self.page.locator(AppLocators.POPUP_TITLE).inner_text().strip(),
            "file_name": self.page.locator(AppLocators.POPUP_INPUT).input_value(),
            "buttons": ",".join(b.strip() for b in self.page.locator(AppLocators.POPUP_BUTTONS).all_inner_texts()),
        }

    def cancel_popup(self) -> None:
        self.page.locator(AppLocators.POPUP_CANCEL).click()
        expect(self.page.locator(AppLocators.POPUP)).to_have_count(0, timeout=self.timeout)
