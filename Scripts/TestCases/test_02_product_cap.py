"""
Panel 2: Product Capability.
Spec: Product Capability & Browser, VIF & DUT Roles.
"""
from playwright.sync_api import Page
import pytest

from Scripts.Data.test_data_manager import test_data_manager
from Scripts.Helpers.api_client import C2ApiClient
from Scripts.Pages.product_capability_page import ProductCapabilityPage

PC = test_data_manager.section("product_capability")


@pytest.fixture
def pc(page: Page) -> ProductCapabilityPage:
    return ProductCapabilityPage(page).open()


@pytest.mark.product_cap
class TestProductCapabilityPanel:
    @pytest.mark.smoke
    def test_TC_01_dut_type_options(self, pc: ProductCapabilityPage):
        assert pc.dut_type_options() == PC["dut_types"]
        assert pc.dut_type() in PC["dut_types"]

    def test_TC_02_cable_options(self, pc: ProductCapabilityPage):
        assert pc.cable_options() == PC["cables"]
        assert pc.cable() in PC["cables"]

    @pytest.mark.smoke
    def test_TC_03_port1_selection_matches_backend(self, pc: ProductCapabilityPage, api_client: C2ApiClient):
        port_a = api_client.get_port_configurations()["ports"]["PortA"]
        assert pc.dut_type() == port_a["dutType"]
        assert pc.cable() == port_a["cableType"]

    @pytest.mark.xfail(strict=True, reason=(
        "PRODUCT DEFECT (1.1.1.4): after a project name is typed and cleared - or is whitespace "
        "only - the Save button stays enabled although the field shows a validation error. "
        "Save is only disabled on first load."))
    def test_TC_04_project_save_requires_name(self, pc: ProductCapabilityPage):
        assert not pc.project_save_enabled(), "Save must be disabled while project name is empty"
        pc.type_project_name("AutomationProbe")
        assert pc.project_save_enabled()
        pc.type_project_name("")
        assert not pc.project_save_enabled()

    def test_TC_05_vif_generator_link_present(self, pc: ProductCapabilityPage):
        assert pc.vif_generator_href(), "USB-IF VIF Generator link has no href"

    @pytest.mark.hardware
    @pytest.mark.parametrize("profile", ["consumer_spr_100w", "provider_epr_240w"])
    def test_TC_06_select_dut_type_and_cable_persists(self, pc: ProductCapabilityPage, api_client: C2ApiClient,
                                                      profile: str):
        data = test_data_manager.get_profile(profile)
        original = (pc.dut_type(), pc.cable())
        try:
            pc.select_dut_type(data["dut_type"])
            pc.select_cable(data["cable"])
            port_a = api_client.get_port_configurations()["ports"]["PortA"]
            assert (port_a["dutType"], port_a["cableType"]) == (data["dut_type"], data["cable"])
        finally:
            pc.select_dut_type(original[0])
            pc.select_cable(original[1])

    @pytest.mark.hardware
    @pytest.mark.requires_tester
    def test_TC_07_read_device_data(self, pc: ProductCapabilityPage):
        pc.read_device_data()
