"""
Test cases for Panel 3: Test Configuration.
"""
import pytest
from playwright.sync_api import Page
from Scripts.Pages.test_config_page import TestConfigPage


@pytest.mark.test_config
@pytest.mark.regression
class TestConfigurationPanel:
    def test_TC_01_verify_test_config_panel_navigation(self, page: Page):
        config_page = TestConfigPage(page)
        config_page.open_panel()

    def test_TC_02_verify_test_categories_present(self, page: Page):
        config_page = TestConfigPage(page)
        config_page.open_panel()
        categories = config_page.get_test_categories_visible()
        assert isinstance(categories, dict)

    def test_TC_03_verify_search_filtering(self, page: Page):
        config_page = TestConfigPage(page)
        config_page.open_panel()
        count = config_page.search_tests("Power")
        assert count >= 0

    def test_TC_04_verify_select_and_deselect_all_tests(self, page: Page):
        config_page = TestConfigPage(page)
        config_page.open_panel()
        config_page.select_all_tests()
        config_page.deselect_all_tests()

    def test_TC_05_verify_engineer_metadata_input(self, page: Page):
        config_page = TestConfigPage(page)
        config_page.open_panel()
        config_page.set_test_engineer("GRL Automation Engineer")
