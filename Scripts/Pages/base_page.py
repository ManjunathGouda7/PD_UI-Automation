"""
Base Page Object providing core interaction, synchronization, and assertion primitives.
"""
from playwright.sync_api import Page
from Scripts.Helpers.logger import logger


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def navigate(self, url: str) -> None:
        logger.info(f"Navigating to {url}")
        self.page.goto(url, wait_until="load", timeout=30000)

    def click(self, selector: str, timeout: float = 10000) -> None:
        logger.info(f"Clicking on selector: {selector}")
        locator = self.page.locator(selector).first
        locator.wait_for(state="visible", timeout=timeout)
        locator.click()

    def fill(self, selector: str, value: str, timeout: float = 10000) -> None:
        logger.info(f"Filling selector: {selector} with '{value}'")
        locator = self.page.locator(selector).first
        locator.wait_for(state="visible", timeout=timeout)
        locator.fill(value)

    def get_text(self, selector: str, timeout: float = 10000) -> str:
        locator = self.page.locator(selector).first
        locator.wait_for(state="visible", timeout=timeout)
        return locator.inner_text().strip()

    def is_visible(self, selector: str, timeout: float = 5000) -> bool:
        try:
            self.page.locator(selector).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def wait_for_hidden(self, selector: str, timeout: float = 10000) -> bool:
        try:
            self.page.locator(selector).first.wait_for(state="hidden", timeout=timeout)
            return True
        except Exception:
            return False

    def take_screenshot(self, name: str) -> bytes:
        return self.page.screenshot(full_page=True)

    def switch_tab(self, tab_selector: str) -> None:
        logger.info(f"Switching panel tab: {tab_selector}")
        self.click(tab_selector)
