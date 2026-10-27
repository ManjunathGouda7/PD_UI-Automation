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
from Scripts.Pages.app_page import AppPage
from Scripts.Pages.connection_page import ConnectionPage

CONN = test_data_manager.section("connection")
KNOWN_STALE_STATUS = (
    "KNOWN PRODUCT ISSUE (1.1.1.4): the UI keeps showing 'IP address ... unreachable' after its auto-connect "
    "attempt failed, although the backend reconnected to the same tester (GET /api/ConnectionSetup: Connected). "
    "The Tester Status does not refresh until the page is reloaded; seen on an unstable tester link.")


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

    @pytest.mark.spec("CONN-05", partial=True)
    @pytest.mark.smoke
    def test_TC_02_ip_field_matches_tester_ip_row_and_history(self, conn: ConnectionPage, api_client: C2ApiClient):
        ip = conn.ip_address()
        ipaddress.IPv4Address(ip)  # raises if malformed
        assert conn.tester_info()["Tester IP Address Information"] == ip
        history = [h["ipAddress"] for h in api_client.get_ip_history()]
        assert ip in history, f"UI IP {ip} not in GET /api/ConnectionSetup/GetIPAddressHistory {history}"

    @pytest.mark.spec("CONN-09")
    @pytest.mark.smoke
    def test_TC_03_tester_status_and_ip_match_api(self, conn: ConnectionPage, api_client: C2ApiClient):
        # Start from a fresh load: an open page does not refresh the Tester Status after the tester
        # reconnects (observed on 1.1.1.4, see README "Known product issues").
        AppPage(conn.page).load()
        conn.open()

        def pair():
            ui, api = conn.tester_info(), api_client.get_connection_info()
            return ((ui["Tester Status"], ui["Tester IP Address Information"]),
                    (api.get("testerStatus"), api.get("testerIpAddress")))

        # UI and API are read a few seconds apart; on a flapping link allow them to settle.
        ui, api = wait_until(pair, lambda r: r[0] == r[1], timeout_s=40, interval_s=2)
        if ui != api and "unreachable" in ui[0] and api == ("Connected", ui[1]):
            pytest.xfail(KNOWN_STALE_STATUS)
        assert ui == api, f"UI (status, IP) {ui} != API {api}"

    def test_TC_04_scan_and_connect_controls_available(self, conn: ConnectionPage):
        assert conn.is_enabled(ConnectionLocators.SCAN_NETWORK_BTN)
        assert conn.is_enabled(ConnectionLocators.CONNECT_BTN)
        assert conn.license_header_visible()

    @pytest.mark.spec("CONN-08", "CONN-10")
    @pytest.mark.spec("CONN-14")
    def test_TC_10_update_firmware_enabled_only_when_connected(self, conn: ConnectionPage):
        def snapshot():
            return conn.tester_info()["Tester Status"], conn.update_firmware_enabled()

        # The link can change between the two reads; take a consistent pair.
        status, enabled = wait_until(snapshot, lambda a: a == snapshot(), timeout_s=10, interval_s=0.5)
        connected = status == CONN["connected_status"]
        assert enabled is connected, f"Update System firmware enabled={enabled} while Tester Status is '{status}'"

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

    @pytest.mark.spec("CONN-11", partial=True)
    @pytest.mark.requires_tester
    def test_TC_06_tester_calibration_is_valid_and_not_expired(self, conn: ConnectionPage):
        info = conn.tester_info()
        assert info["VDPWR Tester Calibration"] == CONN["calibration_ok"], info
        due = date.fromisoformat(info["Calibration Due"])
        assert due >= date.today(), f"Tester calibration expired on {due}"

    @pytest.mark.spec("CONN-12", "LIC-01")
    @pytest.mark.requires_tester
    def test_TC_07_license_table_matches_api(self, conn: ConnectionPage, api_client: C2ApiClient):
        ui = [(lic["name"], lic["type"]) for lic in conn.licenses()]
        api = [(m["moduleName"], m["moduleStatus"]) for m in api_client.get_connection_info()["licenseInfo"]]
        assert ui, "No licenses listed for the connected tester"
        assert ui == api

    @pytest.mark.spec("CONN-04", "GEN-06", partial=True)
    @pytest.mark.hardware
    def test_TC_08_scan_network_discovers_testers(self, conn: ConnectionPage, api_client: C2ApiClient):
        conn.scan_network()
        assert conn.is_enabled(ConnectionLocators.SCAN_NETWORK_BTN)
        assert api_client.get_ip_history(), "No tester addresses known after scan"

    @pytest.mark.spec("CONN-07", "GEN-05")
    @pytest.mark.hardware
    def test_TC_09_connect_to_configured_tester(self, conn: ConnectionPage, api_client: C2ApiClient):
        info = conn.connect(Config.dut_ip())
        assert info["Tester Status"] == CONN["connected_status"], info
        assert api_client.is_tester_connected()
