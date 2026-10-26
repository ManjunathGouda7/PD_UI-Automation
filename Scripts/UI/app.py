"""
Modern PyQt6 Desktop GUI Test Runner for GRL USB PD C2 UI Automation.
Theme: Obsidian & Electric Amber.
Features: test tree discovered from the test files, presets, live search, retries, live log.
"""
import ast
from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QColor, QDesktopServices
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from Scripts.Helpers.reporting import humanize_test_name, short_name_from_title, suite_title

DARK_STYLESHEET = """
QMainWindow {
    background-color: #0a0b0f;
}
QWidget {
    color: #f8fafc;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 13px;
}
QFrame#card {
    background-color: #131622;
    border: 1px solid #232936;
    border-radius: 8px;
    padding: 12px;
}
QLabel#title {
    color: #ff7800;
    font-size: 18px;
    font-weight: bold;
}
QPushButton {
    background-color: #1e2433;
    border: 1px solid #2d3548;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #2b344a;
    border-color: #ff7800;
}
QPushButton#runBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff7800, stop:1 #e05500);
    color: #ffffff;
    font-weight: bold;
    border: none;
    padding: 10px 24px;
    font-size: 14px;
}
QLineEdit, QComboBox {
    background-color: #131622;
    border: 1px solid #2d3548;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f8fafc;
}
QProgressBar {
    background-color: #131622;
    border: 1px solid #232936;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #ff7800;
    border-radius: 5px;
}
QTreeWidget {
    background-color: #131622;
    border: 1px solid #232936;
    border-radius: 6px;
    color: #f8fafc;
}
QHeaderView::section {
    background-color: #1e2433;
    color: #f8fafc;
    border: none;
    border-bottom: 1px solid #2d3548;
    padding: 6px;
    font-weight: bold;
}
QTreeWidget::indicator {
    width: 13px;
    height: 13px;
    border-radius: 3px;
    border: 1px solid #64748b;
    background-color: #0d0e14;
}
QTreeWidget::indicator:checked {
    background-color: #ff7800;
    border-color: #ff7800;
}
QTreeWidget::indicator:indeterminate {
    background-color: #7c3f0a;
    border-color: #ff7800;
}
QFrame#sidebar {
    background-color: #131622;
    border: 1px solid #232936;
    border-radius: 8px;
}
QPushButton#navBtn {
    text-align: left;
    padding: 9px 12px;
    background-color: #1e2433;
    border: 1px solid #2d3548;
}
QPushButton#navBtn:checked {
    background-color: #ff7800;
    border-color: #ff7800;
    color: #ffffff;
}
QPushButton#runAllBtn {
    background-color: #1e2433;
    border: 1px solid #ff7800;
    color: #ff7800;
    font-weight: bold;
    padding: 10px 20px;
    font-size: 14px;
}
QLabel#panelTitle {
    color: #ff7800;
    font-size: 15px;
    font-weight: bold;
}
QTextEdit {
    background-color: #0d0e14;
    border: 1px solid #232936;
    border-radius: 6px;
    font-family: 'Consolas', monospace;
    font-size: 12px;
    color: #10b981;
}
"""

