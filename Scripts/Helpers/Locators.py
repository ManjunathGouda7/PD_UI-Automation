"""
Centralized locators for the GRL-V-DPWR-EPR (USB PD C2) web application.

Verified against the live DOM of software version 1.1.1.4 (page /v1.1.4.html).
Rules:
  * Prefer the application's own element ids; fall back to stable class names.
  * One element per locator - no comma-joined "maybe" alternatives, which hide breakage.
  * Ids that look misspelled (e.g. "...CC2heckBox", "...ClearFiltertn") are spelled
    that way in the product; do not "fix" them here.

Layout note: the app is a single scrolling page. All panels are always mounted, each
inside a wrapper div that carries `.scroll-content-sticky` when it is the active panel
and `.scroll-content-disabled` otherwise. Panel wrappers appear in the same order as
the left navigation (plus a hidden Admin panel at the end).
"""


class AppLocators:
    ROOT = "#root"
    PRIMARY_TITLE = ".navbar-primaryText"
    SECONDARY_TITLE = ".navbar-secondaryText"
    HAMBURGER = ".hamburger-parent"
    PANEL_WRAPPER = ":is(.scroll-content-sticky, .scroll-content-disabled)"
    ACTIVE_PANEL_WRAPPER = ".scroll-content-sticky"

    # Application popups (custom React modal, not native dialogs)
    POPUP = ".modal-backdrop .custom-scroll-popup"
    POPUP_TITLE = ".modal-backdrop .custom-scroll-popup .popup-title"
    POPUP_MESSAGE = ".modal-backdrop .custom-scroll-popup .displayMessage"
    POPUP_INPUT = ".modal-backdrop .custom-scroll-popup input.modal-textField-align"
    POPUP_BUTTONS = ".modal-backdrop .custom-scroll-popup button"
    POPUP_OK = ".modal-backdrop .popupButton_Ok"
    POPUP_CANCEL = ".modal-backdrop .popupButton_Cancel"


class NavigationLocators:
    NAV_GROUP = "#left-toggle-group"
    NAV_LABEL = "#left-toggle-group label.leftNavItems"
    ACTIVE_NAV_LABEL = "#left-toggle-group label.leftNavItems.active"

    # Panel names exactly as shown in the left navigation, in DOM order.
    PANELS = [
        "Connection Setup",
        "Product Capability",
        "Test Config",
        "Results",
        "Report",
        "Configure",
        "LoopBack",
        "Help",
    ]


class ConnectionLocators:
    SCAN_NETWORK_BTN = "#csScanNetworkBtn"
    CONNECT_BTN = "#csConnectBtn"
    UPDATE_FW_BTN = "#csUpdateSystemFirmwareBtn"
    IP_COMBOBOX = ".ip-address-textbox.rc-select"
    IP_INPUT = ".ip-address-textbox .rc-select-search__field"
    TESTER_INFO_TABLE = "table.device-details-margin"
    TESTER_INFO_ROWS = "table.device-details-margin tr"
    LICENSE_HEADER = ".license-info-header"
    LICENSE_ROWS = ".scroll-license-info table tbody tr"


class ProductCapLocators:
    PROJECT_NAME_INPUT = "#pcNewProjectNameInputField"
    PROJECT_SAVE_BTN = "#pcNewProjectNameSaveBtn"
    LOAD_VIF_BTN = "#pcLoadXmlVifFileBtn"
    VIF_GENERATOR_LINK = "a.xml-tool"
    DUT_TYPE_DROPDOWN = "#pcPort1DutTypeComboBox"
    CABLE_DROPDOWN = "#pcPort1CableSelectionComboBox"
    READ_DEVICE_BTN = "#pcPort1GetDeviceDataBtn"
    CLEAR_BTN = "#pcPort1ClearDeviceDataBtn"


