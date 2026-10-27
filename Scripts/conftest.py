"""
Pytest configuration and Playwright fixtures for GRL USB PD C2 UI Automation.

Run-mode switches (env var or CLI option):
  MOCK_SERVER=true       / --mock              API tests against the offline mock; UI tests are skipped.
  ALLOW_HW_ACTIONS=true  / --allow-hw-actions  enable tests marked `hardware` (change tester state).
  STRICT_HARDWARE=true   / --strict-hardware   `requires_tester` tests fail instead of skip when offline.
"""
from __future__ import annotations

import os
import platform
import re
import time

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright
import pytest

from Scripts.Helpers import reporting, run_lock
from Scripts.Helpers.api_client import C2ApiClient
from Scripts.Helpers.config import Config
from Scripts.Helpers.Locators import AppLocators, ConnectionLocators
from Scripts.Helpers.logger import logger
from Scripts.Helpers.mock_server import start_mock_service, stop_mock_service
from Scripts.Helpers.popups import PopupGuard
from Scripts.Pages.app_page import AppPage

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
    reporting.register(config)
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
    _acquire_run_lock(config, items)


def _acquire_run_lock(config, items) -> None:
    """One run at a time may use the tester. API-only, mock and collect-only runs don't need the lock."""
    if (hasattr(config, "workerinput") or config.option.collectonly or Config.is_mock_mode()
            or os.environ.get("C2_RUN_LOCK", "true").lower() in ("0", "false", "no")):
        return
    uses_tester = any(i.get_closest_marker(m) for i in items for m in ("ui", "hardware", "requires_tester"))
    if not uses_tester:
        return
    try:
        run_lock.acquire(command=" ".join(config.invocation_params.args) or "pytest")
    except run_lock.RunLockedError as e:
        pytest.exit(str(e), returncode=5)
    config._c2_run_lock = True


def pytest_unconfigure(config):
    if getattr(config, "_c2_run_lock", False):
        run_lock.release()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


# ----------------------------------------------------------------------------
# Backend
# ----------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def c2_backend(request) -> C2ApiClient:
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
    uses_tester = any(i.get_closest_marker(m) for i in request.session.items
                      for m in ("ui", "hardware", "requires_tester"))
    reporting.set_environment(_run_environment(client, version, started_mock, check_tester=uses_tester))
    yield client

    if started_mock:
        stop_mock_service()


def _tester_link_health(client: C2ApiClient, samples: int, interval_s: float = 1.0) -> str:
    """Samples the tester status a few times; a flapping link makes hardware results unreliable."""
    connected = 0
    for i in range(samples):
        connected += client.is_tester_connected()
        if i < samples - 1:
            time.sleep(interval_s)
    if connected == samples:
        return f"stable ({connected}/{samples} connected)"
    if connected == 0:
        return f"not connected (0/{samples})"
    logger.warning(f"Tester link is UNSTABLE: connected in {connected}/{samples} samples - "
                   f"tester-dependent results may be unreliable")
    return f"UNSTABLE ({connected}/{samples} connected)"


def _run_environment(client: C2ApiClient, version: str, mock: bool, check_tester: bool = True) -> dict[str, str]:
    env = {
        "Started": time.strftime("%Y-%m-%d %H:%M:%S"),
        "Host PC": platform.node(),
        "Python / Playwright": f"{platform.python_version()} / {_playwright_version()}",
        "C2 backend": client.base_url + (" (MOCK)" if mock else ""),
        "GRL software": version,
        "Hardware actions": "allowed" if Config.allow_hw_actions() else "blocked (read-only run)",
        "Browser": Config.browser() + (" (headless)" if Config.is_headless() else ""),
        "Test code": _git_revision(),
    }
    if mock:
        return env
    # GET /api/ConnectionSetup queries the tester live (~5 s on a slow link, longer while it reconnects):
    # bounded timeout, no retries, so the check can't stall the run.
    fast = C2ApiClient(base_url=client.base_url, timeout=8.0, retries=0)
    try:
        info = fast.get_connection_info()
        env.update({
            "Tester status": info.get("testerStatus", ""),
            "Tester IP": info.get("testerIpAddress", ""),
            "Tester serial": info.get("serialNumber", ""),
            "Firmware": info.get("firmwareVersion", ""),
            "Calibration": info.get("boardCalibration", ""),
            "Calibration due": (info.get("calibration_Sp_Date") or "")[:10],
        })
    except Exception as e:
        logger.warning(f"Could not read tester details: {e}")
    samples = Config.get_int("HEALTH_SAMPLES", 3)
    if samples > 0 and check_tester:
        env["Tester link"] = _tester_link_health(fast, samples)
    return env


