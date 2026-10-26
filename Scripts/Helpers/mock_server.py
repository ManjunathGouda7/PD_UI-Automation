"""
Offline mock of the GRL USB PD C2 (V-DPWR-EPR) Web API.

Purpose: develop and run the API test suite without the GRL software / tester.
It serves API responses only. It deliberately does NOT imitate the web UI - a fake page
would let UI tests pass against something that is not the product - so UI tests are
skipped in mock mode (see conftest.py).

Response shapes mirror the live backend (software 1.1.1.4), including content types:
some endpoints return JSON, others text/plain.
"""
from __future__ import annotations

import http.server
import json
import socket
import socketserver
import threading
import time
from typing import Any

MOCK_SOFTWARE_VERSION = "1.1.1.4"
MOCK_URL_VERSION = "v1.1.4"

_TEST_CASE_TREE = [{
    "key": "V-EPR Test Cases", "title": "V-EPR Test Cases", "ctsVersion": "", "lsTags": [],
    "children": [{
        "key": "Power Delivery 3.2 Tests", "title": "Power Delivery 3.2 Tests", "ctsVersion": "", "lsTags": [],
        "children": [
            {"key": "TEST.PD.PHY.ALL.1 Transmit Bit Rate and the Drift",
             "title": "TEST.PD.PHY.ALL.1 Transmit Bit Rate and the Drift", "ctsVersion": "", "lsTags": [], "children": []},
            {"key": "TEST.PD.PHY.ALL.2 Transmitter Eye Diagram",
             "title": "TEST.PD.PHY.ALL.2 Transmitter Eye Diagram", "ctsVersion": "", "lsTags": [], "children": []},
        ],
    }],
}]

# path -> (payload, content kind) ; kind "json" or "text"
_GET_ROUTES: dict[str, tuple[Any, str]] = {
    "/api/App/GetSoftwareVersion": (MOCK_SOFTWARE_VERSION, "text"),
    "/api/App/GetURLVersionExtension": (MOCK_URL_VERSION, "text"),
    "/api/App/GetAppState": ({"appState": "READY", "connectionState": "DISCONNECTED"}, "json"),
    "/api/App/GetAppMode": ("", "text"),
    "/api/App/GetAppStatusMode": ("EndUser", "json"),
    "/api/App/GetPdModeStatus": ("PDMode", "json"),
    "/api/App/GetDebugLogs": ("[MOCK] debug log\n", "text"),
    "/api/ConnectionSetup/GetIPAddressHistory": ([{"ipAddress": "192.168.255.1", "isActive": False}], "json"),
    "/api/C2Api/GetConnectionStatus": (0, "json"),
    "/api/C2Api/GetSerialNumber": ("", "text"),
    "/api/C2Api/GetTotalPDMessageCount": (0, "json"),
    "/api/C2Api/GetPDMessages": ([], "json"),
    "/api/C2Api/GetCaptureStatus": (0, "json"),
    "/api/TestConfiguration/GetTestCaseList": (_TEST_CASE_TREE, "json"),
    "/api/TestConfiguration/GetCertificationFilter": ("All Supported Certifications", "text"),
    "/api/Results/GetTestResults": ({
        "appStatus": {"appState": "READY", "connectionState": "DISCONNECTED"},
        "testResults": [],
        "summary": {"passCount": 0, "failCount": 0, "incompleteCount": 0, "otherCount": 0,
                    "totalTestCaseCount": 0, "repeatLoop": "", "exPortNumber": "NONE"},
    }, "json"),
    "/api/ReportsGeneration/GetReportInputs": ({
        "manufacturer": "", "modelNumber": "", "remarks": "", "savePath": "", "serialNumber": "",
        "testEngineer": "", "testLab": "", "reportFolderPath": "",
    }, "json"),
    "/api/ReportsGeneration/GetReportFileName": ("", "text"),
    "/api/ReportsGeneration/GetResultsFolderName": ("", "text"),
    "/api/ConnectionSetup": ({
        "defaultIpConfig": True, "firmwareVersion": "N/A", "licenseInfo": [], "portInfo": "5002",
        "serialNumber": "N/A", "testerIpAddress": "192.168.255.1", "testerStatus": "Disconnected",
        "calibration_St_Date": "0001-01-01T00:00:00", "calibration_Sp_Date": "0001-01-01T00:00:00",
        "boardCalibration": "N/A", "noiseWarning": "", "applicationMode": "VDPWR", "buildMode": "APP",
        "invalidFRAMVersion": False, "framWarning": "",
    }, "json"),
    "/api/ProductCapability/GetPortConfigurations": ({
        "vifFileName": "Load XML VIF File", "executionMode": "InformationalMode", "rerenderRandomNum": 0,
        "ports": {p: {"port": p, "dutType": "Provider Only", "cableType": "GRL-SPL EPR Test Cable 1",
                      "portLable": "", "stateMachineType": "SRC"} for p in ("PortA", "PortB")},
    }, "json"),
    "/api/ConfigControl/GetC2Configuration": ({
        "portType": 0, "controllerMode": 0, "cableType": 0, "pdSpecType": 0, "appMode": 0,
        "cableEmulation": 0, "rpLevel": 0, "fixtureSelection": 0,
    }, "json"),
    "/swagger/v0.1/swagger.json": ({
        "swagger": "2.0", "info": {"title": "C2 Web API Mock", "version": "v0.1"},
        "paths": {p: {"get": {}} for p in [
            "/api/App/GetSoftwareVersion", "/api/App/GetAppState", "/api/Results/GetTestResults",
        ]},
    }, "json"),
}


