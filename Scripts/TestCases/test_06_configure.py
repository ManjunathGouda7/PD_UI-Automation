"""
Test cases for Panel 6: Configure.
"""
import pytest
from playwright.sync_api import Page
from Scripts.Pages.configure_page import ConfigurePage


@pytest.mark.configure
@pytest.mark.regression
class TestConfigurePanel:
    def test_TC_01_verify_configure_panel_navigation(self, page: Page):
        cfg_page = ConfigurePage(page)
        cfg_page.open_panel()

    def test_TC_02_verify_controller_mode_selection(self, page: Page):
        cfg_page = ConfigurePage(page)
        cfg_page.open_panel()
        cfg_page.select_controller_mode("UFP/Sink")

    def test_TC_03_verify_channel_toggles(self, page: Page):
        cfg_page = ConfigurePage(page)
        cfg_page.open_panel()
        cfg_page.toggle_vbus_channel()
        cfg_page.toggle_cc1_channel()

    def test_TC_04_verify_apply_configuration(self, page: Page):
        cfg_page = ConfigurePage(page)
        cfg_page.open_panel()
        cfg_page.apply_configuration()
