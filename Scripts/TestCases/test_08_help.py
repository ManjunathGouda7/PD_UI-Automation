"""
Panel 8: Help.
Spec: Help & Diagnostics.
"""
from playwright.sync_api import Page
import pytest

from Scripts.Data.test_data_manager import test_data_manager
from Scripts.Helpers.api_client import C2ApiClient
from Scripts.Pages.help_page import HelpPage

HELP = test_data_manager.section("help")


@pytest.fixture
def help_page(page: Page) -> HelpPage:
    return HelpPage(page).open()


@pytest.mark.help
class TestHelpPanel:
    @pytest.mark.smoke
    def test_TC_01_product_and_version(self, help_page: HelpPage, api_client: C2ApiClient):
        assert help_page.product_name() == test_data_manager.section("app")["model_name"]
        assert help_page.app_version() == api_client.get_software_version()

    @pytest.mark.spec("HELP-01", "HELP-02")
    def test_TC_02_support_links(self, help_page: HelpPage):
        desk = help_page.link("Support Desk")
        assert desk["href"] == HELP["support_desk_url"]
        assert desk["target"] == "_blank"
        assert help_page.link("Email Support")["href"].startswith(f"mailto:{HELP['support_email']}")

    @pytest.mark.spec("HELP-04")
    def test_TC_03_api_document_is_served(self, help_page: HelpPage, api_client: C2ApiClient):
        href = help_page.link("API Document")["href"]
        assert href == HELP["api_doc_path"]
        res = api_client.session.get(api_client._url(href), timeout=10)
        assert res.status_code == 200, f"{href} -> HTTP {res.status_code}"

    @pytest.mark.spec("HELP-03")
    @pytest.mark.smoke
    def test_TC_04_debug_log_download(self, help_page: HelpPage):
        path = help_page.download_debug_logs()
        assert path.exists() and path.stat().st_size > 0, f"Empty debug log: {path}"
