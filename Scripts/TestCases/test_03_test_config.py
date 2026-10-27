"""
Panel 3: Test Config.
Spec: Test Config & MOI, License & MOI Filtering.
"""
from playwright.sync_api import Page
import pytest

from Scripts.Data.test_data_manager import test_data_manager
from Scripts.Helpers.api_client import C2ApiClient
from Scripts.Pages.test_config_page import TestConfigPage

TC = test_data_manager.section("test_config")


@pytest.fixture
def tc(page: Page) -> TestConfigPage:
    return TestConfigPage(page).open()


@pytest.mark.test_config
class TestConfigurationPanel:
    @pytest.mark.spec("TCM-10", partial=True)
    @pytest.mark.smoke
    def test_TC_01_total_test_count_matches_api(self, tc: TestConfigPage, api_client: C2ApiClient):
        selected, total = tc.selected_count()
        assert total == api_client.count_test_cases(), "UI total differs from GET /api/TestConfiguration/GetTestCaseList"
        assert 0 <= selected <= total

    @pytest.mark.spec("TCM-20", partial=True)
    def test_TC_02_start_execution_disabled_without_selection(self, tc: TestConfigPage):
        selected, _ = tc.selected_count()
        if selected:
            pytest.skip(f"{selected} tests already selected in this session")
        assert not tc.start_execution_enabled()

    def test_TC_03_certification_filter_options_and_api(self, tc: TestConfigPage, api_client: C2ApiClient):
        assert tc.certification_options() == TC["certifications"]
        assert tc.certification() == api_client.get_certification_filter()

    @pytest.mark.spec("TCM-03", partial=True)
    def test_TC_04_search_field_accepts_and_clears_text(self, tc: TestConfigPage):
        tc.search("PHY")
        tc.clear_search()

    def test_TC_05_report_inputs_reflect_backend(self, tc: TestConfigPage, api_client: C2ApiClient):
        ui = tc.report_inputs()
        api = api_client.get_report_inputs()
        assert set(ui) <= set(api), f"Unknown report input keys: {set(ui) - set(api)}"
        assert ui == {k: api[k] for k in ui}

    def test_TC_06_report_input_is_editable(self, tc: TestConfigPage):
        original = tc.report_inputs()["testEngineer"]
        try:
            tc.set_report_input("testEngineer", "GRL Automation")
            assert tc.report_inputs()["testEngineer"] == "GRL Automation"
        finally:
            tc.set_report_input("testEngineer", original)

    @pytest.mark.spec("TCM-11", partial=True)
    def test_TC_07_rerun_count_only_editable_when_rerun_enabled(self, tc: TestConfigPage):
        assert tc.rerun_count_editable() == tc.rerun_enabled()

    @pytest.mark.spec("TCM-01")
    @pytest.mark.requires_tester
    def test_TC_08_test_tree_lists_api_suites(self, tc: TestConfigPage, api_client: C2ApiClient):
        """Every suite returned by GetTestCaseList is shown in the tree (UI adds a version suffix)."""
        ui_suites = tc.tree_suite_titles()
        api_suites = [suite["title"] for root in api_client.get_test_case_list() for suite in root["children"]]
        assert ui_suites, "Test selection tree shows no suites"
        missing = [s for s in api_suites if not any(u.startswith(s) for u in ui_suites)]
        assert not missing, f"Suites from the API missing in the UI tree: {missing} (UI shows {ui_suites})"


@pytest.mark.test_config
@pytest.mark.requires_tester
class TestConfigurationTree:
    """Test selection tree interactions. All client-side; every test restores the tree."""

    SUITE = "Power Delivery 3.2 Tests"

    @pytest.mark.spec("TCM-08")
    def test_TC_09_expand_test_list_expands_and_collapses_all_nodes(self, tc: TestConfigPage):
        collapsed = tc.wait_for_tree_count(lambda n: n > 0)
        try:
            tc.set_expand_test_list(True)
            expanded = tc.wait_for_tree_count(lambda n: n > collapsed)
            assert expanded > collapsed, f"Expand Test List did not expand the tree ({collapsed} nodes)"
        finally:
            tc.set_expand_test_list(False)
        assert tc.wait_for_tree_count(lambda n: n == collapsed) == collapsed

    @pytest.mark.spec("TCM-09", "TCM-10")
    def test_TC_10_selecting_a_suite_updates_selected_counter(self, tc: TestConfigPage, api_client: C2ApiClient):
        before, total = tc.selected_count()
        suite_size = next(_leaf_count(s) for root in api_client.get_test_case_list()
                          for s in root["children"] if s["title"] == self.SUITE)
        try:
            tc.set_suite_selected(self.SUITE, True)
            assert tc.selected_count() == (before + suite_size, total)
        finally:
            tc.set_suite_selected(self.SUITE, False)
        assert tc.selected_count() == (before, total)

    @pytest.mark.spec("TCM-20", partial=True)
    def test_TC_11_start_execution_enabled_once_tests_selected(self, tc: TestConfigPage):
        if tc.selected_count()[0]:
            pytest.skip("Tests already selected")
        try:
            tc.set_suite_selected(self.SUITE, True)
            assert tc.start_execution_enabled(), "Start Execution stays disabled with tests selected"
        finally:
            tc.set_suite_selected(self.SUITE, False)
        assert not tc.start_execution_enabled()

    @pytest.mark.spec("TCM-03")
    @pytest.mark.parametrize("query", ["Eye Diagram", "TEST.PD.PHY.ALL.2"], ids=["by-name", "by-id"])
    def test_TC_12_search_filters_tree_by_name_and_id(self, tc: TestConfigPage, query: str):
        try:
            tc.search(query)
            tc.wait_for_tree_count(lambda n: n < 10)
            titles = tc.visible_tree_titles()
            assert titles and query.lower() in titles[-1].lower(), f"Search {query!r} shows {titles}"
            assert len(titles) < 10, f"Search {query!r} did not narrow the tree: {len(titles)} nodes"
        finally:
            tc.clear_search()
        assert len(tc.tree_suite_titles()) >= 4

    @pytest.mark.spec("TCM-07", partial=True)
    def test_TC_13_result_filters_toggle_and_clear(self, tc: TestConfigPage):
        baseline = tc.filter_classes()
        try:
            for name in baseline:
                tc.click_filter(name)
                assert tc.filter_classes()[name] != baseline[name], f"{name} filter shows no active state"
        finally:
            tc.clear_filters()
        assert tc.filter_classes() == baseline


def _leaf_count(node) -> int:
    children = node.get("children") or []
    return 1 if not children else sum(_leaf_count(c) for c in children)
