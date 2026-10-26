"""
API Client for GRL USB PD C2 (V-DPWR-EPR) Web API.
Provides high-level Python bindings for the 288 Swagger REST API endpoints
running at http://localhost:5003/swagger/index.html.
"""
from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from Scripts.Helpers.config import Config
from Scripts.Helpers.logger import logger


class C2ApiError(Exception):
    """Exception raised for C2 API request errors."""
    def __init__(self, message: str, status_code: int | None = None, response_text: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class C2ApiClient:
    """
    Client for the GRL-V-DPWR-EPR REST API backend.
    """

    def __init__(self, base_url: str | None = None, timeout: float = 10.0):
        self.base_url = (base_url or Config.api_host()).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        # Retry transient connection errors / 5xx on idempotent reads only; commands are never replayed.
        retry = Retry(
            total=2, connect=2, read=1, backoff_factor=0.5,
            status_forcelist=(502, 503, 504), allowed_methods=frozenset({"GET"}),
            raise_on_status=False,
        )
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.headers.update({
            "User-Agent": "GRL-PD-Automation-Client/1.0",
            "Accept": "application/json, text/plain, */*",
        })

    def _url(self, path: str) -> str:
        clean_path = path.lstrip("/")
        return f"{self.base_url}/{clean_path}"

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = self._url(path)
        kwargs.setdefault("timeout", self.timeout)
        try:
            response = self.session.request(method=method, url=url, **kwargs)
        except requests.exceptions.RequestException as e:
            msg = f"API connection error for {method} {url}: {e}"
            logger.error(msg)
            raise C2ApiError(msg) from e

        if not response.ok:
            msg = f"API request {method} {url} failed with status {response.status_code}: {response.text[:500]}"
            logger.error(msg)
            raise C2ApiError(msg, status_code=response.status_code, response_text=response.text)

        if "application/json" in response.headers.get("Content-Type", ""):
            try:
                return response.json()
            except ValueError:
                return response.text
        return response.text

    # -------------------------------------------------------------------------
    # Health & System APIs (/api/App)
    # -------------------------------------------------------------------------

    def is_online(self) -> bool:
        """Check if the backend server is reachable."""
        try:
            res = self.session.get(self._url("swagger/index.html"), timeout=3.0)
            return res.status_code == 200
        except Exception:
            return False

    def get_swagger_spec(self) -> dict[str, Any] | None:
        """Fetch the full OpenAPI specification."""
        try:
            data = self._request("GET", "swagger/v0.1/swagger.json")
        except C2ApiError as e:
            logger.warning(f"Could not fetch Swagger JSON: {e}")
            return None
        return data if isinstance(data, dict) else None

    def get_software_version(self) -> str:
        """Returns GRL software version (e.g. '1.1.1.1')."""
        val = self._request("GET", "api/App/GetSoftwareVersion")
        return str(val).strip('"').strip("'").strip()

    def get_url_version_extension(self) -> str:
        """Returns UI route extension (e.g. 'v1.1.1')."""
        val = self._request("GET", "api/App/GetURLVersionExtension")
        return str(val).strip('"').strip("'").strip()

    def get_app_state(self) -> dict[str, str]:
        """Returns appState and connectionState (e.g. READY, DISCONNECTED)."""
        data = self._request("GET", "api/App/GetAppState")
        if isinstance(data, dict):
            return data
        return {"raw": str(data)}

    def get_app_mode(self) -> str:
        """Returns current app mode."""
        return str(self._request("GET", "api/App/GetAppMode")).strip('"').strip()

    def get_app_status_mode(self) -> str:
        """Returns app status mode (e.g. EndUser)."""
        return str(self._request("GET", "api/App/GetAppStatusMode")).strip('"').strip()

    def get_pd_mode_status(self) -> str:
        """Returns PD mode status (e.g. PDMode)."""
        return str(self._request("GET", "api/App/GetPdModeStatus")).strip('"').strip()

    def get_debug_logs(self) -> str:
        """Fetch application debug logs."""
        return str(self._request("GET", "api/App/GetDebugLogs"))

    def put_disable_popup_status(self, disable: bool = True) -> Any:
        """Enable or disable modal popups in the application."""
        return self._request("PUT", f"api/App/PutDisablePopUpStatus/{str(disable).lower()}")

    def put_message_box_response(self, reply: str) -> Any:
        """Respond to application prompt or modal dialog (reply is sent as the JSON body)."""
        return self._request("PUT", "api/App/PutMessageBoxResponse", json=reply)

    # -------------------------------------------------------------------------
    # Connection Setup APIs (/api/ConnectionSetup)
    # -------------------------------------------------------------------------

    def get_connection_info(self) -> dict[str, Any]:
        """
        Read-only tester details backing the Connection Setup panel: testerStatus, serialNumber,
        firmwareVersion, testerIpAddress, calibration dates, boardCalibration, licenseInfo, ...
        """
        data = self._request("GET", "api/ConnectionSetup")
        return data if isinstance(data, dict) else {}

    def get_ip_history(self) -> list[dict[str, Any]]:
        """Returns list of recently used IP addresses and active states."""
        data = self._request("GET", "api/ConnectionSetup/GetIPAddressHistory")
        return data if isinstance(data, list) else []

    def discover_ip_address(self) -> Any:
        """Triggers network scan for connected testers."""
        return self._request("GET", "api/ConnectionSetup/DiscoverIPAddress")

    def connect_tester(self, ip_address: str, controller_index: int = 0) -> Any:
        """Connect to hardware tester at specified IP address."""
        logger.info(f"Connecting to hardware tester via API at IP: {ip_address}")
        return self._request("GET", f"api/ConnectionSetup/{controller_index}/{ip_address}")

    def get_latest_firmware_and_eload_version(self) -> Any:
        """Fetch latest available firmware and eload version info."""
        return self._request("GET", "api/ConnectionSetup/LatestFirmwareAndEloadVersion")

    def force_stop_current_execution(self) -> Any:
        """Force stops ongoing test/scan execution."""
        return self._request("GET", "api/ConnectionSetup/ForceStopCurrentExecution")

    # -------------------------------------------------------------------------
    # C2 Hardware Control APIs (/api/C2Api)
    # -------------------------------------------------------------------------

    def get_connection_status(self) -> int:
        """C2 scripting-API link status (0/1). Not the UI tester status - see is_tester_connected()."""
        val = self._request("GET", "api/C2Api/GetConnectionStatus")
        try:
            return int(str(val).strip('"').strip())
        except (ValueError, TypeError):
            return 0

    def get_serial_number(self) -> str:
        """Fetch connected tester serial number."""
        return str(self._request("GET", "api/C2Api/GetSerialNumber")).strip('"').strip()

    def attach(self) -> Any:
        """Simulate physical/electronic cable attachment."""
        logger.info("Triggering C2Api Attach...")
        return self._request("GET", "api/C2Api/Attach")

    def detach(self) -> Any:
        """Simulate physical/electronic cable detachment."""
        logger.info("Triggering C2Api Detach...")
        return self._request("GET", "api/C2Api/Detach")

    def get_pd_messages(self) -> list[dict[str, Any]]:
        """Retrieve logged PD packets/messages."""
        data = self._request("GET", "api/C2Api/GetPDMessages")
        return data if isinstance(data, list) else []

    def get_total_pd_message_count(self) -> int:
        """Returns the total number of captured PD messages."""
        val = self._request("GET", "api/C2Api/GetTotalPDMessageCount")
        try:
            return int(str(val).strip('"').strip())
        except (ValueError, TypeError):
            return 0

    def clear_pd_messages(self) -> Any:
        """Clear captured PD message logs."""
        return self._request("DELETE", "api/C2Api/ClearPDMessages")

    def start_capture(self) -> Any:
        """Start waveform / packet trace capture."""
        return self._request("GET", "api/C2Api/StartCapture")

    def stop_capture(self) -> Any:
        """Stop waveform / packet trace capture."""
        return self._request("GET", "api/C2Api/StopCapture")

    def get_capture_status(self) -> Any:
        """Get capture status."""
        return self._request("GET", "api/C2Api/GetCaptureStatus")

    def set_vbus_voltage(self, voltage_volts: float, current_limit_amps: float, port: str = "ONE") -> Any:
        """Set VBUS source voltage with a current limit (drives tester hardware). port: ONE..FOUR."""
        return self._request(
            "GET",
            "api/C2Api/SetVbusVoltage",
            params={"voltageInVolt": voltage_volts, "currentLimitInAmps": current_limit_amps, "port": port},
        )

    def set_eload_current(
        self,
        voltage_volts: float,
        max_current_amps: float,
        state: str = "ON",
        channel: str = "VBUS",
        port: str = "ONE",
    ) -> Any:
        """Configure the E-Load (drives tester hardware). state: ON/OFF, channel: VBUS/VCONN, port: ONE..FOUR."""
        return self._request(
            "GET",
            "api/C2Api/SetEloadCurrent",
            params={
                "voltageInVolts": voltage_volts,
                "maxCurrentInAmps": max_current_amps,
                "state": state,
                "channel": channel,
                "port": port,
            },
        )

    # -------------------------------------------------------------------------
    # Test Configuration APIs (/api/TestConfiguration)
    # -------------------------------------------------------------------------

    def get_test_case_list(self) -> list[dict[str, Any]]:
        """Retrieve all automated compliance test cases."""
        data = self._request("GET", "api/TestConfiguration/GetTestCaseList")
        return data if isinstance(data, list) else []

    def post_test_list_to_execute(self, test_keys: list[str], rerun_count: int = 0) -> Any:
        """
        Trigger test suite execution for specified test case keys.
        """
        logger.info(f"Executing test cases via API (Count: {len(test_keys)}, Rerun: {rerun_count})")
        return self._request(
            "POST",
            f"api/TestConfiguration/PostTestListToExecute/{rerun_count}",
            json=test_keys,
        )

    def stop_test_execution(self) -> Any:
        """Abort current test execution immediately."""
        logger.info("Stopping test execution via API...")
        return self._request("GET", "api/TestConfiguration/StopTestExecution")

    def get_certification_filter(self) -> str:
        """Get the active certification filter name (e.g. 'All Supported Certifications')."""
        return str(self._request("GET", "api/TestConfiguration/GetCertificationFilter")).strip('"').strip()

    def count_test_cases(self) -> int:
        """Number of leaf test cases in the GetTestCaseList tree."""
        def leaves(node: dict[str, Any]) -> int:
            children = node.get("children") or []
            return 1 if not children else sum(leaves(c) for c in children)
        return sum(leaves(n) for n in self.get_test_case_list())

    def is_tester_connected(self) -> bool:
        """
        True when the app is connected to a tester - the 'Tester Status' the UI shows.
        Source: GET /api/ConnectionSetup testerStatus. (/api/C2Api/GetConnectionStatus reports the
        separate C2 scripting-API link and stays 0 while the UI is connected.)
        """
        try:
            return self.get_connection_info().get("testerStatus") == "Connected"
        except C2ApiError:
            return False

    def put_certification_filter(self, certification: str) -> Any:
        """Set active certification filter."""
        return self._request("PUT", f"api/TestConfiguration/PutCertificationFilter/{certification}")

    # -------------------------------------------------------------------------
    # Test Results APIs (/api/Results)
    # -------------------------------------------------------------------------

    def get_test_results(self) -> dict[str, Any]:
        """
        Retrieve structured test results, including:
        appStatus, testResults array, and summary (passCount, failCount, etc.)
        """
        data = self._request("GET", "api/Results/GetTestResults")
        return data if isinstance(data, dict) else {}

    def clear_test_results(self) -> Any:
        """Clear test results table and counters."""
        logger.info("Clearing test results via API...")
        return self._request("PUT", "api/Results/PutClearTestResults")

    def get_caps_results(self) -> Any:
        """Get capability negotiation results."""
        return self._request("GET", "api/Results/GetCapsResults")

    # -------------------------------------------------------------------------
    # Reports Generation APIs (/api/ReportsGeneration)
    # -------------------------------------------------------------------------

    def get_report_file(self) -> bytes:
        """Download generated report file."""
        url = self._url("api/ReportsGeneration/GetReportFile")
        try:
            res = self.session.get(url, timeout=self.timeout)
        except requests.exceptions.RequestException as e:
            raise C2ApiError(f"API connection error for GET {url}: {e}") from e
        if not res.ok:
            raise C2ApiError(f"GET {url} failed with status {res.status_code}", res.status_code, res.text)
        return res.content

    def get_report_file_name(self) -> str:
        """Get name of generated report file."""
        return str(self._request("GET", "api/ReportsGeneration/GetReportFileName")).strip('"').strip()

    def get_results_folder_name(self) -> str:
        """Get output folder name for test run."""
        return str(self._request("GET", "api/ReportsGeneration/GetResultsFolderName")).strip('"').strip()

    def get_report_inputs(self) -> dict[str, Any]:
        """Get metadata inputs for report generation."""
        data = self._request("GET", "api/ReportsGeneration/GetReportInputs")
        return data if isinstance(data, dict) else {}

    def post_current_test_report(self) -> Any:
        """Trigger generation of current test run report."""
        return self._request("POST", "api/ReportsGeneration/PostCurrentTestReport")

    # -------------------------------------------------------------------------
    # Product Capability APIs (/api/ProductCapability)
    # -------------------------------------------------------------------------

    def get_port_configurations(self) -> dict[str, Any]:
        """VIF file name, execution mode and per-port DUT type / cable (PortA == UI 'Port1')."""
        data = self._request("GET", "api/ProductCapability/GetPortConfigurations")
        return data if isinstance(data, dict) else {}

    # -------------------------------------------------------------------------
    # Config Control APIs (/api/ConfigControl)
    # -------------------------------------------------------------------------

    def get_c2_configuration(self) -> dict[str, Any]:
        """Fetch current hardware configuration settings."""
        data = self._request("GET", "api/ConfigControl/GetC2Configuration")
        return data if isinstance(data, dict) else {}

    def put_simulate_attach_detach(self, selected_type: str) -> Any:
        """Simulate attach/detach cycle with specified type."""
        return self._request("PUT", f"api/ConfigControl/PutSimulateAttachDetach/{selected_type}")


# Singleton convenience instance
c2_api = C2ApiClient()
