"""
Panel 5: Report.
Spec: Report Generation.
"""
from playwright.sync_api import Page
import pytest

from Scripts.Helpers.api_client import C2ApiClient
from Scripts.Pages.report_page import ReportPage


@pytest.fixture
def report(page: Page) -> ReportPage:
    return ReportPage(page).open()


@pytest.mark.report
class TestReportPanel:
    @pytest.mark.smoke
    def test_TC_01_toolbar_buttons_present(self, report: ReportPage):
        labels = report.button_labels()
        assert labels == {name: name for name in ReportPage.BUTTONS}

    @pytest.mark.spec("RPT-15", partial=True)
    def test_TC_02_report_location_is_shown(self, report: ReportPage):
        location = report.report_location()
        assert location and "Report" in location, location

    @pytest.mark.spec("RPT-02", partial=True)
    def test_TC_03_download_html_report_prompts_for_file_name(self, report: ReportPage):
        prompt = report.open_download_html_prompt()
        try:
            assert prompt["title"] == "Download File"
            assert prompt["file_name"].lower().endswith(".html"), prompt
            assert prompt["buttons"] == "Ok,Cancel"
        finally:
            report.cancel_popup()

    def test_TC_04_report_inputs_api_contract(self, api_client: C2ApiClient):
        expected = {"manufacturer", "modelNumber", "remarks", "savePath", "serialNumber",
                    "testEngineer", "testLab", "reportFolderPath"}
        assert expected <= set(api_client.get_report_inputs())
