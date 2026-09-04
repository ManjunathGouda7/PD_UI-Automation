"""
Test cases for Panel 2: Product Capability.
"""
import pytest
from playwright.sync_api import Page
from Scripts.Pages.product_capability_page import ProductCapabilityPage
from Scripts.Data.test_data_manager import test_data_manager


@pytest.mark.product_cap
@pytest.mark.regression
class TestProductCapabilityPanel:
    def test_TC_01_verify_product_capability_panel_navigation(self, page: Page):
        prod_page = ProductCapabilityPage(page)
        prod_page.open_panel()

    def test_TC_02_verify_dut_role_selection(self, page: Page):
        prod_page = ProductCapabilityPage(page)
        prod_page.open_panel()
        profile = test_data_manager.get_profile("provider_epr")
        role = profile.get("dut_role", "Provider Only")
        prod_page.select_dut_role(role)

    def test_TC_03_verify_cable_selection(self, page: Page):
        prod_page = ProductCapabilityPage(page)
        prod_page.open_panel()
        profile = test_data_manager.get_profile("provider_epr")
        cable = profile.get("cable_model", "GRL-SPL EPR Cable 1")
        prod_page.select_cable_model(cable)

    def test_TC_04_verify_read_device_trigger(self, page: Page):
        prod_page = ProductCapabilityPage(page)
        prod_page.open_panel()
        prod_page.read_device()
