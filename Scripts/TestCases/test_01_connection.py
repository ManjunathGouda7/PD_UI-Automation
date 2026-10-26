"""
Panel 1: Connection Setup.
Spec: Connection Setup #4 - #13.
"""
from datetime import date
import ipaddress
import re

from playwright.sync_api import Page
import pytest

from Scripts.Data.test_data_manager import test_data_manager
from Scripts.Helpers.api_client import C2ApiClient
from Scripts.Helpers.config import Config
from Scripts.Helpers.Locators import ConnectionLocators
from Scripts.Helpers.waits import wait_until
from Scripts.Pages.connection_page import ConnectionPage

CONN = test_data_manager.section("connection")


@pytest.fixture
def conn(page: Page) -> ConnectionPage:
    return ConnectionPage(page).open()


@pytest.mark.connection
class TestConnectionPanel:
    @pytest.mark.smoke
    def test_TC_01_tester_info_table_has_all_fields(self, conn: ConnectionPage):
        info = conn.tester_info()
        assert list(info) == CONN["tester_fields"]
        assert all(v for v in info.values()), f"Empty tester info cell: {info}"

    @pytest.mark.smoke
    def test_TC_02_ip_field_matches_tester_ip_row_and_history(self, conn: ConnectionPage, api_client: C2ApiClient):
        ip = conn.ip_address()
        ipaddress.IPv4Address(ip)  # raises if malformed
        assert conn.tester_info()["Tester IP Address Information"] == ip
        history = [h["ipAddress"] for h in api_client.get_ip_history()]
        assert ip in history, f"UI IP {ip} not in GET /api/ConnectionSetup/GetIPAddressHistory {history}"

    @pytest.mark.smoke
    def test_TC_03_tester_status_and_ip_match_api(self, conn: ConnectionPage, api_client: C2ApiClient):
        ui = conn.tester_info()
        api = api_client.get_connection_info()
        assert ui["Tester Status"] == api["testerStatus"], f"UI '{ui['Tester Status']}' != API '{api['testerStatus']}'"
        assert ui["Tester IP Address Information"] == api["testerIpAddress"]

    def test_TC_04_scan_and_connect_controls_available(self, conn: ConnectionPage):
        assert conn.is_enabled(ConnectionLocators.SCAN_NETWORK_BTN)
        assert conn.is_enabled(ConnectionLocators.CONNECT_BTN)
        assert conn.license_header_visible()

    @pytest.mark.requires_tester
    def test_TC_05_connected_tester_details_match_api(self, conn: ConnectionPage, api_client: C2ApiClient):
        def expected() -> dict[str, str]:
            api = api_client.get_connection_info()
            return {
                "Tester Status": api.get("testerStatus", ""),
                "Serial Number": api.get("serialNumber", ""),
                "Firmware Version": api.get("firmwareVersion", ""),
                "Tester IP Address Information": api.get("testerIpAddress", ""),
                "Last Calibration Date": (api.get("calibration_St_Date") or "")[:10],
                "Calibration Due": (api.get("calibration_Sp_Date") or "")[:10],
                "VDPWR Tester Calibration": api.get("boardCalibration", ""),
            }

        # Right after (re)connect the UI briefly shows placeholder calibration data; allow it to settle.
        ui, api = wait_until(lambda: (conn.tester_info(), expected()), lambda r: r[0] == r[1], timeout_s=30)
        assert ui == api
        assert ui["Tester Status"] == CONN["connected_status"]
        assert re.fullmatch(r"GRL-V-DPWR-EPR-\d+", ui["Serial Number"]), ui
        assert "0001-01-01" not in (ui["Last Calibration Date"], ui["Calibration Due"]), ui

    @pytest.mark.requires_tester
    def test_TC_06_tester_calibration_is_valid_and_not_expired(self, conn: ConnectionPage):
        info = conn.tester_info()
        assert info["VDPWR Tester Calibration"] == CONN["calibration_ok"], info
        due = date.fromisoformat(info["Calibration Due"])
        assert due >= date.today(), f"Tester calibration expired on {due}"

    @pytest.mark.requires_tester
    def test_TC_07_license_table_matches_api(self, conn: ConnectionPage, api_client: C2ApiClient):
        ui = [(lic["name"], lic["type"]) for lic in conn.licenses()]
        api = [(m["moduleName"], m["moduleStatus"]) for m in api_client.get_connection_info()["licenseInfo"]]
        assert ui, "No licenses listed for the connected tester"
        assert ui == api

    @pytest.mark.hardware
    def test_TC_08_scan_network_discovers_testers(self, conn: ConnectionPage, api_client: C2ApiClient):
        conn.scan_network()
        assert conn.is_enabled(ConnectionLocators.SCAN_NETWORK_BTN)
        assert api_client.get_ip_history(), "No tester addresses known after scan"

    @pytest.mark.hardware
    def test_TC_09_connect_to_configured_tester(self, conn: ConnectionPage, api_client: C2ApiClient):
        info = conn.connect(Config.dut_ip())
        assert info["Tester Status"] == CONN["connected_status"], info
        assert api_client.is_tester_connected()
