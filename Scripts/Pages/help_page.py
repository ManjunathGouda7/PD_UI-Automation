"""
Page Object Model for Help & Diagnostics Panel.
"""
from playwright.sync_api import Page
from Scripts.Pages.base_page import BasePage
from Scripts.Helpers.Locators import NavigationLocators, HelpLocators
from Scripts.Helpers.logger import logger


class HelpPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def open_panel(self) -> None:
        self.switch_tab(NavigationLocators.TAB_HELP)

    def download_debug_logs(self) -> bool:
        logger.info("Requesting debug logs download...")
        if self.is_visible(HelpLocators.DEBUG_LOG_BTN):
            self.click(HelpLocators.DEBUG_LOG_BTN)
            return True
        return False

    def is_diagnostics_visible(self) -> bool:
        return self.is_visible(HelpLocators.DIAGNOSTICS_SECTION, timeout=3000)
