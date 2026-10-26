"""Unit tests for Scripts.Helpers.config."""
import pytest

from Scripts.Helpers.config import Config


@pytest.fixture(autouse=True)
def _reset_cache():
    Config._cached_resolved_url = None
    yield
    Config._cached_resolved_url = None


@pytest.mark.parametrize("raw, expected", [("true", True), ("1", True), ("YES", True), ("off", False),
                                           ("0", False), ("garbage", False)])
def test_get_bool(monkeypatch, raw, expected):
    monkeypatch.setenv("SOME_FLAG", raw)
    assert Config.get_bool("SOME_FLAG", default=False) is expected


def test_numeric_strings_stay_strings(monkeypatch):
    monkeypatch.setenv("DUT_PORT", "1")
    assert Config.get("DUT_PORT") == "1"


def test_get_int_falls_back_on_garbage(monkeypatch):
    monkeypatch.setenv("UI_TIMEOUT_MS", "abc")
    assert Config.get_int("UI_TIMEOUT_MS", 123) == 123


def test_api_host_strips_page(monkeypatch):
    monkeypatch.setenv("BASE_URL", "http://host:5003/v1.1.4.html")
    assert Config.api_host() == "http://host:5003"


def test_explicit_html_base_url_is_used_as_is(monkeypatch):
    monkeypatch.setenv("BASE_URL", "http://host:5003/v9.9.9.html")
    assert Config.base_url() == "http://host:5003/v9.9.9.html"


def test_unresolvable_version_falls_back_to_host_root(monkeypatch):
    monkeypatch.setenv("BASE_URL", "http://host:5003")
    monkeypatch.setattr(Config, "get_url_version_extension", classmethod(lambda cls, host=None: None))
    assert Config.base_url() == "http://host:5003/"


def test_resolved_version_builds_page_url(monkeypatch):
    monkeypatch.setenv("BASE_URL", "http://host:5003/")
    monkeypatch.setattr(Config, "get_url_version_extension", classmethod(lambda cls, host=None: "v1.2.3"))
    assert Config.base_url() == "http://host:5003/v1.2.3.html"


def test_safety_switches_default_off(monkeypatch):
    for name in ("ALLOW_HW_ACTIONS", "STRICT_HARDWARE", "MOCK_SERVER"):
        monkeypatch.delenv(name, raising=False)
    assert not Config.allow_hw_actions()
    assert not Config.strict_hardware()
    assert not Config.is_mock_mode()
