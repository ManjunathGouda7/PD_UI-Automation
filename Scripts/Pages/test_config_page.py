"""
Page Object Model for Test Configuration Panel.
"""
from playwright.sync_api import Page
from Scripts.Pages.base_page import BasePage
from Scripts.Helpers.Locators import NavigationLocators, TestConfigLocators
from Scripts.Helpers.logger import logger


class TestConfigPage(BasePage):
    __test__ = False
    def __init__(self, page: Page):
        super().__init__(page)

    def open_panel(self) -> None:
        self.switch_tab(NavigationLocators.TAB_TEST_CONFIG)

    def select_all_tests(self) -> None:
        logger.info("Selecting all 207 test cases...")
        if self.is_visible(TestConfigLocators.SELECT_ALL_CHECKBOX):
            self.click(TestConfigLocators.SELECT_ALL_CHECKBOX)

    def deselect_all_tests(self) -> None:
        logger.info("Deselecting all tests...")
        if self.is_visible(TestConfigLocators.DESELECT_ALL_BTN):
            self.click(TestConfigLocators.DESELECT_ALL_BTN)

    def search_tests(self, keyword: str) -> int:
        logger.info(f"Searching tests for keyword: {keyword}")
        self.fill(TestConfigLocators.SEARCH_INPUT, keyword)
        self.page.wait_for_timeout(500)
        return self.page.locator(TestConfigLocators.TEST_ITEMS).count()

    def set_test_engineer(self, name: str) -> None:
        if self.is_visible(TestConfigLocators.TEST_ENGINEER_INPUT):
            self.fill(TestConfigLocators.TEST_ENGINEER_INPUT, name)

    def get_test_categories_visible(self) -> dict[str, bool]:
        return {
            "pd_3_2": self.is_visible(TestConfigLocators.CATEGORY_PD_3_2, timeout=2000),
            "usbc": self.is_visible(TestConfigLocators.CATEGORY_USBC, timeout=2000),
            "safety": self.is_visible(TestConfigLocators.CATEGORY_SAFETY, timeout=2000),
        }