class MockC2RequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler simulating the GRL C2 Web API."""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
        pass

    def _send(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data: Any, status: int = 200) -> None:
        self._send(json.dumps(data).encode("utf-8"), "application/json; charset=utf-8", status)

    def _send_text(self, text: str, content_type: str = "text/plain; charset=utf-8", status: int = 200) -> None:
        self._send(text.encode("utf-8"), content_type, status)

    def _path(self) -> str:
        return self.path.split("?")[0].rstrip("/") or "/"

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self) -> None:
        path = self._path()
        if path in ("/swagger/index.html", "/swagger"):
            self._send_text("<html><title>Swagger UI</title><body>C2 Web API mock</body></html>",
                            "text/html; charset=utf-8")
            return
        if path in _GET_ROUTES:
            payload, kind = _GET_ROUTES[path]
            if kind == "json":
                self._send_json(payload)
            else:
                self._send_text(str(payload))
            return
        if path == "/api/ReportsGeneration/GetReportFile":
            self._send_text("", "text/html; charset=utf-8")
            return
        self._send_json({"error": f"mock has no route for GET {path}"}, status=404)

    def _command(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)
        self._send_json(True)

    do_POST = _command
    do_PUT = _command
    do_DELETE = _command


class MockC2Server:
    """Manages the lifecycle of the background mock HTTP server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5003):
        self.host = host
        self.port = port
        self.server: socketserver.ThreadingTCPServer | None = None
        self.thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self.server is not None

    @staticmethod
    def port_in_use(port: int) -> bool:
        """True if anything accepts connections on localhost:port (IPv4 or IPv6)."""
        for family, addr in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
            try:
                with socket.socket(family, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    if s.connect_ex((addr, port)) == 0:
                        return True
            except OSError:
                continue
        return False

    def start(self) -> bool:
        if self.running:
            return True
        # Windows lets a specific-address bind succeed next to a wildcard listener, which would
        # silently shadow the real GRL backend for local clients - so refuse any occupied port.
        if self.port_in_use(self.port):
            return False
        socketserver.ThreadingTCPServer.allow_reuse_address = False
        socketserver.ThreadingTCPServer.daemon_threads = True
        try:
            self.server = socketserver.ThreadingTCPServer((self.host, self.port), MockC2RequestHandler)
        except OSError:
            return False
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return True

    def stop(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None


_mock_instance: MockC2Server | None = None


def start_mock_service(port: int = 5003) -> bool:
    global _mock_instance
    if _mock_instance is None:
        _mock_instance = MockC2Server(port=port)
    return _mock_instance.start()


def stop_mock_service() -> None:
    global _mock_instance
    if _mock_instance:
        _mock_instance.stop()
        _mock_instance = None


if __name__ == "__main__":
    server = MockC2Server(port=5003)
    if not server.start():
        raise SystemExit("Port 5003 is in use (the real C2 software is probably running).")
    print("Mock C2 API on http://127.0.0.1:5003 - Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
