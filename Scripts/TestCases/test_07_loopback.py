"""
Panel 7: LoopBack.
Spec: LoopBack.
"""
import re

from playwright.sync_api import Page
import pytest

from Scripts.Data.test_data_manager import test_data_manager
from Scripts.Pages.loopback_page import LoopBackPage

LB = test_data_manager.section("loopback")


@pytest.fixture
def lb(page: Page) -> LoopBackPage:
    return LoopBackPage(page).open()


@pytest.mark.loopback
class TestLoopBackPanel:
    @pytest.mark.spec("LB-02", partial=True)
    @pytest.mark.smoke
    def test_TC_01_data_fields_present_with_units(self, lb: LoopBackPage):
        data = lb.data()
        assert list(data) == LB["data_labels"]
        assert re.fullmatch(r"[\d.]+ MB", data["Transferred Data"]), data
        assert re.fullmatch(r"[\d.]+ MB", data["Received Data"]), data
        assert re.fullmatch(r"[\d.]+ Mbps", data["Effective Throughput"]), data
        assert data["Status"], "LoopBack status is empty"

    @pytest.mark.spec("LB-01", partial=True)
    def test_TC_02_start_stop_disabled_without_device(self, lb: LoopBackPage):
        if lb.selected_device():
            pytest.skip("A loopback device is selected")
        assert not lb.start_enabled()
        assert not lb.stop_enabled()

    @pytest.mark.spec("LB-01", partial=True)
    def test_TC_03_device_list_has_placeholder(self, lb: LoopBackPage):
        assert lb.device_options()[0] == "Select a device..."
