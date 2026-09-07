"""
Pytest configuration and Playwright fixtures for GRL USB PD C2 UI Automation.
"""
import time
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from Scripts.Helpers.config import Config
from Scripts.Helpers.logger import logger
from Scripts.Helpers.api_client import C2ApiClient, c2_api

REPORTS_DIR = Path(__file__).resolve().parent.parent / "Reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

@pytest.fixture(scope="session")
def api_client() -> C2ApiClient:
    """Fixture providing C2ApiClient instance for REST API interactions."""
    return c2_api


@pytest.fixture(scope="session")
def browser_instance():
    headless = Config.is_headless()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-web-security", "--allow-running-insecure-content"]
        )
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser_instance: Browser, request) -> Page:
    context: BrowserContext = browser_instance.new_context(
        viewport={"width": 1440, "height": 900},
        ignore_https_errors=True
    )
    # Start tracing for failure debugging
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()

    base_url = Config.base_url()
    logger.info(f"Target Base URL resolved to: {base_url}")
    try:
        page.goto(base_url, wait_until="load", timeout=25000)
    except Exception as e:
        logger.warning(f"Initial page load warning: {e}")

    yield page

    # Post-test failure capture
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        test_name = request.node.name
        ts = int(time.time())
        screenshot_path = REPORTS_DIR / f"fail_{test_name}_{ts}.png"
        trace_path = REPORTS_DIR / f"trace_{test_name}_{ts}.zip"

        try:
            page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"Captured failure screenshot: {screenshot_path}")
        except Exception:
            pass

        try:
            context.tracing.stop(path=str(trace_path))
            logger.info(f"Saved Playwright trace: {trace_path}")
        except Exception:
            pass
    else:
        try:
            context.tracing.stop()
        except Exception:
            pass

    context.close()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
