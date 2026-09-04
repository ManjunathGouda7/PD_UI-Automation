"""
Test cases for Panel 7: LoopBack.
"""
import pytest
from playwright.sync_api import Page
from Scripts.Pages.loopback_page import LoopBackPage


@pytest.mark.loopback
@pytest.mark.regression
class TestLoopBackPanel:
    def test_TC_01_verify_loopback_panel_navigation(self, page: Page):
        lb_page = LoopBackPage(page)
        lb_page.open_panel()

    def test_TC_02_verify_start_and_stop_loopback(self, page: Page):
        lb_page = LoopBackPage(page)
        lb_page.open_panel()
        lb_page.start_loopback()
        lb_page.stop_loopback()
