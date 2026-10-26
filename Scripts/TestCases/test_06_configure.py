"""
Panel 6: Configure.
Spec: Configure & E-Load.
"""
from playwright.sync_api import Page
import pytest

from Scripts.Data.test_data_manager import test_data_manager
from Scripts.Helpers.api_client import C2ApiClient
from Scripts.Helpers.Locators import ConfigureLocators
from Scripts.Pages.configure_page import ConfigurePage

CFG = test_data_manager.section("configure")


@pytest.fixture
def cfg(page: Page) -> ConfigurePage:
    return ConfigurePage(page).open()


@pytest.mark.configure
class TestConfigurePanel:
    @pytest.mark.spec("CFG-01", partial=True)
    @pytest.mark.smoke
    def test_TC_01_controller_mode_options(self, cfg: ConfigurePage):
        assert cfg.options("Controller Mode") == CFG["controller_modes"]
        assert cfg.settings()["Controller Mode"] in CFG["controller_modes"]

    @pytest.mark.spec("CFG-02", partial=True)
    def test_TC_02_all_controller_settings_have_values(self, cfg: ConfigurePage):
        settings = cfg.settings()
        assert all(settings.values()), settings

    @pytest.mark.spec("CFG-03", partial=True)
    def test_TC_03_channel_checkbox_toggles_and_restores(self, cfg: ConfigurePage):
        """Channel selection is client-side until Apply, so toggling is safe."""
        before = cfg.channel_states()
        for channel, state in before.items():
            cfg.set_channel(channel, not state)
            assert cfg.channel_states()[channel] is (not state)
            cfg.set_channel(channel, state)
        assert cfg.channel_states() == before

    @pytest.mark.spec("CFG-04", partial=True)
    def test_TC_04_sampling_ratio_is_positive_integer(self, cfg: ConfigurePage):
        ratio = cfg.sampling_ratio()
        assert ratio.isdigit() and int(ratio) > 0, ratio

    @pytest.mark.spec("CFG-06", partial=True)
    def test_TC_05_stop_capture_disabled_when_not_capturing(self, cfg: ConfigurePage, api_client: C2ApiClient):
        if api_client.get_capture_status():
            pytest.skip("A capture is running")
        assert not cfg.button_enabled(ConfigureLocators.STOP_CAPTURE_BTN)
        assert cfg.button_enabled(ConfigureLocators.START_CAPTURE_BTN)

    @pytest.mark.spec("CFG-03", partial=True)
    @pytest.mark.hardware
    @pytest.mark.requires_tester
    def test_TC_06_apply_configuration(self, cfg: ConfigurePage):
        cfg.apply()
        assert cfg.is_active()