class TestConfigLocators:
    __test__ = False

    FILTER_PASS_BTN = "#tcFilterSelectionPassBtn"
    FILTER_FAIL_BTN = "#tcFilterSelectionFailBtn"
    FILTER_INCOMPLETE_BTN = "#tcFilterSelectionIncompleteBtn"
    FILTER_WARNING_BTN = "#tcFilterSelectionWarningBtn"
    FILTER_CLEAR_BTN = "#tcFilterSelectionClearFiltertn"
    START_EXECUTION_BTN = "#tcStartAndStopExecutionBtn"
    CERTIFICATION_DROPDOWN = "#tcCertificationComboBox"
    SEARCH_INPUT = "#tcSearchTestCaseInputField"
    EXPAND_TEST_LIST = "#tcExpandTestListCheckBox"
    SELECTED_COUNT = ".selected-test-count-div strong"
    RERUN_SELECTED_CHECKBOX = "#tcRunSelectedTestsCheckBox"
    RERUN_COUNT_INPUT = "#tcRunSelectedTestInputField"
    # rc-tree inside the Test Config panel. (#test-selection-tree is the Results panel's tree.)
    TEST_TREE = ".test-selection-treeview-container ul.rc-tree"
    TREE_SUITE_NODE = ".test-selection-treeview-container ul.rc-tree > li"
    TREE_NODE = ".test-selection-treeview-container ul.rc-tree li"
    TREE_NODE_LABEL = ".rc-tree-title"

    # Report Generation inputs (DUT / Test information)
    MANUFACTURER_INPUT = "#tcReportManufacturerInputField"
    MODEL_NUMBER_INPUT = "#tcReportModelNumberInputField"
    SERIAL_NUMBER_INPUT = "#tcReportSerialNumberInputField"
    TEST_LAB_INPUT = "#tcReportTestLabInputField"
    TEST_ENGINEER_INPUT = "#tcReportTestEngineerInputField"
    REMARKS_INPUT = "#tcReportRemarksInputField"
    REPORT_FOLDER_PATH_INPUT = "#tcReportFolderPathInputField"

    REPORT_INPUTS = {
        "manufacturer": MANUFACTURER_INPUT,
        "modelNumber": MODEL_NUMBER_INPUT,
        "serialNumber": SERIAL_NUMBER_INPUT,
        "testLab": TEST_LAB_INPUT,
        "testEngineer": TEST_ENGINEER_INPUT,
        "remarks": REMARKS_INPUT,
        "reportFolderPath": REPORT_FOLDER_PATH_INPUT,
    }


class ResultsLocators:
    # Scoped to the Results panel by the page object; these are relative selectors.
    PANEL_HEADING = "p.panelHeading:has-text('Test Results')"
    START_EXECUTION_BTN = "#tcStartAndStopExecutionBtn"
    TEST_STATUS = ".status-notify .test-status"
    SUMMARY_COUNTS = ".results-notify .test-results-notify-count"  # pass, fail, incomplete, warning
    PLOT_CONTAINER = "#plot-container"

    LOAD_BTN = "#chart_toolbar_load_button"
    H_ZOOM_IN_BTN = "#chart_toolbar_horizontal_zoom_in_button"
    H_ZOOM_OUT_BTN = "#chart_toolbar_horizontal_zoom_out_button"
    V_ZOOM_IN_BTN = "#chart_toolbar_vertical_zoom_in"
    V_ZOOM_OUT_BTN = "#chart_toolbar_vertical_zoom_out"
    FIT_BTN = "#chart_toolbar_fit_button"
    PAN_BTN = "#chart_toolbar_click_pan_button"
    PAN_LEFT_BTN = "#chart_toolbar_pan_left_button"
    PAN_RIGHT_BTN = "#chart_toolbar_pan_right_button"
    PAN_TOP_BTN = "#chart_toolbar_pan_top_button"
    PAN_BOTTOM_BTN = "#chart_toolbar_pan_bottom_button"
    MERGE_BTN = "#chart_toolbar_merge_button"
    UNMERGE_BTN = "#chart_toolbar_unmerge_button"
    MARKER_BTN = "#chart_toolbar_set_marker_button"
    SCREENSHOT_BTN = "#btn_screenshot"
    CHANNELS_DROPDOWN = ".channels-dropdown-toggle"
    LIVE_UPDATES_BTN = "#chart_toolbar_live_updates_button"

    TOOLBAR_BUTTONS = [
        LOAD_BTN, H_ZOOM_IN_BTN, H_ZOOM_OUT_BTN, V_ZOOM_IN_BTN, V_ZOOM_OUT_BTN, FIT_BTN,
        PAN_BTN, PAN_LEFT_BTN, PAN_RIGHT_BTN, PAN_TOP_BTN, PAN_BOTTOM_BTN, MERGE_BTN,
        UNMERGE_BTN, MARKER_BTN, SCREENSHOT_BTN, LIVE_UPDATES_BTN,
    ]