def _git_revision() -> str:
    """'<branch>@<short sha>' plus ' +local changes' when the working tree is dirty."""
    import subprocess

    def git(*args: str) -> str:
        res = subprocess.run(["git", *args], capture_output=True, text=True, check=False,
                             cwd=os.path.dirname(__file__))
        return res.stdout.strip() if res.returncode == 0 else ""

    sha = git("rev-parse", "--short", "HEAD")
    if not sha:
        return "unknown (not a git checkout)"
    dirty = " +local changes" if git("status", "--porcelain", "--untracked-files=no") else ""
    return f"{git('rev-parse', '--abbrev-ref', 'HEAD')}@{sha}{dirty}"


def _playwright_version() -> str:
    try:
        from importlib.metadata import version as pkg_version
        return pkg_version("playwright")
    except Exception:
        return "?"


@pytest.fixture(scope="session")
def api_client(c2_backend: C2ApiClient) -> C2ApiClient:
    return c2_backend


_OFFLINE_GRACE_S = 120.0
_tester_offline_since = 0.0


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
    global _tester_offline_since
    if not request.node.get_closest_marker("requires_tester"):
        return
    wait_s = Config.get_int("TESTER_WAIT_S", 30)
    # After a failed wait, don't make every following test wait again: re-check once without waiting.
    recently_offline = _tester_offline_since and time.monotonic() - _tester_offline_since < _OFFLINE_GRACE_S
    connected = api_client.is_tester_connected() if recently_offline else _wait_for_tester(api_client, wait_s)
    if connected:
        _tester_offline_since = 0.0
    elif not recently_offline:
        _tester_offline_since = time.monotonic()  # a full wait just failed: start a new grace period
    if not connected:
        waited = (f"offline for {time.monotonic() - _tester_offline_since:.0f}s, not waiting again"
                  if recently_offline else f"waited {wait_s}s")
        msg = f"No tester connected ({waited}; GET /api/ConnectionSetup testerStatus != Connected)"
        if Config.strict_hardware():
            pytest.fail(msg)
        pytest.skip(msg)


# ----------------------------------------------------------------------------
# Browser - one window for the whole run
# ----------------------------------------------------------------------------

class BrowserSession:
    """
    A single browser, context and page shared by every UI test in the run, so the window
    is not closed and reopened per test. Each test starts from a reset page (popups closed,
    menus closed, app reloaded only if it is not healthy) and records its own trace chunk.
    """

    def __init__(self, browser: Browser):
        self.context: BrowserContext = browser.new_context(viewport={"width": 1440, "height": 900},
                                                           accept_downloads=True)
        self.context.set_default_timeout(Config.ui_timeout_ms())
        self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self.console_errors: list[str] = []
        self.page: Page | None = None
        self.guard: PopupGuard | None = None
        self._open_page()

    def _open_page(self) -> None:
        pg = self.context.new_page()
        pg.on("console", lambda m: self.console_errors.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: self.console_errors.append(f"pageerror: {e}"))
        pg.on("dialog", lambda d: (logger.warning(f"Native dialog dismissed: {d.message}"), d.dismiss()))
        self.guard = PopupGuard(pg).install()
        pg._c2_popup_guard = self.guard  # type: ignore[attr-defined]
        self.page = pg
        AppPage(pg).load()
        self.guard.dismiss_informational()

    def _healthy(self) -> bool:
        pg = self.page
        if pg is None or pg.is_closed():
            return False
        try:
            return bool(re.search(r"/v[\d.]+\.html", pg.url)) and pg.locator("#left-toggle-group").is_visible()
        except Exception:
            return False

    def reset_for_test(self) -> Page:
        if self.page is None or self.page.is_closed():
            logger.warning("Browser page was closed; opening a new one")
            self._open_page()
        pg = self.page
        self.guard.dismiss_informational()
        cancel = pg.locator(AppLocators.POPUP_CANCEL)
        if cancel.count() and cancel.first.is_visible():  # a confirmation left open by a failed test
            cancel.first.click()
        pg.keyboard.press("Escape")  # close any open dropdown menu
        if not self._healthy():
            logger.warning("App not in a usable state; reloading it")
            AppPage(pg).load()
            self.guard.dismiss_informational()
        return pg

    def sync_tester_state(self) -> None:
        """
        The page is shared, so it may still show a tester state from before a reconnect. Tests that
        need the tester (the backend already reports it connected) get a reloaded app if the UI lags.
        """
        status = self.page.locator(ConnectionLocators.TESTER_INFO_ROWS).first.locator("td")
        if status.count() and status.inner_text().strip() != "Connected":
            logger.info(f"UI shows tester '{status.inner_text().strip()}' but backend is connected; reloading app")
            AppPage(self.page).load()
            self.guard.dismiss_informational()

    def close(self) -> None:
        try:
            self.context.tracing.stop()
        except Exception:
            pass
        self.context.close()


