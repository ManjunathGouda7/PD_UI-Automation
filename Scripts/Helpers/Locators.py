"""
Centralized Locators for the GRL-V-DPWR-EPR (USB PD C2) Web Application.
Aligned with live DOM elements running at http://localhost:5003/v1.1.1.html.
"""

class NavigationLocators:
    TAB_CONNECTION = "#left-toggle-group label:has-text('Connection Setup'), .leftnavbar-title:has-text('Connection Setup'), button:has-text('Connection Setup')"
    TAB_PRODUCT_CAP = "#left-toggle-group label:has-text('Product Capability'), .leftnavbar-title:has-text('Product Capability'), button:has-text('Product Capability')"
    TAB_TEST_CONFIG = "#left-toggle-group label:has-text('Test Config'), .leftnavbar-title:has-text('Test Config'), button:has-text('Test Config')"
    TAB_RESULTS = "#left-toggle-group label:has-text('Results'), .leftnavbar-title:has-text('Results'), button:has-text('Results')"
    TAB_REPORT = "#left-toggle-group label:has-text('Report'), .leftnavbar-title:has-text('Report'), button:has-text('Report')"
    TAB_CONFIGURE = "#left-toggle-group label:has-text('Configure'), .leftnavbar-title:has-text('Configure'), button:has-text('Configure')"
    TAB_LOOPBACK = "#left-toggle-group label:has-text('LoopBack'), .leftnavbar-title:has-text('LoopBack'), button:has-text('LoopBack')"
    TAB_HELP = "#left-toggle-group label:has-text('Help'), .leftnavbar-title:has-text('Help'), button:has-text('Help')"
    
    MODAL_OK_BTN = ".popupButton_Ok, button:has-text('Ok')"
    ALL_TABS = [
        TAB_CONNECTION, TAB_PRODUCT_CAP, TAB_TEST_CONFIG, TAB_RESULTS,
        TAB_REPORT, TAB_CONFIGURE, TAB_LOOPBACK, TAB_HELP
    ]


class ConnectionLocators:
    SCAN_NETWORK_BTN = "#csScanNetworkBtn, button:has-text('Scan Network'), .scanBtn"
    CONNECT_BTN = "#csConnectBtn, button:has-text('Connect'), .connectBtn"
    DISCONNECT_BTN = "button:has-text('Disconnect')"
    IP_DROPDOWN = ".rc-select-search__field, select.ip-select, input[placeholder*='IP'], .ipInput"
    PRIMARY_IP_OPTION = "option:has-text('192.168.102.76'), text=192.168.102.76"
    UPDATE_FW_BTN = "#csUpdateSystemFirmwareBtn, button:has-text('Update System firmware')"
    TESTER_STATUS_HEADER = "text=Tester Status, h4:has-text('Tester Status')"
    STATUS_FIRMWARE = "text=Firmware Version"
    STATUS_CALIBRATION = "text=Last Calibration Date, text=Calibration"
    STATUS_LICENSES = "text=License Information, text=Licenses"


class ProductCapLocators:
    PROJECT_NAME_INPUT = "#pcNewProjectNameInputField, input.project-name-input"
    PROJECT_SAVE_BTN = "#pcNewProjectNameSaveBtn, button:has-text('Save')"
    LOAD_VIF_BTN = "#pcLoadXmlVifFileBtn, button:has-text('Load XML VIF File'), button:has-text('Load VIF')"
    CLEAR_VIF_BTN = "#pcPort1ClearDeviceDataBtn, button:has-text('Clear'), button:has-text('Clear VIF')"
    READ_DEVICE_BTN = "#pcPort1GetDeviceDataBtn, button:has-text('Read Device Data'), .btnReadDevice"
    DUT_TYPE_DROPDOWN = "#pcPort1DutTypeComboBox, select.dut-role, button:has-text('Provider Only')"
    CABLE_SELECT = "#pcPort1CableSelectionComboBox, select.cable-select, button:has-text('GRL-SPL EPR')"
    VIF_GENERATOR_LINK = "a.xml-tool, text='USB-IF VIF Generator Download Link'"


class TestConfigLocators:
    START_EXECUTION_BTN = "#tcStartAndStopExecutionBtn, button:has-text('Start Execution')"
    CERTIFICATION_COMBO = "#tcCertificationComboBox, button.dropdowncustom"
    SEARCH_INPUT = "#tcSearchTestCaseInputField, input[placeholder*='Search'], input[type='search']"
    EXPAND_TEST_LIST = "#tcExpandTestListCheckBox"
    RERUN_SELECTED_CHECKBOX = "#tcRunSelectedTestsCheckBox"
    TEST_ENGINEER_INPUT = "#tcReportTestEngineerInputField, input[name*='engineer'], input[placeholder*='Engineer']"
    TEST_LAB_INPUT = "#tcReportTestLabInputField"
    MANUFACTURER_INPUT = "#tcReportManufacturerInputField"
    REPORT_FOLDER_PATH_INPUT = "#tcReportFolderPathInputField"
    CATEGORY_PD_3_2 = "text=Power Delivery 3.2 Tests"
    CATEGORY_USBC = "text=USB-C Functional Tests"
    CATEGORY_SAFETY = "text=IEC Functional Safety Tests"


