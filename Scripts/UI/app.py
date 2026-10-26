"""
Modern PyQt6 Desktop GUI Test Runner for GRL USB PD C2 UI Automation.
Theme: Obsidian & Electric Amber.
Features: test tree discovered from the test files, presets, live search, retries, live log.
"""
import ast
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
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

        # Tree & Log view
        content_layout = QHBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Available Panels & Test Suites", "Status"])
        self.populate_tree()
        content_layout.addWidget(self.tree, 3)

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

        self.run_btn = QPushButton("🚀 Run Automation Tests")
        self.run_btn.setObjectName("runBtn")
        self.run_btn.clicked.connect(self.on_run_clicked)
        bottom_layout.addWidget(self.run_btn, 1)
        main_layout.addWidget(bottom_bar)

    def populate_tree(self):
        """Builds the tree from Scripts/TestCases by parsing test classes, functions and markers."""
        self.tree.clear()
        total = 0
        for suite, tests in discover_tests().items():
            suite_item = QTreeWidgetItem([suite, ""])
            suite_item.setFlags(suite_item.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
            for node_id, name, markers in tests:
                item = QTreeWidgetItem([name, ", ".join(sorted(markers))])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(0, Qt.CheckState.Checked)
                item.setData(0, Qt.ItemDataRole.UserRole, (node_id, markers))
                suite_item.addChild(item)
                total += 1
            self.tree.addTopLevelItem(suite_item)
        self.tree.expandAll()
        self.test_count_lbl.setText(f"Showing {total} tests")

    def _test_items(self):
        for i in range(self.tree.topLevelItemCount()):
            suite = self.tree.topLevelItem(i)
            for j in range(suite.childCount()):
                yield suite.child(j)

    def selected_node_ids(self) -> list[str]:
        return [item.data(0, Qt.ItemDataRole.UserRole)[0] for item in self._test_items()
                if item.checkState(0) == Qt.CheckState.Checked]

    def select_smoke_preset(self):
        for item in self._test_items():
            smoke = "smoke" in item.data(0, Qt.ItemDataRole.UserRole)[1]
            item.setCheckState(0, Qt.CheckState.Checked if smoke else Qt.CheckState.Unchecked)

    def select_full_preset(self):
        for item in self._test_items():
            item.setCheckState(0, Qt.CheckState.Checked)

    def clear_selection(self):
        for item in self._test_items():
            item.setCheckState(0, Qt.CheckState.Unchecked)

    def filter_tests(self, text):
        text = text.lower()
        visible_count = 0
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            parent_match = text in parent.text(0).lower()
            child_matches = False
            for j in range(parent.childCount()):
                child = parent.child(j)
                match = parent_match or text in child.text(0).lower()
                child.setHidden(not match)
                if match:
                    child_matches = True
                    visible_count += 1
            parent.setHidden(not (parent_match or child_matches))
        self.test_count_lbl.setText(f"Showing {visible_count} tests")

    def on_run_clicked(self):
        if self.controller:
            self.controller.start_execution()
        else:
            self.log_view.append("[INFO] Starting test execution in local runner...")
            self.progress_bar.setValue(50)

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


def _marker_names(decorators: list[ast.expr]) -> set[str]:
    names = set()
    for dec in decorators:
        node = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute) and node.value.attr == "mark":
            names.add(node.attr)
    return names - {"parametrize", "xfail", "skip", "skipif"}


def discover_tests() -> dict[str, list[tuple[str, str, set[str]]]]:
    """{suite file: [(pytest node id, test name, markers)]} without importing the test modules."""
    suites: dict[str, list[tuple[str, str, set[str]]]] = {}
    for path in sorted(TEST_DIR.glob("test_*.py")):
        rel = f"Scripts/TestCases/{path.name}"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        tests = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                cls_markers = _marker_names(node.decorator_list)
                for fn in node.body:
                    if isinstance(fn, ast.FunctionDef) and fn.name.startswith("test_"):
                        tests.append((f"{rel}::{node.name}::{fn.name}", fn.name,
                                      cls_markers | _marker_names(fn.decorator_list)))
            elif isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                tests.append((f"{rel}::{node.name}", node.name, _marker_names(node.decorator_list)))
        if tests:
            suites[path.name] = tests
    return suites
