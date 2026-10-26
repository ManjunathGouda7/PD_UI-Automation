"""
Page Object Model for the Configure panel.
"""
from __future__ import annotations

from playwright.sync_api import Page

from Scripts.Helpers.Locators import ConfigureLocators
from Scripts.Helpers.logger import logger
from Scripts.Pages.base_page import BasePage


class ConfigurePage(BasePage):
    PANEL_NAME = "Configure"

    DROPDOWNS = {
        "Controller Mode": ConfigureLocators.CONTROLLER_MODE_DROPDOWN,
        "Test Cable Type": ConfigureLocators.TEST_CABLE_TYPE_DROPDOWN,
        "PD Spec Type": ConfigureLocators.PD_SPEC_TYPE_DROPDOWN,
        "Cable Emulation": ConfigureLocators.CABLE_EMULATION_DROPDOWN,
        "Rp Level": ConfigureLocators.RP_LEVEL_DROPDOWN,
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # Controller settings ---------------------------------------------------------

    def settings(self) -> dict[str, str]:
        return {name: self.dropdown_value(sel) for name, sel in self.DROPDOWNS.items()}

    def options(self, setting: str) -> list[str]:
        return self.dropdown_options(self.DROPDOWNS[setting])

    def select(self, setting: str, value: str) -> None:
        self.select_dropdown(self.DROPDOWNS[setting], value)

    def is_setting_enabled(self, setting: str) -> bool:
        return self.is_enabled(self.DROPDOWNS[setting])

    # Channels (client-side until Apply) ------------------------------------------

    def channel_states(self) -> dict[str, bool]:
        return {name: self.is_checked(sel) for name, sel in ConfigureLocators.CHANNELS.items()}

    def set_channel(self, channel: str, enabled: bool) -> None:
        self.set_checked(ConfigureLocators.CHANNELS[channel], enabled)

    def sampling_ratio(self) -> str:
        return self.value(ConfigureLocators.SAMPLING_RATIO_INPUT)

    def button_enabled(self, selector: str) -> bool:
        return self.is_enabled(selector)

    # Hardware actions -----------------------------------------------------------

    def apply(self) -> None:
        logger.info("Applying controller configuration to tester...")
        self.click(ConfigureLocators.APPLY_BTN)

    def attach(self) -> None:
        self.click(ConfigureLocators.ATTACH_BTN)

    def detach(self) -> None:
        self.click(ConfigureLocators.DETACH_BTN)