class MainWindow(QMainWindow):
    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("GRL USB PD C2 - Modern Test Automation Suite")
        self.resize(1100, 750)
        self.setStyleSheet(DARK_STYLESHEET)
        self.init_ui()
        QTimer.singleShot(200, self.update_backend_status)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Top Bar
        top_bar = QFrame()
        top_bar.setObjectName("card")
        top_layout = QHBoxLayout(top_bar)
        title_lbl = QLabel("⚡ GRL-V-DPWR-EPR (USB PD C2) Automation Suite")
        title_lbl.setObjectName("title")
        top_layout.addWidget(title_lbl)
        top_layout.addStretch()

        self.backend_status_lbl = QLabel("🟡 Checking C2 Backend...")
        self.backend_status_lbl.setStyleSheet("background-color: #1e2433; border: 1px solid #334155; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 11px;")
        top_layout.addWidget(self.backend_status_lbl)
        top_layout.addSpacing(10)

        from Scripts.Helpers.config import Config
        self.ip_input = QLineEdit(Config.dut_ip())
        self.ip_input.setPlaceholderText("Tester IP")
        self.ip_input.setFixedWidth(140)
        top_layout.addWidget(QLabel("IP:"))
        top_layout.addWidget(self.ip_input)
        main_layout.addWidget(top_bar)


        # Presets & Execution Options Bar
        opts_bar = QFrame()
        opts_bar.setObjectName("card")
        opts_layout = QHBoxLayout(opts_bar)

        btn_smoke = QPushButton("⚡ Smoke Test")
        btn_smoke.clicked.connect(self.select_smoke_preset)
        opts_layout.addWidget(btn_smoke)

        btn_full = QPushButton("🎯 Full Suite")
        btn_full.clicked.connect(self.select_full_preset)
        opts_layout.addWidget(btn_full)

        btn_clear = QPushButton("🧹 Clear")
        btn_clear.clicked.connect(self.clear_selection)
        opts_layout.addWidget(btn_clear)

        opts_layout.addSpacing(20)
        opts_layout.addWidget(QLabel("Retries:"))
        self.retries_combo = QComboBox()
        self.retries_combo.addItems(["0", "1", "2"])
        self.retries_combo.setCurrentText("0")
        opts_layout.addWidget(self.retries_combo)

        self.hw_actions_chk = QCheckBox("Allow hardware actions")
        self.hw_actions_chk.setToolTip("Also run tests that connect, apply configuration or otherwise change the tester")
        opts_layout.addWidget(self.hw_actions_chk)

        self.headless_chk = QCheckBox("Headless Browser")
        self.headless_chk.setChecked(False)
        opts_layout.addWidget(self.headless_chk)

        opts_layout.addStretch()
        main_layout.addWidget(opts_bar)

        # Search Bar
        search_bar = QFrame()
        search_bar.setObjectName("card")
        sb_layout = QHBoxLayout(search_bar)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search tests by name or panel...")
        self.search_input.textChanged.connect(self.filter_tests)
        sb_layout.addWidget(self.search_input)
        self.test_count_lbl = QLabel("")
        sb_layout.addWidget(self.test_count_lbl)
        main_layout.addWidget(search_bar)

        # Panel sidebar | test list | log
        self.suites = discover_tests()
        content_layout = QHBoxLayout()
        content_layout.addWidget(self._build_sidebar())

        tests_box = QVBoxLayout()
        self.panel_title_lbl = QLabel("")
        self.panel_title_lbl.setObjectName("panelTitle")
        tests_box.addWidget(self.panel_title_lbl)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Panels & Test Cases", "Status"])
        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.populate_tree()
        tests_box.addWidget(self.tree)
        content_layout.addLayout(tests_box, 3)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("Live automation log output will appear here...")
        content_layout.addWidget(self.log_view, 2)
        main_layout.addLayout(content_layout)

        # Bottom Controls
        bottom_bar = QFrame()
        bottom_bar.setObjectName("card")
        bottom_layout = QHBoxLayout(bottom_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        bottom_layout.addWidget(self.progress_bar, 4)

        self.run_btn = QPushButton("▶ Run Selected")
        self.run_btn.setObjectName("runBtn")
        self.run_btn.setToolTip("Run the ticked tests of the panel shown on the left")
        self.run_btn.clicked.connect(self.on_run_clicked)
        bottom_layout.addWidget(self.run_btn, 1)

        self.run_all_btn = QPushButton("⏩ Run All")
        self.run_all_btn.setObjectName("runAllBtn")
        self.run_all_btn.setToolTip("Run every test of every panel")
        self.run_all_btn.clicked.connect(self.on_run_all_clicked)
        bottom_layout.addWidget(self.run_all_btn, 1)

        self.open_report_btn = QPushButton("📂 Open Report")
        self.open_report_btn.setToolTip("Open the report folder of the last run")
        self.open_report_btn.setEnabled(False)
        self.open_report_btn.clicked.connect(self.open_last_report)
        bottom_layout.addWidget(self.open_report_btn)
        main_layout.addWidget(bottom_bar)

        self.show_panel(None)

    def _build_sidebar(self) -> QFrame:
        """One button per test panel (plus 'All Panels'); clicking shows only that panel's scripts."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        self.panel_buttons = QButtonGroup(self)
        self.panel_buttons.setExclusive(True)
        entries = [(None, "All Panels", sum(len(s.tests) for s in self.suites))]
        entries += [(i, s.short_name, len(s.tests)) for i, s in enumerate(self.suites)]
        for index, name, count in entries:
            btn = QPushButton(f"{name}  ({count})")
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _=False, i=index: self.show_panel(i))
            self.panel_buttons.addButton(btn)
            layout.addWidget(btn)
            if index is None:
                btn.setChecked(True)
        layout.addStretch()
        return sidebar

    def show_panel(self, index: int | None) -> None:
        """Shows one panel's tests (None = all panels)."""
        self.current_panel = index
        title = "All Panels" if index is None else self.suites[index].title
        self.panel_title_lbl.setText(title)
        self.filter_tests(self.search_input.text())

    def populate_tree(self):
        """Builds the tree from Scripts/TestCases: readable panel and test names, run status per test."""
        self.tree.clear()
        self._items_by_node: dict[str, QTreeWidgetItem] = {}
        total = 0
        for suite_index, suite in enumerate(self.suites):
            suite_item = QTreeWidgetItem([f"{suite.title}  ({len(suite.tests)})", ""])
            suite_item.setData(0, Qt.ItemDataRole.UserRole, suite_index)
            suite_item.setToolTip(0, suite.file)
            suite_item.setFlags(suite_item.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
            font = suite_item.font(0)
            font.setBold(True)
            suite_item.setFont(0, font)
            for test in suite.tests:
                item = QTreeWidgetItem([test.title, ""])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(0, Qt.CheckState.Checked)
                item.setData(0, Qt.ItemDataRole.UserRole, (test.node_id, test.markers))
                tip = [test.description] if test.description else []
                tip += [f"Tags: {', '.join(sorted(test.markers)) or '-'}", test.node_id]
                item.setToolTip(0, "\n".join(tip))
                suite_item.addChild(item)
                self._items_by_node[test.node_id] = item
                total += 1
            self.tree.addTopLevelItem(suite_item)
        self.reset_statuses()
        self.tree.expandAll()
        self.test_count_lbl.setText(f"Showing {total} tests")

    def reset_statuses(self):
        for item in self._test_items():
            markers = item.data(0, Qt.ItemDataRole.UserRole)[1]
            ready = "Ready · changes tester" if "hardware" in markers else "Ready"
            item.setText(1, ready)
            item.setForeground(1, QColor("#94a3b8"))

    _STATUS_COLORS = {"PASSED": "#34d399", "FAILED": "#f87171", "ERROR": "#f87171",
                      "SKIPPED": "#fbbf24", "XFAIL": "#a78bfa", "RUNNING": "#60a5fa"}
    _STATUS_RANK = {"RUNNING": 0, "PASSED": 1, "XFAIL": 2, "SKIPPED": 3, "FAILED": 4, "ERROR": 5}

    def set_test_status(self, node_id: str, status: str):
        """Live status from the runner. Parametrised cases roll up: the worst outcome wins."""
        item = self._items_by_node.get(node_id.split("[", 1)[0])
        if item is None:
            return
        current = item.text(1)
        if "[" in node_id and current in self._STATUS_RANK and status != "RUNNING":
            if self._STATUS_RANK[current] > self._STATUS_RANK.get(status, 0):
                return
        item.setText(1, status)
        item.setForeground(1, QColor(self._STATUS_COLORS.get(status, "#f8fafc")))

    def _test_items(self):
        for i in range(self.tree.topLevelItemCount()):
            suite = self.tree.topLevelItem(i)
            for j in range(suite.childCount()):
                yield suite.child(j)

    def _shown_test_items(self):
        """Test rows currently shown (selected panel and search filter)."""
        for item in self._test_items():
            if not item.isHidden() and not item.parent().isHidden():
                yield item

    def selected_node_ids(self) -> list[str]:
        """Ticked tests of the panel being shown."""
        return [item.data(0, Qt.ItemDataRole.UserRole)[0] for item in self._shown_test_items()
                if item.checkState(0) == Qt.CheckState.Checked]

    def all_node_ids(self) -> list[str]:
        """Every test of every panel, regardless of ticks or filters."""
        return [test.node_id for suite in self.suites for test in suite.tests]

    def select_smoke_preset(self):
        for item in self._shown_test_items():
            smoke = "smoke" in item.data(0, Qt.ItemDataRole.UserRole)[1]
            item.setCheckState(0, Qt.CheckState.Checked if smoke else Qt.CheckState.Unchecked)

    def select_full_preset(self):
        for item in self._shown_test_items():
            item.setCheckState(0, Qt.CheckState.Checked)

    def clear_selection(self):
        for item in self._shown_test_items():
            item.setCheckState(0, Qt.CheckState.Unchecked)

    def filter_tests(self, text):
        text = text.lower()
        visible_count = 0
        panel = getattr(self, "current_panel", None)
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            if panel is not None and parent.data(0, Qt.ItemDataRole.UserRole) != panel:
                parent.setHidden(True)
                continue
            parent_match = text in parent.text(0).lower()
            child_matches = False
            for j in range(parent.childCount()):
                child = parent.child(j)
                node_id = child.data(0, Qt.ItemDataRole.UserRole)[0].rsplit("::", 1)[-1].lower()
                match = parent_match or text in child.text(0).lower() or text in node_id
                child.setHidden(not match)
                if match:
                    child_matches = True
                    visible_count += 1
            parent.setHidden(not (parent_match or child_matches))
        self.test_count_lbl.setText(f"Showing {visible_count} tests")

    def on_run_clicked(self):
        if self.controller:
            self.controller.start_execution(self.selected_node_ids())

    def on_run_all_clicked(self):
        if self.controller:
            self.controller.start_execution(self.all_node_ids())

    def set_last_report_dir(self, folder: str) -> None:
        self.last_report_dir = folder
        self.open_report_btn.setEnabled(True)
        self.open_report_btn.setToolTip(folder)

    def open_last_report(self) -> None:
        folder = getattr(self, "last_report_dir", "")
        if folder:
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def set_running(self, running: bool) -> None:
        self.run_btn.setEnabled(not running)
        self.run_all_btn.setEnabled(not running)

    def update_backend_status(self):
        try:
            from Scripts.Helpers.api_client import c2_api
            if c2_api.is_online():
                ver = c2_api.get_software_version()
                conn = c2_api.get_connection_info().get("testerStatus", "unknown")
                self.backend_status_lbl.setText(f"🟢 C2 Online (v{ver}) | {conn}")
                self.backend_status_lbl.setStyleSheet("background-color: #064e3b; color: #34d399; border: 1px solid #059669; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 11px;")
            else:
                self.backend_status_lbl.setText("🔴 C2 Offline")
                self.backend_status_lbl.setStyleSheet("background-color: #450a0a; color: #f87171; border: 1px solid #dc2626; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 11px;")
        except Exception:
            self.backend_status_lbl.setText("⚪ C2 Offline")
            self.backend_status_lbl.setStyleSheet("background-color: #1e2433; color: #94a3b8; border: 1px solid #334155; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 11px;")



TEST_DIR = Path(__file__).resolve().parent.parent / "TestCases"


@dataclass
class DiscoveredTest:
    node_id: str
    title: str
    description: str
    markers: set[str]


@dataclass
class DiscoveredSuite:
    file: str
    title: str
    tests: list[DiscoveredTest] = field(default_factory=list)

    @property
    def short_name(self) -> str:
        """Sidebar label - same name as the panel's report folder."""
        return short_name_from_title(self.title)


def _marker_names(decorators: list[ast.expr]) -> set[str]:
    names = set()
    for dec in decorators:
        node = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute) and node.value.attr == "mark":
            names.add(node.attr)
    return names - {"parametrize", "xfail", "skip", "skipif"}



def _discovered_test(fn: ast.FunctionDef, prefix: str, inherited: set[str]) -> DiscoveredTest:
    doc = (ast.get_docstring(fn) or "").strip().splitlines()
    return DiscoveredTest(
        node_id=f"{prefix}::{fn.name}",
        title=humanize_test_name(fn.name),
        description=doc[0] if doc else "",
        markers=inherited | _marker_names(fn.decorator_list),
    )


def discover_tests() -> list[DiscoveredSuite]:
    """Test suites and cases read from the test files without importing them."""
    suites: list[DiscoveredSuite] = []
    for path in sorted(TEST_DIR.glob("test_*.py")):
        rel = f"Scripts/TestCases/{path.name}"
        module = ast.parse(path.read_text(encoding="utf-8"))
        suite = DiscoveredSuite(file=rel, title=suite_title(str(path)))
        for node in module.body:
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                cls_markers = _marker_names(node.decorator_list)
                for fn in node.body:
                    if isinstance(fn, ast.FunctionDef) and fn.name.startswith("test_"):
                        suite.tests.append(_discovered_test(fn, f"{rel}::{node.name}", cls_markers))
            elif isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                suite.tests.append(_discovered_test(node, rel, set()))
        if suite.tests:
            suites.append(suite)
    return suites
