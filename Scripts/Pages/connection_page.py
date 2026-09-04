"""
Page Object Model for Connection Setup Panel.
"""
from playwright.sync_api import Page
from Scripts.Pages.base_page import BasePage
from Scripts.Helpers.Locators import NavigationLocators, ConnectionLocators
from Scripts.Helpers.logger import logger


class ConnectionPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def open_connection_panel(self) -> None:
        if not self.is_visible(ConnectionLocators.SCAN_NETWORK_BTN, timeout=2000):
            self.switch_tab(NavigationLocators.TAB_CONNECTION)

    def scan_network(self) -> None:
        logger.info("Scanning network for connected PD hardware...")
        self.click(ConnectionLocators.SCAN_NETWORK_BTN)
        self.page.wait_for_timeout(1500)

    def select_ip(self, ip: str = "192.168.102.76") -> None:
        logger.info(f"Selecting IP address: {ip}")
        ip_dropdown = self.page.locator(ConnectionLocators.IP_DROPDOWN).first
        if ip_dropdown.is_visible():
            try:
                ip_dropdown.select_option(value=ip)
            except Exception:
                ip_dropdown.fill(ip)

    def connect(self) -> bool:
        logger.info("Connecting to USB PD hardware tester...")
        if self.is_visible(ConnectionLocators.CONNECT_BTN, timeout=3000):
            self.click(ConnectionLocators.CONNECT_BTN)
            self.page.wait_for_timeout(2000)
            return True
        return False

    def disconnect(self) -> bool:
        logger.info("Disconnecting tester...")
        if self.is_visible(ConnectionLocators.DISCONNECT_BTN, timeout=3000):
            self.click(ConnectionLocators.DISCONNECT_BTN)
            self.page.wait_for_timeout(1000)
            return True
        return False

    def get_tester_status(self) -> dict[str, bool]:
        return {
            "firmware_visible": self.is_visible(ConnectionLocators.STATUS_FIRMWARE, timeout=2000),
            "calibration_visible": self.is_visible(ConnectionLocators.STATUS_CALIBRATION, timeout=2000),
            "licenses_visible": self.is_visible(ConnectionLocators.STATUS_LICENSES, timeout=2000),
        }
