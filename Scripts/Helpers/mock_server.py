"""
Lightweight Mock Server for GRL USB PD C2 (V-DPWR-EPR).
Enables 100% offline development, local unit testing, and headless CI/CD execution
without requiring physical hardware or the proprietary C2 backend.
"""
from __future__ import annotations

import http.server
import json
import socketserver
import threading
import time
from typing import Any

MOCK_HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>GRL-V-DPWR-EPR - USB Power Delivery & Type-C Tester</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0b0f; color: #fff; margin: 0; padding: 20px; }
        .nav-tabs { display: flex; gap: 10px; border-bottom: 2px solid #232936; padding-bottom: 10px; }
        .nav-tab { background: #1e2433; border: 1px solid #2d3548; color: #fff; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
        .panel { display: block; margin-top: 20px; padding: 20px; background: #131622; border-radius: 8px; border: 1px solid #232936; }
        button { background: #ff7800; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: bold; }
        select, input { background: #1e2433; color: #fff; border: 1px solid #2d3548; padding: 6px 10px; border-radius: 4px; }
        .badge-pass { background: #10b981; padding: 4px 8px; border-radius: 4px; }
        .badge-fail { background: #ef4444; padding: 4px 8px; border-radius: 4px; }
        .chart-container { height: 150px; background: #0d0e14; border: 1px dashed #232936; margin: 10px 0; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="nav-tabs">
        <button class="nav-tab">Connection Setup</button>
        <button class="nav-tab">Product Capability</button>
        <button class="nav-tab">Test Config</button>
        <button class="nav-tab">Results</button>
        <button class="nav-tab">Report</button>
        <button class="nav-tab">Configure</button>
        <button class="nav-tab">LoopBack</button>
        <button class="nav-tab">Help</button>
    </div>

    <!-- Panel 1: Connection Setup -->
    <div id="connection-panel" class="panel">
        <h4>Tester Status</h4>
        <button id="scanBtn" class="scanBtn">Scan Network</button>
        <select class="ip-select ipInput">
            <option value="192.168.102.76">192.168.102.76</option>
            <option value="192.168.255.1">192.168.255.1</option>
        </select>
        <button id="connectBtn" class="connectBtn">Connect</button>
        <button id="disconnectBtn">Disconnect</button>
        <div class="status-indicators">
            <span>Firmware: OK</span>
            <span>Calibration: Valid</span>
            <span>Licenses: Active</span>
        </div>
    </div>

    <!-- Panel 2: Product Capability -->
    <div id="product-cap-panel" class="panel">
        <button id="loadVifBtn">Load VIF</button>
        <button id="clearVifBtn">Clear VIF</button>
        <button class="btnReadDevice">Read Device</button>
        <select class="dut-role">
            <option value="Provider Only">Provider Only</option>
            <option value="Consumer Only">Consumer Only</option>
            <option value="Dual-Role Power">Dual-Role Power</option>
        </select>
        <select class="cable-select">
            <option value="GRL-SPL EPR Cable 1">GRL-SPL EPR Cable 1</option>
        </select>
        <input name="cert" placeholder="Certification ID" value="GRL-CERT-001" />
    </div>

    <!-- Panel 3: Test Config -->
    <div id="test-config-panel" class="panel">
        <button id="selectAll">Select All</button>
        <button id="deselectAll">Deselect All</button>
        <input type="search" placeholder="Search Test Cases" />
        <input type="checkbox" id="selectAllCheckbox" />
        <label><input type="checkbox" class="test-item-checkbox test-check" checked /> Power Delivery 3.2 Tests</label>
        <label><input type="checkbox" class="test-item-checkbox test-check" checked /> USB-C Functional Tests</label>
        <label><input type="checkbox" class="test-item-checkbox test-check" checked /> IEC Functional Safety Tests</label>
        <div class="dut-info">DUT Information</div>
        <input name="engineer" placeholder="Engineer Name" value="GRL QA Lead" />
    </div>

    <!-- Panel 4: Results -->
    <div id="results-panel" class="panel">
        <div class="chart-container chartist"></div>
        <button title="Zoom In">Zoom In</button>
        <button title="Zoom Out">Zoom Out</button>
        <button>Reset</button>
        <button title="Pan">Pan</button>
        <button>H-Marker</button>
        <button>V-Marker</button>
        <span class="badge-pass">Pass: 207</span>
        <span class="badge-fail">Fail: 0</span>
        <table class="results-table">
            <tbody>
                <tr class="results-row"><td>TC_01</td><td>PASSED</td><td>1.2s</td></tr>
            </tbody>
        </table>
    </div>

    <!-- Panel 5: Report -->
    <div id="report-panel" class="panel">
        <button>View Report</button>
        <button>Download HTML Report</button>
        <button>Download DUT Report Data</button>
        <input class="report-dir" placeholder="Report Path" value="./Reports" />
    </div>

    <!-- Panel 6: Configure -->
    <div id="configure-panel" class="panel">
        <select class="cfg-mode"><option>UFP/Sink</option></select>
        <button class="vbus-btn">VBUS 5V</button>
        <input class="load-input" value="1.5" />
    </div>

    <!-- Panel 7: Loopback -->
    <div id="loopback-panel" class="panel">
        <button class="loopback-start">Start Loopback</button>
        <div class="throughput-val">10.0 Gbps</div>
    </div>

    <!-- Panel 8: Help -->
    <div id="help-panel" class="panel">
        <div class="diag-status">All Systems Operational</div>
        <button class="export-logs">Export Debug Logs</button>
    </div>
</body>
</html>
"""


class MockC2RequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP Request Handler simulating GRL C2 Web API and UI."""

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy standard logging
        pass

    def _send_json(self, data: Any, status_code: int = 200) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _send_text(self, text: str, content_type: str = "text/plain", status_code: int = 200) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self) -> None:
        path = self.path.split("?")[0].rstrip("/")

        # Web UI Pages
        if path in ("", "/", "/index.html", "/v1.1.1.html"):
            self._send_text(MOCK_HTML_PAGE, "text/html")
            return

        # Swagger Docs
        if path in ("/swagger/index.html", "/swagger"):
            self._send_text("<html><title>C2WebAPI Mock Swagger</title><body>Swagger UI Mock</body></html>", "text/html")
            return

        if path == "/swagger/v0.1/swagger.json":
            self._send_json({
                "swagger": "2.0",
                "info": {"title": "C2 Web API Mock", "version": "0.1"},
                "paths": {
                    "/api/App/GetSoftwareVersion": {"get": {"tags": ["App"]}},
                    "/api/App/GetAppState": {"get": {"tags": ["App"]}},
                    "/api/Results/GetTestResults": {"get": {"tags": ["Results"]}},
                }
            })
            return

        # App Controller
        if path == "/api/App/GetSoftwareVersion":
            self._send_text("1.1.1.1")
            return
        if path == "/api/App/GetURLVersionExtension":
            self._send_text("v1.1.1")
            return
        if path == "/api/App/GetAppState":
            self._send_json({"appState": "READY", "connectionState": "CONNECTED"})
            return
        if path == "/api/App/GetAppMode":
            self._send_text("Compliance")
            return
        if path == "/api/App/GetAppStatusMode":
            self._send_text("EndUser")
            return
        if path == "/api/App/GetPdModeStatus":
            self._send_text("PDMode")
            return
        if path == "/api/App/GetDebugLogs":
            self._send_text("[MOCK LOG] Tester initialized successfully.\n")
            return

        # ConnectionSetup Controller
        if path == "/api/ConnectionSetup/GetIPAddressHistory":
            self._send_json([
                {"ipAddress": "192.168.102.76", "isActive": True},
                {"ipAddress": "192.168.255.1", "isActive": False}
            ])
            return
        if path == "/api/ConnectionSetup/DiscoverIPAddress":
            self._send_json(["192.168.102.76"])
            return
        if path.startswith("/api/ConnectionSetup/"):
            self._send_json({"status": "CONNECTED", "ip": "192.168.102.76"})
            return

        # C2Api Controller
        if path == "/api/C2Api/GetConnectionStatus":
            self._send_text("1")
            return
        if path == "/api/C2Api/GetSerialNumber":
            self._send_text("GRL-V-DPWR-EPR-0002")
            return
        if path in ("/api/C2Api/Attach", "/api/C2Api/Detach"):
            self._send_json({"status": "OK"})
            return
        if path == "/api/C2Api/GetTotalPDMessageCount":
            self._send_text("42")
            return
        if path == "/api/C2Api/GetPDMessages":
            self._send_json([{"id": 1, "type": "Source_Capabilities", "voltage": 5.0, "current": 3.0}])
            return

        # TestConfiguration Controller
        if path == "/api/TestConfiguration/GetTestCaseList":
            self._send_json([
                {"key": "TC_01", "title": "Power Delivery 3.2 Negotiation", "children": []},
                {"key": "TC_02", "title": "USB-C Functional VBUS Test", "children": []},
            ])
            return
        if path == "/api/TestConfiguration/StopTestExecution":
            self._send_json({"status": "STOPPED"})
            return

        # Results Controller
        if path == "/api/Results/GetTestResults":
            self._send_json({
                "appStatus": {"appState": "READY", "connectionState": "CONNECTED"},
                "testResults": [
                    {"testCaseId": "TC_01", "result": "PASS", "duration": 1.2},
                    {"testCaseId": "TC_02", "result": "PASS", "duration": 1.5}
                ],
                "summary": {
                    "passCount": 207,
                    "failCount": 0,
                    "incompleteCount": 0,
                    "otherCount": 0,
                    "totalTestCaseCount": 207,
                    "repeatLoop": "1",
                    "exPortNumber": "Port 1"
                }
            })
            return

        # Reports Controller
        if path == "/api/ReportsGeneration/GetReportFile":
            self._send_text("<html><body>Mock Report Content</body></html>", "text/html")
            return
        if path == "/api/ReportsGeneration/GetReportFileName":
            self._send_text("USB_PD_Report.html")
            return

        # Generic fallback for any other GET API
        self._send_json({"status": "MOCK_OK", "endpoint": path})

    def do_POST(self) -> None:
        path = self.path.split("?")[0].rstrip("/")
        self._send_json({"status": "SUCCESS", "action": path})

    def do_PUT(self) -> None:
        path = self.path.split("?")[0].rstrip("/")
        self._send_json({"status": "SUCCESS", "updated": path})

    def do_DELETE(self) -> None:
        path = self.path.split("?")[0].rstrip("/")
        self._send_json({"status": "SUCCESS", "cleared": path})


class MockC2Server:
    """Manages the lifecycle of the background mock HTTP server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5003):
        self.host = host
        self.port = port
        self.server: socketserver.TCPServer | None = None
        self.thread: threading.Thread | None = None
        self.running = False

    def start(self) -> bool:
        if self.running:
            return True

        socketserver.TCPServer.allow_reuse_address = True
        try:
            self.server = socketserver.TCPServer((self.host, self.port), MockC2RequestHandler)
        except OSError:
            # Port might already be in use (e.g. real server is running)
            return False

        self.running = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        time.sleep(0.2)
        return True

    def stop(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        self.running = False


# Module level singleton
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
    print("Starting Mock GRL USB PD C2 Server on http://localhost:5003 ...")
    server = MockC2Server(port=5003)
    if server.start():
        print("Mock server online. Press Ctrl+C to terminate.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.stop()
            print("Mock server stopped.")
    else:
        print("Could not start mock server. Port 5003 is already active (Live C2 server is likely running).")
