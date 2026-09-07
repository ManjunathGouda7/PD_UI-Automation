"""
API Test Suite for GRL USB PD C2 (V-DPWR-EPR).
Direct REST API verification without browser rendering overhead.
"""
import pytest
from Scripts.Helpers.api_client import C2ApiClient


@pytest.mark.smoke
@pytest.mark.api
def test_api_server_online(api_client: C2ApiClient):
    """Verify C2 Web API backend is online and responding."""
    assert api_client.is_online(), "C2 Web API backend is offline or unresponsive."


@pytest.mark.api
def test_api_software_version(api_client: C2ApiClient):
    """Verify backend software version returns expected format."""
    version = api_client.get_software_version()
    assert version, "Software version should not be empty."
    assert "." in version, f"Software version '{version}' expected to contain periods."


@pytest.mark.api
def test_api_url_extension(api_client: C2ApiClient):
    """Verify URL version extension (e.g., v1.1.1)."""
    ext = api_client.get_url_version_extension()
    assert ext.startswith("v"), f"URL extension '{ext}' expected to start with 'v'."


@pytest.mark.api
def test_api_app_state(api_client: C2ApiClient):
    """Verify application state returns appState and connectionState."""
    state = api_client.get_app_state()
    assert isinstance(state, dict), f"Expected dict, got {type(state)}"
    assert "appState" in state, "Missing 'appState' in response"
    assert "connectionState" in state, "Missing 'connectionState' in response"


@pytest.mark.api
def test_api_ip_history(api_client: C2ApiClient):
    """Verify tester IP address history can be retrieved."""
    history = api_client.get_ip_history()
    assert isinstance(history, list), "Expected list of IP history records."


@pytest.mark.api
def test_api_test_results_summary(api_client: C2ApiClient):
    """Verify test results endpoint returns valid summary counters."""
    results = api_client.get_test_results()
    assert isinstance(results, dict), "Expected dict response for test results."
    assert "summary" in results, "Missing 'summary' in test results response."
    summary = results["summary"]
    assert "passCount" in summary
    assert "failCount" in summary
