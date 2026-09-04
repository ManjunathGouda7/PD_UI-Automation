"""
Page Object Model for Report Panel.
"""
from playwright.sync_api import Page
from Scripts.Pages.base_page import BasePage
from Scripts.Helpers.Locators import NavigationLocators, ReportLocators
from Scripts.Helpers.logger import logger


class ReportPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def open_panel(self) -> None:
        self.switch_tab(NavigationLocators.TAB_REPORT)

    def view_report(self) -> bool:
        logger.info("Clicking View Report...")
        if self.is_visible(ReportLocators.VIEW_REPORT_BTN):
            self.click(ReportLocators.VIEW_REPORT_BTN)
            return True
        return False

    def download_html_report(self) -> bool:
        logger.info("Triggering HTML Report Download...")
        if self.is_visible(ReportLocators.DOWNLOAD_HTML_BTN):
            self.click(ReportLocators.DOWNLOAD_HTML_BTN)
            return True
        return False

    def download_dut_data(self) -> bool:
        logger.info("Triggering DUT Data Download...")
        if self.is_visible(ReportLocators.DOWNLOAD_DUT_BTN):
            self.click(ReportLocators.DOWNLOAD_DUT_BTN)
            return True
        return False
