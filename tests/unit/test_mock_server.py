"""Unit tests for the offline API mock (runs on a free local port)."""
import socket

import pytest
import requests

from Scripts.Helpers.mock_server import MockC2Server


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server():
    srv = MockC2Server(port=_free_port())
    assert srv.start()
    yield f"http://127.0.0.1:{srv.port}"
    srv.stop()


def test_json_and_text_routes(server):
    state = requests.get(f"{server}/api/App/GetAppState", timeout=5)
    assert state.headers["Content-Type"].startswith("application/json")
    assert state.json() == {"appState": "READY", "connectionState": "DISCONNECTED"}
    version = requests.get(f"{server}/api/App/GetSoftwareVersion", timeout=5)
    assert version.headers["Content-Type"].startswith("text/plain")
    assert version.text.count(".") == 3


def test_results_summary_shape(server):
    summary = requests.get(f"{server}/api/Results/GetTestResults", timeout=5).json()["summary"]
    assert set(summary) >= {"passCount", "failCount", "incompleteCount", "otherCount", "totalTestCaseCount"}


def test_unknown_route_is_404_and_commands_succeed(server):
    assert requests.get(f"{server}/api/Nope", timeout=5).status_code == 404
    assert requests.post(f"{server}/api/Anything", json=[1], timeout=5).json() is True


def test_refuses_an_occupied_port(server):
    port = int(server.rsplit(":", 1)[1])
    assert MockC2Server.port_in_use(port)
    assert not MockC2Server(port=port).start()
