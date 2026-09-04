"""
Test cases for Panel 8: Help & Diagnostics.
"""
import pytest
from playwright.sync_api import Page
from Scripts.Pages.help_page import HelpPage


@pytest.mark.help
@pytest.mark.smoke
class TestHelpPanel:
    def test_TC_01_verify_help_panel_navigation(self, page: Page):
        help_page = HelpPage(page)
        help_page.open_panel()

    def test_TC_02_verify_debug_log_download_trigger(self, page: Page):
        help_page = HelpPage(page)
        help_page.open_panel()
        help_page.download_debug_logs()

    def test_TC_03_verify_diagnostics_information_visible(self, page: Page):
        help_page = HelpPage(page)
        help_page.open_panel()
        help_page.is_diagnostics_visible()
