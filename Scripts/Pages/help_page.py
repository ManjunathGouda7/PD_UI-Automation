"""
Page Object Model for the Help panel.
"""
from __future__ import annotations

from pathlib import Path
import re

from playwright.sync_api import Page

from Scripts.Helpers.Locators import HelpLocators
from Scripts.Pages.base_page import REPORTS_DIR, BasePage


class HelpPage(BasePage):
    PANEL_NAME = "Help"

    LINKS = {
        "Support Desk": HelpLocators.SUPPORT_DESK_LINK,
        "Email Support": HelpLocators.EMAIL_SUPPORT_LINK,
        "Debug Logs": HelpLocators.DEBUG_LOG_LINK,
        "API Document": HelpLocators.API_DOC_LINK,
    }

    def __init__(self, page: Page):
        super().__init__(page)

    def product_name(self) -> str:
        return self.text(HelpLocators.PRODUCT_HEADING)

    def app_version(self) -> str:
        """'App Version : 1.1.1.4' -> '1.1.1.4'."""
        text = self.text(HelpLocators.APP_VERSION)
        match = re.search(r"([\d]+(?:\.[\d]+)+)", text)
        return match.group(1) if match else ""

    def link(self, name: str) -> dict[str, str]:
        loc = self.el(self.LINKS[name])
        return {
            "text": " ".join(loc.inner_text().split()),
            "href": loc.get_attribute("href") or "",
            "target": loc.get_attribute("target") or "",
        }

    def download_debug_logs(self, timeout_ms: int = 30000) -> Path:
        """Downloads the debug log and returns the saved file path."""
        with self.page.expect_download(timeout=timeout_ms) as info:
            self.click(HelpLocators.DEBUG_LOG_LINK)
        download = info.value
        failure = download.failure()
        if failure:
            raise AssertionError(f"Debug log download failed: {failure}")
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        target = REPORTS_DIR / f"downloads_{download.suggested_filename}"
        download.save_as(str(target))
        return target
