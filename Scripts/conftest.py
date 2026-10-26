"""
Pytest configuration and Playwright fixtures for GRL USB PD C2 UI Automation.

Run-mode switches (env var or CLI option):
  MOCK_SERVER=true       / --mock              API tests against the offline mock; UI tests are skipped.
  ALLOW_HW_ACTIONS=true  / --allow-hw-actions  enable tests marked `hardware` (change tester state).
  STRICT_HARDWARE=true   / --strict-hardware   `requires_tester` tests fail instead of skip when offline.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import time

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright
import pytest

from Scripts.Helpers.api_client import C2ApiClient
from Scripts.Helpers.config import Config
from Scripts.Helpers.logger import logger
from Scripts.Helpers.mock_server import start_mock_service, stop_mock_service
from Scripts.Helpers.popups import PopupGuard
from Scripts.Pages.app_page import AppPage

REPORTS_DIR = Path(__file__).resolve().parent.parent / "Reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

try:  # optional
    import allure
except ImportError:  # pragma: no cover
    allure = None


# ----------------------------------------------------------------------------
# Options & collection
# ----------------------------------------------------------------------------

def pytest_addoption(parser):
    group = parser.getgroup("c2", "GRL C2 automation")
    group.addoption("--mock", action="store_true", help="Run API tests against the offline mock server.")
    group.addoption("--allow-hw-actions", action="store_true", help="Enable tests that change tester state.")
    group.addoption("--strict-hardware", action="store_true",
                    help="Fail (instead of skip) tests that need a connected tester when it is offline.")


def pytest_configure(config):
    if config.getoption("--mock"):
        os.environ["MOCK_SERVER"] = "true"
    if config.getoption("--allow-hw-actions"):
        os.environ["ALLOW_HW_ACTIONS"] = "true"
    if config.getoption("--strict-hardware"):
        os.environ["STRICT_HARDWARE"] = "true"


def pytest_collection_modifyitems(config, items):
    mock = Config.is_mock_mode()
    allow_hw = Config.allow_hw_actions()
    for item in items:
        if "page" in getattr(item, "fixturenames", ()):
            item.add_marker(pytest.mark.ui)
        if mock and item.get_closest_marker("ui"):
            item.add_marker(pytest.mark.skip(reason="UI tests need the real C2 web app (mock serves API only)"))
        if mock and item.get_closest_marker("requires_tester"):
            item.add_marker(pytest.mark.skip(reason="needs a real tester"))
        if item.get_closest_marker("hardware") and not allow_hw:
            item.add_marker(pytest.mark.skip(
                reason="changes tester state; enable with --allow-hw-actions / ALLOW_HW_ACTIONS=true"))


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


# ----------------------------------------------------------------------------
# Backend
# ----------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def c2_backend() -> C2ApiClient:
    """
    Verifies the C2 backend is reachable before any test runs. There is no silent
    fallback: against the real app an offline backend aborts the run; the mock is used
    only when explicitly requested.
    """
    started_mock = False
    if Config.is_mock_mode():
        port = int(Config.dut_port())
        started_mock = start_mock_service(port=port)
        if not started_mock:
            pytest.exit(f"MOCK_SERVER requested but port {port} is busy (is the real C2 app running?)", returncode=4)
        logger.info(f"Mock C2 API server started on port {port}")

    client = C2ApiClient()
    if not client.is_online():
        pytest.exit(f"C2 backend is not reachable at {client.base_url}. Start the GRL software "
                    f"or run with --mock for API-only tests.", returncode=4)

    version = client.get_software_version()
    logger.info(f"C2 backend online at {client.base_url} (software {version}, mock={started_mock})")
    yield client

    if started_mock:
        stop_mock_service()


@pytest.fixture(scope="session")
def api_client(c2_backend: C2ApiClient) -> C2ApiClient:
    return c2_backend


def _wait_for_tester(api_client: C2ApiClient, timeout_s: float) -> bool:
    deadline = time.monotonic() + timeout_s
    while True:
        if api_client.is_tester_connected():
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(2)


@pytest.fixture(autouse=True)
def _requires_tester(request, api_client: C2ApiClient):
    """
    Tests marked `requires_tester` wait up to TESTER_WAIT_S (default 30 s) for a connected
    tester - the link can drop briefly - then skip, or fail with STRICT_HARDWARE.
    """
    if not request.node.get_closest_marker("requires_tester"):
        return
    wait_s = Config.get_int("TESTER_WAIT_S", 30)
    if not _wait_for_tester(api_client, wait_s):
        msg = f"No tester connected within {wait_s}s (GET /api/ConnectionSetup testerStatus != Connected)"
        if Config.strict_hardware():
            pytest.fail(msg)
        pytest.skip(msg)


# ----------------------------------------------------------------------------
# Browser
# ----------------------------------------------------------------------------

@pytest.fixture(scope="session")
def browser_instance():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=Config.is_headless())
        yield browser
        browser.close()


@pytest.fixture
def context(browser_instance: Browser) -> BrowserContext:
    ctx = browser_instance.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
    ctx.set_default_timeout(Config.ui_timeout_ms())
    ctx.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield ctx
    ctx.close()


@pytest.fixture
def popup_guard(page: Page) -> PopupGuard:
    return page._c2_popup_guard  # type: ignore[attr-defined]


@pytest.fixture
def page(context: BrowserContext, request) -> Page:
    pg = context.new_page()
    console_errors: list[str] = []
    pg.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: console_errors.append(f"pageerror: {e}"))
    pg.on("dialog", lambda d: (logger.warning(f"Native dialog dismissed: {d.message}"), d.dismiss()))

    guard = PopupGuard(pg).install()
    pg._c2_popup_guard = guard  # type: ignore[attr-defined]

    AppPage(pg).load()
    guard.dismiss_informational()

    yield pg

    for rec in guard.seen:
        request.node.user_properties.append(("app_popup", f"{rec.title}: {rec.message}"))
    if console_errors:
        logger.info(f"{len(console_errors)} browser console error(s) during {request.node.name}")

    failed = any(getattr(request.node, f"rep_{w}", None) and getattr(request.node, f"rep_{w}").failed
                 for w in ("setup", "call"))
    if failed:
        _log_backend_state(request)
        _save_failure_artifacts(pg, context, request.node.name, console_errors)
    else:
        try:
            context.tracing.stop()
        except Exception:
            pass


@pytest.fixture
def app(page: Page) -> AppPage:
    return AppPage(page)


def _log_backend_state(request) -> None:
    """Records tester/app state at failure time; the shared backend can change underneath a test."""
    try:
        client: C2ApiClient = request.getfixturevalue("api_client")
        state = client.get_app_state()
        active = [h["ipAddress"] for h in client.get_ip_history() if h.get("isActive")]
        note = f"backend at failure: {state}, active tester IP: {active or 'none'}"
        logger.warning(note)
        request.node.user_properties.append(("backend_state", note))
    except Exception as e:
        logger.warning(f"Could not read backend state: {e}")


def _save_failure_artifacts(pg: Page, ctx: BrowserContext, test_name: str, console_errors: list[str]) -> None:
    safe = re.sub(r"[^\w.-]+", "_", test_name)
    ts = int(time.time())
    shot = REPORTS_DIR / f"fail_{safe}_{ts}.png"
    trace = REPORTS_DIR / f"trace_{safe}_{ts}.zip"
    try:
        pg.screenshot(path=str(shot), full_page=False)
        logger.info(f"Failure screenshot: {shot}")
        if allure:
            allure.attach.file(str(shot), name="failure screenshot", attachment_type=allure.attachment_type.PNG)
    except Exception as e:
        logger.warning(f"Could not capture screenshot: {e}")
    try:
        ctx.tracing.stop(path=str(trace))
        logger.info(f"Playwright trace: {trace} (open with: playwright show-trace {trace})")
        if allure:
            allure.attach.file(str(trace), name="playwright trace", extension="zip")
    except Exception as e:
        logger.warning(f"Could not save trace: {e}")
    if console_errors and allure:
        allure.attach("\n".join(console_errors), name="browser console errors",
                      attachment_type=allure.attachment_type.TEXT)