class ResultsLocators:
    CHART_CONTAINER = "#plot-container, .chartist, .chart-container, canvas"
    ZOOM_IN_BTN = "#chart_toolbar_horizontal_zoom_in_button, button[title*='Zoom In'], button:has-text('Zoom In')"
    ZOOM_OUT_BTN = "#chart_toolbar_horizontal_zoom_out_button, button[title*='Zoom Out'], button:has-text('Zoom Out')"
    RESET_PLOT_BTN = "#chart_toolbar_fit_button, button:has-text('Reset'), button:has-text('Fit')"
    PAN_PLOT_BTN = "#chart_toolbar_click_pan_button, button[title*='Pan'], button:has-text('Pan')"
    HORIZONTAL_MARKER = "#chart_toolbar_set_marker_button, button:has-text('H-Marker')"
    VERTICAL_MARKER = "#chart_toolbar_set_marker_button, button:has-text('V-Marker')"
    PASSED_COUNTER = ".badge-pass, .test-results-notify-count, text=Pass:"
    FAILED_COUNTER = ".badge-fail, .test-results-notify-count, text=Fail:"
    SCREENSHOT_BTN = "#btn_screenshot"
    CHANNELS_DROPDOWN = ".channels-dropdown-toggle"


class ReportLocators:
    VIEW_REPORT_BTN = "#reportToolbarViewReportBtn, button:has-text('View Report')"
    DOWNLOAD_HTML_BTN = "#reportToolbarDownloadCurrentHtmlReportBtn, button:has-text('Download Current HTML Report')"
    DOWNLOAD_DUT_BTN = "#reportToolbarDownloadCurrentDutReportDataBtn, button:has-text('Download Current DUT Report Data')"
    REPORT_DATA_MGMT_BTN = "#reportToolbarReportDataManagementBtn, button:has-text('Report Data Management')"
    REPORT_PATH_LABEL = "text=Test Reports Location"


class ConfigureLocators:
    CONTROLLER_MODE_SELECT = "#opConfigControllerConfigureControllerModeComboBox, select.controller-mode"
    CHANNEL_VBUS = "#opConfigControllerConfigureChannelsVBusCheckBox, input[type='checkbox']#ch_vbus"
    CHANNEL_VBUS_SENSE = "#opConfigControllerConfigureChannelsVBusSenseCheckBox"
    CHANNEL_CC1 = "#opConfigControllerConfigureChannelsCC1CheckBox"
    CHANNEL_CC2 = "#opConfigControllerConfigureChannelsCC2heckBox"
    SAMPLING_RATIO_INPUT = "#opConfigControllerSamplingRatioInput"
    APPLY_CONFIG_BTN = "#opConfigControllerConfigureApplyBtn, button:has-text('Apply')"
    ATTACH_BTN = "#opConfigControllerConfigureAttachBtn, button:has-text('Attach')"
    DETACH_BTN = "#opConfigControllerConfigureDetachBtn, button:has-text('Detach')"
    START_CAPTURE_BTN = "#opConfigControllerConfigureStartBtn"
    STOP_CAPTURE_BTN = "#opConfigControllerConfigureStopBtn"
    DOWNLOAD_CAPTURE_BTN = "#opConfigControllerConfigureDownloadCaptureBtn"


class LoopBackLocators:
    DEVICE_SELECT = "#device-list, select.loopback-device"
    REFRESH_BTN = ".refresh-button, button:has-text('Refresh')"
    START_LOOPBACK_BTN = ".start-button, button:has-text('Start')"
    STOP_LOOPBACK_BTN = ".stop-button, button:has-text('Stop')"
    THROUGHPUT_LABEL = ".data-value, .throughput-val, text=Throughput"


class HelpLocators:
    SUPPORT_DESK_LINK = "#hpGraniteRiverLabsSupportDeskLinkLabel, a:has-text('Granite River Labs Support Desk')"
    EMAIL_SUPPORT_LINK = "#hpEmailCustomerSupportLinkLabel, a:has-text('Email Customer Support')"
    DEBUG_LOG_BTN = "#hpDownloadDebugLogsLinkLabel, a:has-text('Download Debug Logs')"
    API_DOC_LINK = "#hpApiDocumentLinkLabel, a:has-text('API Document')"
