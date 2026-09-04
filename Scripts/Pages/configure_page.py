"""
Page Object Model for Configure Panel.
"""
from playwright.sync_api import Page
from Scripts.Pages.base_page import BasePage
from Scripts.Helpers.Locators import NavigationLocators, ConfigureLocators
from Scripts.Helpers.logger import logger


class ConfigurePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def open_panel(self) -> None:
        self.switch_tab(NavigationLocators.TAB_CONFIGURE)

    def select_controller_mode(self, mode: str = "UFP/Sink") -> None:
        logger.info(f"Setting Controller Mode: {mode}")
        mode_el = self.page.locator(ConfigureLocators.CONTROLLER_MODE_SELECT).first
        if mode_el.is_visible():
            try:
                mode_el.select_option(label=mode)
            except Exception:
                pass

    def toggle_vbus_channel(self) -> None:
        if self.is_visible(ConfigureLocators.CHANNEL_VBUS):
            self.click(ConfigureLocators.CHANNEL_VBUS)

    def toggle_cc1_channel(self) -> None:
        if self.is_visible(ConfigureLocators.CHANNEL_CC1):
            self.click(ConfigureLocators.CHANNEL_CC1)

    def apply_configuration(self) -> bool:
        if self.is_visible(ConfigureLocators.APPLY_CONFIG_BTN):
            self.click(ConfigureLocators.APPLY_CONFIG_BTN)
            return True
        return False
