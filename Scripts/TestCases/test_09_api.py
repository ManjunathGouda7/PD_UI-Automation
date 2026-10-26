"""
REST API suite for GRL USB PD C2 (V-DPWR-EPR) - no browser.
Read-only endpoints only; endpoints that drive hardware are covered by `hardware` UI tests.
"""
import ipaddress
from pathlib import Path
import re

import pytest

from Scripts.Data.test_data_manager import test_data_manager
from Scripts.Helpers.api_client import C2ApiClient
from Scripts.Helpers.config import Config
from Scripts.Helpers.swagger_contract import SwaggerContract

API_CLIENT_SRC = Path(__file__).resolve().parent.parent / "Helpers" / "api_client.py"
live_only = pytest.mark.skipif(Config.is_mock_mode(), reason="needs the real backend's Swagger spec")


@pytest.fixture(scope="module")
def contract(api_client: C2ApiClient) -> SwaggerContract:
    spec = api_client.get_swagger_spec()
    assert spec, "GET /swagger/v0.1/swagger.json returned nothing"
    return SwaggerContract(spec)


@pytest.mark.api
class TestAppApi:
    @pytest.mark.smoke
    def test_server_online(self, api_client: C2ApiClient):
        assert api_client.is_online()

    @pytest.mark.smoke
    def test_software_version_format(self, api_client: C2ApiClient):
        assert re.fullmatch(r"\d+(\.\d+){2,3}", api_client.get_software_version())

    def test_url_version_extension_resolves_ui(self, api_client: C2ApiClient):
        ext = api_client.get_url_version_extension()
        assert re.fullmatch(r"v\d+(\.\d+)+", ext), ext
        if not Config.is_mock_mode():
            res = api_client.session.get(api_client._url(f"{ext}.html"), timeout=10)
            assert res.status_code == 200, f"/{ext}.html -> HTTP {res.status_code}"

    def test_app_state_values(self, api_client: C2ApiClient):
        state = api_client.get_app_state()
        assert state.get("appState") in ("READY", "BUSY", "ERROR"), state
        assert state.get("connectionState") in ("CONNECTED", "DISCONNECTED"), state

    def test_app_status_and_pd_mode(self, api_client: C2ApiClient):
        assert api_client.get_app_status_mode()
        assert api_client.get_pd_mode_status()


@pytest.mark.api
class TestConnectionApi:
    def test_ip_history_entries(self, api_client: C2ApiClient):
        history = api_client.get_ip_history()
        assert isinstance(history, list)
        for entry in history:
            ipaddress.IPv4Address(entry["ipAddress"])
            assert isinstance(entry["isActive"], bool)
        assert sum(e["isActive"] for e in history) <= 1, f"More than one active tester: {history}"

    def test_connection_status_is_binary(self, api_client: C2ApiClient):
        assert api_client.get_connection_status() in (0, 1)


@pytest.mark.api
class TestTestConfigApi:
    def test_test_case_tree_keys_unique(self, api_client: C2ApiClient):
        keys: list[str] = []

        def walk(nodes):
            for n in nodes:
                assert n.get("key") and n.get("title"), n
                keys.append(n["key"])
                walk(n.get("children") or [])

        walk(api_client.get_test_case_list())
        assert keys, "Empty test case list"
        assert len(keys) == len(set(keys)), "Duplicate test case keys"
        assert api_client.count_test_cases() > 0

    def test_certification_filter_is_known(self, api_client: C2ApiClient):
        known = test_data_manager.section("test_config")["certifications"]
        assert api_client.get_certification_filter() in known


@pytest.mark.api
class TestResultsApi:
    @pytest.mark.smoke
    def test_results_summary_counts(self, api_client: C2ApiClient):
        summary = api_client.get_test_results()["summary"]
        counts = [summary[k] for k in ("passCount", "failCount", "incompleteCount", "otherCount")]
        assert all(isinstance(c, int) and c >= 0 for c in counts), summary
        if summary["totalTestCaseCount"]:
            assert sum(counts) <= summary["totalTestCaseCount"], summary

    def test_results_list_matches_summary_when_empty(self, api_client: C2ApiClient):
        results = api_client.get_test_results()
        if results["testResults"]:
            pytest.skip("Results present; emptiness check not applicable")
        s = results["summary"]
        assert s["passCount"] == s["failCount"] == s["incompleteCount"] == s["otherCount"] == 0


@pytest.mark.api
class TestProductCapabilityApi:
    def test_port_configurations(self, api_client: C2ApiClient):
        data = api_client.get_port_configurations()
        pc = test_data_manager.section("product_capability")
        assert data["executionMode"] in ("ComplianceMode", "InformationalMode")
        for name, port in data["ports"].items():
            assert port["dutType"] in pc["dut_types"], (name, port)
            assert port["cableType"] in pc["cables"], (name, port)


@pytest.mark.api
@live_only
class TestApiContract:
    """Detects backend changes that would silently break C2ApiClient."""

    def test_spec_size(self, contract: SwaggerContract):
        assert len(contract.spec["paths"]) >= 288

    def test_every_client_endpoint_exists_in_spec(self, contract: SwaggerContract):
        src = API_CLIENT_SRC.read_text(encoding="utf-8")
        calls = re.findall(r'_request\(\s*"(GET|POST|PUT|DELETE)",\s*f?"(api/[^"]+)"', src)
        assert calls, "No endpoints parsed from api_client.py"
        missing = [f"{m} /{p}" for m, p in calls if not contract.has_operation(m, p)]
        assert not missing, f"Endpoints used by C2ApiClient but absent from Swagger: {missing}"

    @pytest.mark.parametrize("path, fetch", [
        ("/api/App/GetAppState", lambda c: c.get_app_state()),
        ("/api/Results/GetTestResults", lambda c: c.get_test_results()),
        ("/api/ConnectionSetup/GetIPAddressHistory", lambda c: c.get_ip_history()),
        ("/api/ReportsGeneration/GetReportInputs", lambda c: c.get_report_inputs()),
        ("/api/ConfigControl/GetC2Configuration", lambda c: c.get_c2_configuration()),
        ("/api/ProductCapability/GetPortConfigurations", lambda c: c.get_port_configurations()),
        ("/api/TestConfiguration/GetTestCaseList", lambda c: c.get_test_case_list()),
    ], ids=lambda v: v.rsplit("/", 1)[-1] if isinstance(v, str) else "")
    def test_response_matches_schema(self, contract: SwaggerContract, api_client: C2ApiClient, path, fetch):
        schema = contract.response_schema(path)
        assert schema, f"No 200 schema published for {path}"
        errors = contract.validate(fetch(api_client), schema)
        assert not errors, f"{path} violates its Swagger schema:\n" + "\n".join(errors[:20])
