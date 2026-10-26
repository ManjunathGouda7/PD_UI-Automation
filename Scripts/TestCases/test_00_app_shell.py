"""
Application shell: load, header, left navigation.
Spec: Connection Setup #1, #2; General #9.
"""
from playwright.sync_api import Page
import pytest

from Scripts.Data.test_data_manager import test_data_manager
from Scripts.Helpers.api_client import C2ApiClient
from Scripts.Pages.app_page import AppPage
from Scripts.Pages.configure_page import ConfigurePage
from Scripts.Pages.connection_page import ConnectionPage
from Scripts.Pages.help_page import HelpPage
from Scripts.Pages.loopback_page import LoopBackPage
from Scripts.Pages.product_capability_page import ProductCapabilityPage
from Scripts.Pages.report_page import ReportPage
from Scripts.Pages.results_page import ResultsPage
from Scripts.Pages.test_config_page import TestConfigPage

APP = test_data_manager.section("app")
PANEL_PAGES = [ConnectionPage, ProductCapabilityPage, TestConfigPage, ResultsPage,
               ReportPage, ConfigurePage, LoopBackPage, HelpPage]


@pytest.mark.smoke
@pytest.mark.shell
class TestAppShell:
    @pytest.mark.spec("CONN-01")
    def test_TC_01_title_shows_software_name_version_and_model(self, app: AppPage, api_client: C2ApiClient):
        assert app.page.title() == APP["model_name"]
        assert app.primary_title().startswith(APP["title_prefix"]), app.primary_title()
        assert app.model_name() == APP["model_name"]
        assert app.header_version() == api_client.get_software_version(), \
            "Header version differs from GET /api/App/GetSoftwareVersion"

    @pytest.mark.spec("CONN-02")
    def test_TC_02_left_navigation_lists_all_panels(self, app: AppPage):
        assert app.nav_panel_names() == APP["panels"]

    def test_TC_03_connection_setup_is_default_panel(self, app: AppPage):
        app.load()  # the browser page is shared across tests; check the state of a fresh load
        assert app.active_panel_name() == "Connection Setup"
        assert ConnectionPage(app.page).is_active()

    def test_TC_04_url_uses_backend_version_extension(self, page: Page, api_client: C2ApiClient):
        assert page.url.endswith(f"/{api_client.get_url_version_extension()}.html"), page.url

    @pytest.mark.spec("GEN-09", "GEN-10")
    @pytest.mark.parametrize("page_cls", PANEL_PAGES, ids=[p.PANEL_NAME for p in PANEL_PAGES])
    def test_TC_05_each_panel_becomes_active_and_version_stays_visible(self, app: AppPage, page_cls, api_client):
        panel = page_cls(app.page).open()
        assert panel.is_active()
        assert app.active_panel_name() == page_cls.PANEL_NAME
        others = [p for p in PANEL_PAGES if p is not page_cls]
        assert not any(o(app.page).is_active() for o in others), "More than one panel marked active"
        assert app.header_version() == api_client.get_software_version()
