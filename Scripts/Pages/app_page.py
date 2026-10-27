"""
Application shell: page load / readiness, header, left navigation.
"""
from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from Scripts.Helpers.config import Config
from Scripts.Helpers.Locators import AppLocators, ConnectionLocators, NavigationLocators
from Scripts.Helpers.logger import logger
from Scripts.Pages.base_page import BasePage


class AppPage(BasePage):
    PANEL_NAME = None

    def __init__(self, page: Page):
        super().__init__(page)

    def load(self, url: str | None = None) -> AppPage:
        """
        Opens the app and waits until the React shell is rendered. The app polls the
        backend continuously, so 'networkidle' never settles - readiness is element based.
        """
        target = url or Config.base_url()
        logger.info(f"Loading C2 web UI: {target}")
        self.page.goto(target, wait_until="domcontentloaded", timeout=Config.page_load_timeout_ms())
        # The host root serves a tiny page that JS-redirects to /<version>.html.
        self.page.wait_for_url(re.compile(r"/v[\d.]+\.html"), timeout=Config.page_load_timeout_ms())
        self.wait_until_ready()
        return self

    def wait_until_ready(self) -> None:
        timeout = Config.page_load_timeout_ms()
        expect(self.page.locator(NavigationLocators.NAV_GROUP)).to_be_visible(timeout=timeout)
        expect(self.page.locator(NavigationLocators.NAV_LABEL)).to_have_count(
            len(NavigationLocators.PANELS), timeout=timeout
        )
        expect(self.page.locator(AppLocators.PRIMARY_TITLE)).to_contain_text("(", timeout=timeout)
        # On load the app auto-connects to the last tester IP (~5 s, longer if unreachable).
        # Scan Network stays disabled until that attempt finishes; tests must not start earlier.
        expect(self.page.locator(ConnectionLocators.SCAN_NETWORK_BTN)).to_be_enabled(
            timeout=Config.get_int("AUTO_CONNECT_TIMEOUT_MS", 90000)
        )

    # Header ------------------------------------------------------------

    def primary_title(self) -> str:
        return " ".join(self.page.locator(AppLocators.PRIMARY_TITLE).inner_text().split())

    def model_name(self) -> str:
        return self.page.locator(AppLocators.SECONDARY_TITLE).inner_text().strip()

    def header_version(self) -> str:
        """Version shown in the header, e.g. '1.1.1.4'."""
        match = re.search(r"\(([\d.]+)\)", self.primary_title())
        return match.group(1) if match else ""

    # Navigation --------------------------------------------------------

    def nav_panel_names(self) -> list[str]:
        return [" ".join(t.split()) for t in self.page.locator(NavigationLocators.NAV_LABEL).all_inner_texts()]

    def toggle_navigation(self) -> None:
        """Top-left menu control: collapses / expands the left navigation pane."""
        self.page.locator(AppLocators.HAMBURGER).click()

    def navigation_visible(self) -> bool:
        return self.page.locator(NavigationLocators.NAV_GROUP).is_visible()

    def layout_overflow(self) -> dict[str, int]:
        """Horizontal overflow of the page at the current viewport (0 = no horizontal scrolling needed)."""
        return self.page.evaluate("""() => ({
            viewport: window.innerWidth,
            overflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
        })""")

    def active_panel_name(self) -> str:
        return " ".join(self.page.locator(NavigationLocators.ACTIVE_NAV_LABEL).inner_text().split())