class ReportLocators:
    VIEW_REPORT_BTN = "#reportToolbarViewReportBtn"
    DOWNLOAD_HTML_BTN = "#reportToolbarDownloadCurrentHtmlReportBtn"
    DOWNLOAD_DUT_BTN = "#reportToolbarDownloadCurrentDutReportDataBtn"
    REPORT_DATA_MGMT_BTN = "#reportToolbarReportDataManagementBtn"
    REPORT_LOCATION = ".toolbar_report_location p"


class ConfigureLocators:
    CONTROLLER_MODE_DROPDOWN = "#opConfigControllerConfigureControllerModeComboBox"
    TEST_CABLE_TYPE_DROPDOWN = "#opConfigControllerConfigureTestCableTypeComboBox"
    PD_SPEC_TYPE_DROPDOWN = "#opConfigControllerConfigurePdSpecTypeComboBox"
    CABLE_EMULATION_DROPDOWN = "#opConfigControllerConfigureCableEmulationComboBox"
    RP_LEVEL_DROPDOWN = "#opConfigControllerConfigureRpLevelComboBox"
    CHANNEL_VBUS = "#opConfigControllerConfigureChannelsVBusCheckBox"
    CHANNEL_VBUS_SENSE = "#opConfigControllerConfigureChannelsVBusSenseCheckBox"
    CHANNEL_CC1 = "#opConfigControllerConfigureChannelsCC1CheckBox"
    CHANNEL_CC2 = "#opConfigControllerConfigureChannelsCC2heckBox"  # product typo, keep
    SAMPLING_RATIO_INPUT = "#opConfigControllerSamplingRatioInput"
    APPLY_BTN = "#opConfigControllerConfigureApplyBtn"
    START_CAPTURE_BTN = "#opConfigControllerConfigureStartBtn"
    STOP_CAPTURE_BTN = "#opConfigControllerConfigureStopBtn"
    ATTACH_BTN = "#opConfigControllerConfigureAttachBtn"
    DETACH_BTN = "#opConfigControllerConfigureDetachBtn"
    DOWNLOAD_CAPTURE_BTN = "#opConfigControllerConfigureDownloadCaptureBtn"
    VBUS_CURRENT_INPUT = "#opConfigControllerVbusCurrentInput"
    VCONN_CURRENT_INPUT = "#opConfigControllerVconnCurrentInput"

    CHANNELS = {
        "VBUS": CHANNEL_VBUS,
        "VBUS SENSE": CHANNEL_VBUS_SENSE,
        "CC1": CHANNEL_CC1,
        "CC2": CHANNEL_CC2,
    }


class LoopBackLocators:
    CONTAINER = ".loopback-container"
    DEVICE_SELECT = "#device-list"
    REFRESH_BTN = ".loopback-container .refresh-button"
    START_BTN = ".loopback-container .start-button"
    STOP_BTN = ".loopback-container .stop-button"
    DATA_ITEM = ".loopback-container .data-item"
    DATA_LABEL = ".data-label"
    DATA_VALUE = ".data-value"


class HelpLocators:
    SUPPORT_DESK_LINK = "#hpGraniteRiverLabsSupportDeskLinkLabel"
    EMAIL_SUPPORT_LINK = "#hpEmailCustomerSupportLinkLabel"
    DEBUG_LOG_LINK = "#hpDownloadDebugLogsLinkLabel"
    API_DOC_LINK = "#hpApiDocumentLinkLabel"
    PRODUCT_HEADING = ".help-container h2"
    APP_VERSION = ".help-container p"


class DropdownLocators:
    """Bootstrap dropdowns: a toggle <button id=X> and a menu labelled by X."""

    @staticmethod
    def menu(toggle_id: str) -> str:
        return f".dropdown-menu[aria-labelledby='{toggle_id.lstrip('#')}']"

    @staticmethod
    def items(toggle_id: str) -> str:
        return f"{DropdownLocators.menu(toggle_id)} .dropdown-item"
