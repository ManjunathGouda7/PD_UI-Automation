"""
Base Page Object: panel navigation, panel-scoped element lookup, and the interaction /
synchronisation primitives shared by all panel pages.

Every interaction waits through Playwright's auto-waiting and fails loudly. Page objects
never silently skip a step because an element is missing - that hides regressions.
"""
from __future__ import annotations

from pathlib import Path
import re
import time

from playwright.sync_api import Locator, Page, expect

from Scripts.Helpers.config import Config
from Scripts.Helpers.Locators import AppLocators, DropdownLocators, NavigationLocators
from Scripts.Helpers.logger import logger

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "Reports"


class BasePage:
    #: Text of the left-navigation entry for this panel; None for page-wide objects.
    PANEL_NAME: str | None = None

    def __init__(self, page: Page):
        self.page = page
        self.timeout = Config.ui_timeout_ms()

    # ------------------------------------------------------------------
    # Panel navigation
    # ------------------------------------------------------------------

    @property
    def panel_index(self) -> int:
        if self.PANEL_NAME is None:
            raise TypeError(f"{type(self).__name__} is not bound to a panel")
        return NavigationLocators.PANELS.index(self.PANEL_NAME)

    @property
    def nav_label(self) -> Locator:
        return self.page.locator(NavigationLocators.NAV_LABEL).nth(self.panel_index)

    @property
    def panel(self) -> Locator:
        """Wrapper of this panel. All panels are mounted at once, so lookups must be scoped."""
        return self.page.locator(AppLocators.PANEL_WRAPPER).nth(self.panel_index)

    def open(self):
        """Navigates to this panel and waits until the app marks it active."""
        logger.info(f"Opening panel: {self.PANEL_NAME}")
        expect(self.nav_label).to_contain_text(self.PANEL_NAME, timeout=self.timeout)
        start = time.perf_counter()
        self.nav_label.click()
        expect(self.nav_label).to_have_class(re.compile(r"\bactive\b"), timeout=self.timeout)
        expect(self.panel).to_have_class(re.compile(r"\bscroll-content-sticky\b"), timeout=self.timeout)
        logger.info(f"Panel '{self.PANEL_NAME}' active in {time.perf_counter() - start:.2f}s")
        return self

    def is_active(self) -> bool:
        classes = self.panel.get_attribute("class") or ""
        return "scroll-content-sticky" in classes.split()

    def el(self, selector: str) -> Locator:
        """Element lookup scoped to this panel (page-wide when the page has no panel)."""
        scope = self.panel if self.PANEL_NAME else self.page
        return scope.locator(selector).first

    def ensure_active(self) -> None:
        """
        The app jumps to Connection Setup by itself when the tester connection drops. Before
        interacting, re-open this panel once if that happened (logged, so it stays visible).
        """
        if self.PANEL_NAME is None or self.is_active():
            return
        logger.warning(f"App left panel '{self.PANEL_NAME}' on its own (tester connection change?); re-opening")
        self.open()

    # ------------------------------------------------------------------
    # Interaction primitives
    # ------------------------------------------------------------------

    def click(self, selector: str) -> None:
        self.ensure_active()
        locator = self.el(selector)
        logger.info(f"[{self.PANEL_NAME}] click {selector}")
        expect(locator).to_be_enabled(timeout=self.timeout)
        locator.click(timeout=self.timeout)

    def fill(self, selector: str, value: str) -> None:
        self.ensure_active()
        locator = self.el(selector)
        logger.info(f"[{self.PANEL_NAME}] fill {selector} = {value!r}")
        locator.fill(value, timeout=self.timeout)
        expect(locator).to_have_value(value, timeout=self.timeout)

    def text(self, selector: str) -> str:
        return " ".join(self.el(selector).inner_text(timeout=self.timeout).split())

    def value(self, selector: str) -> str:
        return self.el(selector).input_value(timeout=self.timeout)

    def is_enabled(self, selector: str) -> bool:
        return self.el(selector).is_enabled(timeout=self.timeout)

    def is_checked(self, selector: str) -> bool:
        return self.el(selector).is_checked(timeout=self.timeout)

    def set_checked(self, selector: str, checked: bool) -> None:
        locator = self.el(selector)
        locator.set_checked(checked, timeout=self.timeout)
        if checked:
            expect(locator).to_be_checked(timeout=self.timeout)
        else:
            expect(locator).not_to_be_checked(timeout=self.timeout)

    # ------------------------------------------------------------------
    # Bootstrap dropdowns (<button id=X class=dropdown-toggle> + menu labelled by X)
    # ------------------------------------------------------------------

    def dropdown_value(self, toggle: str) -> str:
        return self.text(toggle)

    def dropdown_options(self, toggle: str) -> list[str]:
        """Opens the dropdown, reads its items and closes it again without selecting."""
        menu = self.page.locator(DropdownLocators.menu(toggle)).first
        self.click(toggle)
        expect(menu).to_be_visible(timeout=self.timeout)
        options = [" ".join(t.split()) for t in menu.locator(".dropdown-item").all_inner_texts()]
        self.page.keyboard.press("Escape")
        if menu.is_visible():
            self.el(toggle).click()
        expect(menu).to_be_hidden(timeout=self.timeout)
        return options

    def select_dropdown(self, toggle: str, option: str) -> None:
        """Selects `option` and verifies the toggle now shows it."""
        menu = self.page.locator(DropdownLocators.menu(toggle)).first
        logger.info(f"[{self.PANEL_NAME}] select {option!r} in {toggle}")
        self.click(toggle)
        expect(menu).to_be_visible(timeout=self.timeout)
        menu.locator(".dropdown-item", has_text=re.compile(rf"^\s*{re.escape(option)}\s*$")).first.click()
        expect(self.el(toggle)).to_have_text(re.compile(rf"^\s*{re.escape(option)}\s*$"), timeout=self.timeout)

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def take_screenshot(self, name: str) -> Path:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^\w.-]+", "_", name)
        path = REPORTS_DIR / f"{safe}_{int(time.time())}.png"
        self.page.screenshot(path=str(path), full_page=False)
        return path
