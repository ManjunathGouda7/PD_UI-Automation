"""
Page Object Model for the Product Capability panel.
"""
from __future__ import annotations

from playwright.sync_api import Page

from Scripts.Helpers.Locators import ProductCapLocators
from Scripts.Helpers.logger import logger
from Scripts.Pages.base_page import BasePage


class ProductCapabilityPage(BasePage):
    PANEL_NAME = "Product Capability"

    def __init__(self, page: Page):
        super().__init__(page)

    # DUT type ------------------------------------------------------------

    def dut_type(self) -> str:
        return self.dropdown_value(ProductCapLocators.DUT_TYPE_DROPDOWN)

    def dut_type_options(self) -> list[str]:
        return self.dropdown_options(ProductCapLocators.DUT_TYPE_DROPDOWN)

    def select_dut_type(self, dut_type: str) -> None:
        self.select_dropdown(ProductCapLocators.DUT_TYPE_DROPDOWN, dut_type)

    # Cable -----------------------------------------------------------------

    def cable(self) -> str:
        return self.dropdown_value(ProductCapLocators.CABLE_DROPDOWN)

    def cable_options(self) -> list[str]:
        return self.dropdown_options(ProductCapLocators.CABLE_DROPDOWN)

    def select_cable(self, cable: str) -> None:
        self.select_dropdown(ProductCapLocators.CABLE_DROPDOWN, cable)

    # Project / VIF -----------------------------------------------------------

    def project_save_enabled(self) -> bool:
        return self.is_enabled(ProductCapLocators.PROJECT_SAVE_BTN)

    def type_project_name(self, name: str) -> None:
        self.fill(ProductCapLocators.PROJECT_NAME_INPUT, name)

    def vif_generator_href(self) -> str:
        return self.el(ProductCapLocators.VIF_GENERATOR_LINK).get_attribute("href") or ""

    # Hardware actions ----------------------------------------------------------

    def read_device_data(self) -> None:
        logger.info("Reading device data from DUT...")
        self.click(ProductCapLocators.READ_DEVICE_BTN)
