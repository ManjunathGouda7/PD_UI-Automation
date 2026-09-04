"""
Page Object Model for Product Capability Panel.
"""
from playwright.sync_api import Page
from Scripts.Pages.base_page import BasePage
from Scripts.Helpers.Locators import NavigationLocators, ProductCapLocators
from Scripts.Helpers.logger import logger


class ProductCapabilityPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def open_panel(self) -> None:
        self.switch_tab(NavigationLocators.TAB_PRODUCT_CAP)

    def select_dut_role(self, role: str = "Provider Only") -> None:
        logger.info(f"Selecting DUT Role: {role}")
        dut_el = self.page.locator(ProductCapLocators.DUT_TYPE_DROPDOWN).first
        if dut_el.is_visible():
            try:
                dut_el.select_option(label=role)
            except Exception:
                dut_el.click()

    def select_cable_model(self, cable: str = "GRL-SPL EPR Cable 1") -> None:
        logger.info(f"Selecting Cable Model: {cable}")
        cable_el = self.page.locator(ProductCapLocators.CABLE_SELECT).first
        if cable_el.is_visible():
            try:
                cable_el.select_option(label=cable)
            except Exception:
                pass

    def read_device(self) -> bool:
        logger.info("Triggering Read Device data...")
        if self.is_visible(ProductCapLocators.READ_DEVICE_BTN):
            self.click(ProductCapLocators.READ_DEVICE_BTN)
            self.page.wait_for_timeout(1500)
            return True
        return False

    def clear_vif(self) -> bool:
        logger.info("Clearing VIF...")
        if self.is_visible(ProductCapLocators.CLEAR_VIF_BTN):
            self.click(ProductCapLocators.CLEAR_VIF_BTN)
            return True
        return False
