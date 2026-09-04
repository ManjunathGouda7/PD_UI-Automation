"""
Page Object Model for LoopBack Panel.
"""
from playwright.sync_api import Page
from Scripts.Pages.base_page import BasePage
from Scripts.Helpers.Locators import NavigationLocators, LoopBackLocators
from Scripts.Helpers.logger import logger


class LoopBackPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def open_panel(self) -> None:
        self.switch_tab(NavigationLocators.TAB_LOOPBACK)

    def select_device(self, device_name: str) -> None:
        dev_el = self.page.locator(LoopBackLocators.DEVICE_SELECT).first
        if dev_el.is_visible():
            try:
                dev_el.select_option(label=device_name)
            except Exception:
                pass

    def start_loopback(self) -> bool:
        logger.info("Starting LoopBack test...")
        if self.is_visible(LoopBackLocators.START_LOOPBACK_BTN):
            self.click(LoopBackLocators.START_LOOPBACK_BTN)
            return True
        return False

    def stop_loopback(self) -> bool:
        logger.info("Stopping LoopBack test...")
        if self.is_visible(LoopBackLocators.STOP_LOOPBACK_BTN):
            self.click(LoopBackLocators.STOP_LOOPBACK_BTN)
            return True
        return False
