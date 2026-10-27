"""
Page Object Model for the Connection Setup panel.
"""
from __future__ import annotations

from playwright.sync_api import Page, expect

from Scripts.Helpers.Locators import ConnectionLocators
from Scripts.Helpers.logger import logger
from Scripts.Pages.base_page import BasePage


class ConnectionPage(BasePage):
    PANEL_NAME = "Connection Setup"

    TESTER_FIELDS = (
        "Tester Status",
        "Serial Number",
        "Firmware Version",
        "Tester IP Address Information",
        "Last Calibration Date",
        "Calibration Due",
        "VDPWR Tester Calibration",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # Read-only ---------------------------------------------------------

    def tester_info(self) -> dict[str, str]:
        """Tester Status table as {row header: value}."""
        rows = self.panel.locator(ConnectionLocators.TESTER_INFO_ROWS)
        expect(rows.first).to_be_visible(timeout=self.timeout)
        info: dict[str, str] = {}
        for i in range(rows.count()):
            row = rows.nth(i)
            key = " ".join(row.locator("th").inner_text().split())
            info[key] = " ".join(row.locator("td").inner_text().split())
        return info

    def ip_address(self) -> str:
        return self.value(ConnectionLocators.IP_INPUT).strip()

    def licenses(self) -> list[dict[str, str]]:
        """
        License Information entries. The table is column-oriented: one <td> holds all license
        names (one per line), the next all types, the last all periods.
        """
        rows = self.panel.locator(ConnectionLocators.LICENSE_ROWS)
        result: list[dict[str, str]] = []
        for i in range(rows.count()):
            columns = [[ln.strip() for ln in cell.splitlines() if ln.strip()]
                       for cell in rows.nth(i).locator("td").all_inner_texts()]
            if not columns or not columns[0]:
                continue
            names, types = columns[0], columns[1] if len(columns) > 1 else []
            periods = columns[2] if len(columns) > 2 else []
            for idx, name in enumerate(names):
                result.append({
                    "name": name,
                    "type": types[idx] if idx < len(types) else "",
                    "period": periods[idx] if idx < len(periods) else "",
                })
        return result

    def update_firmware_enabled(self) -> bool:
        return self.is_enabled(ConnectionLocators.UPDATE_FW_BTN)

    def license_header_visible(self) -> bool:
        return self.el(ConnectionLocators.LICENSE_HEADER).is_visible()

    # Hardware actions (only from tests marked `hardware`) -------------------

    def scan_network(self) -> None:
        logger.info("Scanning network for testers...")
        self.click(ConnectionLocators.SCAN_NETWORK_BTN)

    def enter_ip(self, ip: str) -> None:
        field = self.el(ConnectionLocators.IP_INPUT)
        field.click()
        field.fill(ip)
        field.press("Enter")
        expect(field).to_have_value(ip, timeout=self.timeout)

    def connect(self, ip: str, timeout_ms: int = 60000) -> dict[str, str]:
        """Connects to `ip` and waits until the Tester Status row reports the outcome."""
        logger.info(f"Connecting to tester {ip}")
        self.enter_ip(ip)
        self.click(ConnectionLocators.CONNECT_BTN)
        status = self.panel.locator(ConnectionLocators.TESTER_INFO_ROWS).first.locator("td")
        expect(status).not_to_have_text("", timeout=timeout_ms)
        expect(self.panel.locator(ConnectionLocators.TESTER_INFO_ROWS).nth(3).locator("td")).to_have_text(
            ip, timeout=timeout_ms
        )
        return self.tester_info()
