"""
Test cases for Panel 1: Connection Setup.
"""
import pytest
from playwright.sync_api import Page
from Scripts.Pages.connection_page import ConnectionPage
from Scripts.Helpers.config import Config


@pytest.mark.connection
@pytest.mark.smoke
class TestConnectionPanel:
    def test_TC_01_verify_connection_panel_loaded(self, page: Page):
        conn_page = ConnectionPage(page)
        conn_page.open_connection_panel()
        assert page.title() != "", "Application title should not be empty"

    def test_TC_02_verify_network_scan_and_ip_selection(self, page: Page):
        conn_page = ConnectionPage(page)
        conn_page.open_connection_panel()
        conn_page.scan_network()
        dut_ip = Config.dut_ip()
        conn_page.select_ip(dut_ip)

    def test_TC_03_verify_connect_hardware_tester(self, page: Page):
        conn_page = ConnectionPage(page)
        conn_page.open_connection_panel()
        dut_ip = Config.dut_ip()
        conn_page.select_ip(dut_ip)
        conn_page.connect()

    def test_TC_04_verify_tester_status_indicators(self, page: Page):
        conn_page = ConnectionPage(page)
        conn_page.open_connection_panel()
        status = conn_page.get_tester_status()
        assert isinstance(status, dict)
