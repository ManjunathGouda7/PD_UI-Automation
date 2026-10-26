"""
Page Object Model for the LoopBack panel.
"""
from __future__ import annotations

from playwright.sync_api import Page

from Scripts.Helpers.Locators import LoopBackLocators
from Scripts.Pages.base_page import BasePage


class LoopBackPage(BasePage):
    PANEL_NAME = "LoopBack"

    def __init__(self, page: Page):
        super().__init__(page)

    def data(self) -> dict[str, str]:
        """{'Transferred Data': '0 MB', ..., 'Status': '...'} (labels without trailing colon)."""
        items = self.panel.locator(LoopBackLocators.DATA_ITEM)
        result = {}
        for i in range(items.count()):
            item = items.nth(i)
            label = item.locator(LoopBackLocators.DATA_LABEL).inner_text().strip().rstrip(":")
            result[label] = " ".join(item.locator(LoopBackLocators.DATA_VALUE).inner_text().split())
        return result

    def device_options(self) -> list[str]:
        return [o.strip() for o in self.el(LoopBackLocators.DEVICE_SELECT).locator("option").all_inner_texts()]

    def selected_device(self) -> str:
        return self.value(LoopBackLocators.DEVICE_SELECT)

    def start_enabled(self) -> bool:
        return self.is_enabled(LoopBackLocators.START_BTN)

    def stop_enabled(self) -> bool:
        return self.is_enabled(LoopBackLocators.STOP_BTN)

    def refresh_devices(self) -> None:
        self.click(LoopBackLocators.REFRESH_BTN)

    def select_device(self, label: str) -> None:
        self.el(LoopBackLocators.DEVICE_SELECT).select_option(label=label, timeout=self.timeout)

    def start(self) -> None:
        self.click(LoopBackLocators.START_BTN)

    def stop(self) -> None:
        self.click(LoopBackLocators.STOP_BTN)