@pytest.fixture(scope="session")
def browser_instance():
    """BROWSER = chromium (bundled, default) | msedge | chrome | firefox."""
    name = Config.browser()
    with sync_playwright() as p:
        if name == "firefox":
            browser = p.firefox.launch(headless=Config.is_headless())
        else:
            channel = name if name in ("msedge", "chrome") else None
            browser = p.chromium.launch(headless=Config.is_headless(), channel=channel)
        logger.info(f"Browser: {name} {browser.version}")
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def browser_session(browser_instance: Browser) -> BrowserSession:
    session = BrowserSession(browser_instance)
    yield session
    session.close()


@pytest.fixture
def popup_guard(page: Page) -> PopupGuard:
    return page._c2_popup_guard  # type: ignore[attr-defined]


@pytest.fixture
def page(browser_session: BrowserSession, request) -> Page:
    pg = browser_session.reset_for_test()
    if request.node.get_closest_marker("requires_tester"):
        browser_session.sync_tester_state()
    guard = browser_session.guard
    guard.start_test()
    popups_before = len(guard.seen)
    errors_before = len(browser_session.console_errors)
    browser_session.context.tracing.start_chunk(title=request.node.nodeid)

    yield pg

    for rec in guard.seen[popups_before:]:
        request.node.user_properties.append(("app_popup", f"{rec.title}: {rec.message}"))
    console_errors = browser_session.console_errors[errors_before:]
    if console_errors:
        logger.info(f"{len(console_errors)} browser console error(s) during {request.node.name}")

    failed = any(getattr(request.node, f"rep_{w}", None) and getattr(request.node, f"rep_{w}").failed
                 for w in ("setup", "call"))
    if failed:
        _log_backend_state(request)
        _save_failure_artifacts(pg, browser_session.context, request.node, console_errors)
    else:
        try:
            browser_session.context.tracing.stop_chunk()
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


def _save_failure_artifacts(pg: Page, ctx: BrowserContext, node, console_errors: list[str]) -> None:
    folder = reporting.panel_dir(node.path)
    safe = reporting.safe_name(node.name)
    shot = folder / f"fail_{safe}.png"
    trace = folder / f"trace_{safe}.zip"
    try:
        pg.screenshot(path=str(shot), full_page=False)
        node.user_properties.append(("screenshot", str(shot)))
        logger.info(f"Failure screenshot: {shot}")
        if allure:
            allure.attach.file(str(shot), name="failure screenshot", attachment_type=allure.attachment_type.PNG)
    except Exception as e:
        logger.warning(f"Could not capture screenshot: {e}")
    try:
        ctx.tracing.stop_chunk(path=str(trace))
        node.user_properties.append(("trace", str(trace)))
        logger.info(f"Playwright trace: {trace} (open with: playwright show-trace {trace})")
        if allure:
            allure.attach.file(str(trace), name="playwright trace", extension="zip")
    except Exception as e:
        logger.warning(f"Could not save trace: {e}")
    if console_errors and allure:
        allure.attach("\n".join(console_errors), name="browser console errors",
                      attachment_type=allure.attachment_type.TEXT)
