"""
Test cases for Panel 5: Report.
"""
import pytest
from playwright.sync_api import Page
from Scripts.Pages.report_page import ReportPage


@pytest.mark.report
@pytest.mark.regression
class TestReportPanel:
    def test_TC_01_verify_report_panel_navigation(self, page: Page):
        report_page = ReportPage(page)
        report_page.open_panel()

    def test_TC_02_verify_view_report_button(self, page: Page):
        report_page = ReportPage(page)
        report_page.open_panel()
        report_page.view_report()

    def test_TC_03_verify_download_html_report_trigger(self, page: Page):
        report_page = ReportPage(page)
        report_page.open_panel()
        report_page.download_html_report()

    def test_TC_04_verify_download_dut_data_trigger(self, page: Page):
        report_page = ReportPage(page)
        report_page.open_panel()
        report_page.download_dut_data()
