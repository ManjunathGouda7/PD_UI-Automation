"""
Centralized Locators for the GRL-V-DPWR-EPR (USB PD C2) Web Application.
"""

class NavigationLocators:
    TAB_CONNECTION = "button:has-text('Connection Setup'), a:has-text('Connection Setup')"
    TAB_PRODUCT_CAP = "button:has-text('Product Capability'), a:has-text('Product Capability')"
    TAB_TEST_CONFIG = "button:has-text('Test Config'), a:has-text('Test Config')"
    TAB_RESULTS = "button:has-text('Results'), a:has-text('Results')"
    TAB_REPORT = "button:has-text('Report'), a:has-text('Report')"
    TAB_CONFIGURE = "button:has-text('Configure'), a:has-text('Configure')"
    TAB_LOOPBACK = "button:has-text('LoopBack'), a:has-text('LoopBack')"
    TAB_HELP = "button:has-text('Help'), a:has-text('Help')"
    ALL_TABS = [
        TAB_CONNECTION, TAB_PRODUCT_CAP, TAB_TEST_CONFIG, TAB_RESULTS,
        TAB_REPORT, TAB_CONFIGURE, TAB_LOOPBACK, TAB_HELP
    ]


class ConnectionLocators:
    SCAN_NETWORK_BTN = "button:has-text('Scan Network'), .scanBtn"
    CONNECT_BTN = "button:has-text('Connect'), .connectBtn"
    DISCONNECT_BTN = "button:has-text('Disconnect')"
    IP_DROPDOWN = "select.ip-select, input[placeholder*='IP'], .ipInput"
    PRIMARY_IP_OPTION = "option:has-text('192.168.102.76'), text=192.168.102.76"
    TESTER_STATUS_HEADER = "h4:has-text('Tester Status'), text=Tester Status"
    STATUS_FIRMWARE = "text=Firmware"
    STATUS_CALIBRATION = "text=Calibration"
    STATUS_LICENSES = "text=Licenses"


class ProductCapLocators:
    LOAD_VIF_BTN = "button:has-text('Load VIF'), input[type='file']"
    CLEAR_VIF_BTN = "button:has-text('Clear'), button:has-text('Clear VIF')"
    READ_DEVICE_BTN = "button:has-text('Read Device'), .btnReadDevice"
    DUT_TYPE_DROPDOWN = "select:has-text('Provider Only'), select.dut-role"
    CABLE_SELECT = "select:has-text('GRL-SPL EPR Cable'), select.cable-select"
    CERTIFICATION_ID_INPUT = "input[placeholder*='Certification'], input[name*='cert']"


class TestConfigLocators:
    SELECT_ALL_CHECKBOX = "input[type='checkbox']#selectAll, button:has-text('Select All')"
    DESELECT_ALL_BTN = "button:has-text('Deselect All'), button:has-text('Clear All')"
    SEARCH_INPUT = "input[placeholder*='Search'], input[type='search']"
    TEST_ITEMS = ".test-item-checkbox, input[type='checkbox'].test-check"
    CATEGORY_PD_3_2 = "text=Power Delivery 3.2 Tests"
    CATEGORY_USBC = "text=USB-C Functional Tests"
    CATEGORY_SAFETY = "text=IEC Functional Safety Tests"
    DUT_INFO_PANEL = "text=DUT Information"
    TEST_ENGINEER_INPUT = "input[name*='engineer'], input[placeholder*='Engineer']"


class ResultsLocators:
    CHART_CONTAINER = ".chartist, .chart-container, canvas, svg.chart"
    ZOOM_IN_BTN = "button:has-text('Zoom In'), button[title*='Zoom In']"
    ZOOM_OUT_BTN = "button:has-text('Zoom Out'), button[title*='Zoom Out']"
    RESET_PLOT_BTN = "button:has-text('Reset'), button:has-text('Fit')"
    PAN_PLOT_BTN = "button:has-text('Pan'), button[title*='Pan']"
    HORIZONTAL_MARKER = "button:has-text('H-Marker'), text=H-Marker"
    VERTICAL_MARKER = "button:has-text('V-Marker'), text=V-Marker"
    LOG_TABLE_ROWS = "table.results-table tbody tr, .results-row"
    PASSED_COUNTER = ".badge-pass, text=Pass:"
    FAILED_COUNTER = ".badge-fail, text=Fail:"


class ReportLocators:
    VIEW_REPORT_BTN = "button:has-text('View Report')"
    DOWNLOAD_HTML_BTN = "button:has-text('Download HTML Report'), button:has-text('HTML')"
    DOWNLOAD_DUT_BTN = "button:has-text('Download DUT Report Data'), button:has-text('DUT Data')"
    REPORT_PATH_INPUT = "input[placeholder*='Report Path'], input.report-dir"


class ConfigureLocators:
    CONTROLLER_MODE_SELECT = "select.controller-mode, select:has-text('UFP/Sink')"
    CHANNEL_VBUS = "input[type='checkbox']#ch_vbus, label:has-text('VBUS')"
    CHANNEL_VBUS_SENSE = "input[type='checkbox']#ch_sense, label:has-text('VBUS SENSE')"
    CHANNEL_CC1 = "input[type='checkbox']#ch_cc1, label:has-text('CC1')"
    CHANNEL_CC2 = "input[type='checkbox']#ch_cc2, label:has-text('CC2')"
    ATTACH_DETACH_BTN = "button:has-text('Attach'), button:has-text('Detach')"
    APPLY_CONFIG_BTN = "button:has-text('Apply'), button:has-text('Set')"


class LoopBackLocators:
    DEVICE_SELECT = "select.loopback-device, select:has-text('LoopBack')"
    START_LOOPBACK_BTN = "button:has-text('Start'), button:has-text('Run LoopBack')"
    STOP_LOOPBACK_BTN = "button:has-text('Stop')"
    THROUGHPUT_LABEL = "text=Throughput, .throughput-val"
    BYTES_TRANSFERRED = "text=Transferred, .bytes-tx"


class HelpLocators:
    DEBUG_LOG_BTN = "button:has-text('Download Debug Log'), a:has-text('Debug Log')"
    DIAGNOSTICS_SECTION = "text=Diagnostics, text=Hardware Info"
    API_DOC_LINK = "a:has-text('API Documentation'), a[href*='api']"
