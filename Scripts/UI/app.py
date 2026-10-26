"""
PyQt6 desktop test runner for GRL USB PD C2 UI Automation.
Theme: Obsidian & Electric Amber.

Layout: options bar, panel sidebar | test list | live log + test details, run controls.
Tests run in a separate pytest process (see MainGUI.GUIController) so a run can be stopped.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
import html
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QSettings, Qt, QTimer, QUrl
from PyQt6.QtGui import QColor, QDesktopServices, QGuiApplication, QPixmap
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
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from Scripts.Helpers.reporting import humanize_test_name, short_name_from_title, suite_title

DARK_STYLESHEET = """
QMainWindow { background-color: #0a0b0f; }
QWidget {
    color: #f8fafc;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 13px;
}
QFrame#card {
    background-color: #131622;
    border: 1px solid #232936;
    border-radius: 8px;
}
QLabel#title { color: #ff7800; font-size: 17px; font-weight: bold; }
QLabel#panelTitle { color: #ff7800; font-size: 15px; font-weight: bold; }
QLabel#sectionTitle { color: #94a3b8; font-size: 12px; font-weight: bold; }
QPushButton {
    background-color: #1e2433;
    border: 1px solid #2d3548;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 600;
}
QPushButton:hover { background-color: #2b344a; border-color: #ff7800; }
QPushButton:disabled { color: #64748b; border-color: #232936; }
QPushButton#runBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff7800, stop:1 #e05500);
    color: #ffffff; border: none; padding: 9px 20px; font-size: 14px; font-weight: bold;
}
QPushButton#runBtn:disabled { background: #3a2a1a; color: #94a3b8; }
QPushButton#runAllBtn {
    border: 1px solid #ff7800; color: #ff7800; padding: 9px 18px; font-size: 14px; font-weight: bold;
}
QPushButton#stopBtn {
    border: 1px solid #ef4444; color: #f87171; padding: 9px 18px; font-size: 14px; font-weight: bold;
}
QPushButton#navBtn { text-align: left; padding: 8px 12px; }
QPushButton#navBtn:checked { background-color: #ff7800; border-color: #ff7800; color: #ffffff; }
QLineEdit, QComboBox {
    background-color: #0d0e14;
    border: 1px solid #2d3548;
    border-radius: 6px;
    padding: 5px 9px;
    color: #f8fafc;
}
QProgressBar {
    background-color: #0d0e14; border: 1px solid #232936; border-radius: 6px;
    text-align: center; color: #ffffff; font-weight: bold;
}
QProgressBar::chunk { background-color: #ff7800; border-radius: 5px; }
QTreeWidget, QTextBrowser {
    background-color: #131622; border: 1px solid #232936; border-radius: 6px; color: #f8fafc;
}
QHeaderView::section {
    background-color: #1e2433; color: #f8fafc; border: none;
    border-bottom: 1px solid #2d3548; padding: 6px; font-weight: bold;
}
QTreeWidget::indicator {
    width: 13px; height: 13px; border-radius: 3px;
    border: 1px solid #64748b; background-color: #0d0e14;
}
QTreeWidget::indicator:checked { background-color: #ff7800; border-color: #ff7800; }
QTreeWidget::indicator:indeterminate { background-color: #7c3f0a; border-color: #ff7800; }
QScrollArea#sidebar { background-color: #131622; border: 1px solid #232936; border-radius: 8px; }
QWidget#sidebarInner { background-color: #131622; }
QPlainTextEdit {
    background-color: #0d0e14; border: 1px solid #232936; border-radius: 6px;
    font-family: 'Consolas', monospace; font-size: 12px; color: #10b981;
}
QSplitter::handle { background-color: #0a0b0f; }
"""

STATUS_COLORS = {"PASSED": "#34d399", "FAILED": "#f87171", "ERROR": "#f87171", "SKIPPED": "#fbbf24",
                 "XFAIL": "#a78bfa", "RUNNING": "#60a5fa", "STOPPED": "#94a3b8"}
STATUS_RANK = {"RUNNING": 0, "PASSED": 1, "XFAIL": 2, "SKIPPED": 3, "FAILED": 4, "ERROR": 5}

PILL = "padding: 4px 10px; border-radius: 11px; font-weight: bold; font-size: 11px;"
PILL_OK = "background-color: #064e3b; color: #34d399; border: 1px solid #059669; " + PILL
PILL_WARN = "background-color: #422006; color: #fbbf24; border: 1px solid #b45309; " + PILL
PILL_BAD = "background-color: #450a0a; color: #f87171; border: 1px solid #dc2626; " + PILL
PILL_IDLE = "background-color: #1e2433; color: #94a3b8; border: 1px solid #334155; " + PILL


def _card() -> tuple[QFrame, QHBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(12, 8, 12, 8)
    return frame, layout


class MainWindow(QMainWindow):
    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.settings = QSettings("GRL", "PD-UI-Automation")
        self.results: dict[str, list[dict[str, Any]]] = {}   # base node id -> result events
        self.last_report_dir = ""
        self.setWindowTitle("GRL USB PD C2 - Test Automation Suite")
        self.setStyleSheet(DARK_STYLESHEET)
        self.init_ui()
        self._fit_to_screen()
        self._restore_settings()
        QTimer.singleShot(200, self.update_backend_status)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # Header: title | backend status | tester IP
        header, h = _card()
        title = QLabel("⚡ GRL-V-DPWR-EPR (USB PD C2) Automation Suite")
        title.setObjectName("title")
        h.addWidget(title)
        h.addStretch()
        self.backend_status_lbl = QLabel("Checking C2 backend...")
        self.backend_status_lbl.setStyleSheet(PILL_IDLE)
        h.addWidget(self.backend_status_lbl)
        refresh = QPushButton("⟳")
        refresh.setToolTip("Refresh backend / tester status")
        refresh.clicked.connect(self.update_backend_status)
        h.addWidget(refresh)
        h.addSpacing(8)
        from Scripts.Helpers.config import Config
        h.addWidget(QLabel("Tester IP:"))
        self.ip_input = QLineEdit(Config.dut_ip())
        self.ip_input.setFixedWidth(130)
        h.addWidget(self.ip_input)
        root.addWidget(header)

        # Options + search in one row
        opts, o = _card()
        for text, slot, tip in (("⚡ Smoke", self.select_smoke_preset, "Tick only smoke tests in the panel shown"),
                                ("🎯 All", self.select_full_preset, "Tick every test in the panel shown"),
                                ("🧹 Clear", self.clear_selection, "Untick every test in the panel shown")):
            btn = QPushButton(text)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            o.addWidget(btn)
        o.addSpacing(12)
        o.addWidget(QLabel("Retries:"))
        self.retries_combo = QComboBox()
        self.retries_combo.addItems(["0", "1", "2"])
        o.addWidget(self.retries_combo)
        self.hw_actions_chk = QCheckBox("Allow hardware actions")
        self.hw_actions_chk.setToolTip("Also run tests that connect, apply configuration or otherwise change the tester")
        o.addWidget(self.hw_actions_chk)
        self.headless_chk = QCheckBox("Headless")
        self.headless_chk.setToolTip("Run Chrome without a visible window")
        o.addWidget(self.headless_chk)
        o.addSpacing(12)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search tests...")
        self.search_input.textChanged.connect(self.filter_tests)
        o.addWidget(self.search_input, 1)
        self.test_count_lbl = QLabel("")
        o.addWidget(self.test_count_lbl)
        root.addWidget(opts)

        # Sidebar | tests | (log / details)
        self.suites = discover_tests()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_sidebar())

        tests_panel = QWidget()
        tv = QVBoxLayout(tests_panel)
        tv.setContentsMargins(0, 0, 0, 0)
        self.panel_title_lbl = QLabel("")
        self.panel_title_lbl.setObjectName("panelTitle")
        tv.addWidget(self.panel_title_lbl)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Test Case", "Status"])
        hdr = self.tree.header()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.tree.currentItemChanged.connect(lambda cur, _prev: self.show_details(cur))
        self.populate_tree()
        tv.addWidget(self.tree)
        splitter.addWidget(tests_panel)

        right = QSplitter(Qt.Orientation.Vertical)
        right.setChildrenCollapsible(False)
        log_box = QWidget()
        lv = QVBoxLayout(log_box)
        lv.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel("LIVE LOG")
        lbl.setObjectName("sectionTitle")
        lv.addWidget(lbl)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(20000)
        self.log_view.setPlaceholderText("pytest output appears here while tests run...")
        lv.addWidget(self.log_view)
        right.addWidget(log_box)

        details_box = QWidget()
        dv = QVBoxLayout(details_box)
        dv.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel("TEST DETAILS")
        lbl.setObjectName("sectionTitle")
        dv.addWidget(lbl)
        self.details_view = QTextBrowser()
        self.details_view.setOpenLinks(False)
        self.details_view.anchorClicked.connect(lambda url: QDesktopServices.openUrl(url))
        self.details_view.setHtml("<i style='color:#94a3b8'>Select a test to see its last result.</i>")
        dv.addWidget(self.details_view, 1)
        self.screenshot_lbl = QLabel()
        self.screenshot_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshot_lbl.setMinimumHeight(0)
        self.screenshot_lbl.setVisible(False)
        self.screenshot_lbl.setFixedHeight(175)
        dv.addWidget(self.screenshot_lbl)
        right.addWidget(details_box)
        right.setSizes([260, 360])
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 2)
        root.addWidget(splitter, 1)
        self.splitter = splitter

        # Run controls
        bottom, b = _card()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        b.addWidget(self.progress_bar, 1)
        self.run_btn = QPushButton("▶ Run Selected")
        self.run_btn.setObjectName("runBtn")
        self.run_btn.setToolTip("Run the ticked tests of the panel shown")
        self.run_btn.clicked.connect(self.on_run_clicked)
        b.addWidget(self.run_btn)
        self.run_all_btn = QPushButton("⏩ Run All")
        self.run_all_btn.setObjectName("runAllBtn")
        self.run_all_btn.setToolTip("Run every test of every panel")
        self.run_all_btn.clicked.connect(self.on_run_all_clicked)
        b.addWidget(self.run_all_btn)
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setToolTip("Stop the running tests (browser closes; no report for a stopped run)")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        b.addWidget(self.stop_btn)
        self.open_report_btn = QPushButton("📂 Open Report")
        self.open_report_btn.setToolTip("Open the report folder of the last run")
        self.open_report_btn.setEnabled(False)
        self.open_report_btn.clicked.connect(self.open_last_report)
        b.addWidget(self.open_report_btn)
        root.addWidget(bottom)

        self.show_panel(None)

    def _fit_to_screen(self) -> None:
        """Opens at a size that fits the available screen area (taskbar excluded)."""
        self.setMinimumSize(900, 560)
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(1280, 800)
            return
        avail = screen.availableGeometry()
        width = min(1400, int(avail.width() * 0.92))
        height = min(900, int(avail.height() * 0.90))
        self.resize(width, height)
        self.move(avail.x() + (avail.width() - width) // 2, avail.y() + (avail.height() - height) // 2)

    def _build_sidebar(self) -> QScrollArea:
        """One button per panel (plus 'All Panels'); scrolls instead of forcing the window taller."""
        inner = QWidget()
        inner.setObjectName("sidebarInner")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        self.panel_buttons = QButtonGroup(self)
        self.panel_buttons.setExclusive(True)
        entries = [(None, "All Panels", sum(len(s.tests) for s in self.suites))]
        entries += [(i, s.short_name, len(s.tests)) for i, s in enumerate(self.suites)]
        self._panel_button_by_index = {}
        for index, name, count in entries:
            btn = QPushButton(f"{name}  ({count})")
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _=False, i=index: self.show_panel(i))
            self.panel_buttons.addButton(btn)
            self._panel_button_by_index[index] = btn
            layout.addWidget(btn)
        layout.addStretch()
        area = QScrollArea()
        area.setObjectName("sidebar")
        area.setWidget(inner)
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        area.setFixedWidth(220)
        return area

    # ------------------------------------------------------------------
    # Panels & tree
    # ------------------------------------------------------------------

    def show_panel(self, index: int | None) -> None:
        """Shows one panel's tests (None = all panels)."""
        self.current_panel = index
        self._panel_button_by_index[index].setChecked(True)
        self.panel_title_lbl.setText("All Panels" if index is None else self.suites[index].title)
        self.filter_tests(self.search_input.text())

    def populate_tree(self):
        self.tree.clear()
        self._items_by_node: dict[str, QTreeWidgetItem] = {}
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
            self.tree.addTopLevelItem(suite_item)
        self.reset_statuses()
        self.tree.expandAll()

    def reset_statuses(self):
        self.results.clear()
        for item in self._test_items():
            markers = item.data(0, Qt.ItemDataRole.UserRole)[1]
            item.setText(1, "Ready · changes tester" if "hardware" in markers else "Ready")
            item.setForeground(1, QColor("#94a3b8"))

    def _test_items(self):
        for i in range(self.tree.topLevelItemCount()):
            suite = self.tree.topLevelItem(i)
            for j in range(suite.childCount()):
                yield suite.child(j)

    def _shown_test_items(self):
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
        visible = 0
        panel = getattr(self, "current_panel", None)
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            if panel is not None and parent.data(0, Qt.ItemDataRole.UserRole) != panel:
                parent.setHidden(True)
                continue
            parent_match = text in parent.text(0).lower()
            any_child = False
            for j in range(parent.childCount()):
                child = parent.child(j)
                fn_name = child.data(0, Qt.ItemDataRole.UserRole)[0].rsplit("::", 1)[-1].lower()
                match = parent_match or text in child.text(0).lower() or text in fn_name
                child.setHidden(not match)
                any_child |= match
                visible += match
            parent.setHidden(not (parent_match or any_child))
        self.test_count_lbl.setText(f"{visible} tests")

    # ------------------------------------------------------------------
    # Live results (called by the controller)
    # ------------------------------------------------------------------

    def set_test_status(self, node_id: str, status: str):
        """Parametrised cases roll up into one row: the worst outcome wins."""
        item = self._items_by_node.get(node_id.split("[", 1)[0])
        if item is None:
            return
        current = item.text(1)
        if "[" in node_id and current in STATUS_RANK and status != "RUNNING":
            if STATUS_RANK[current] > STATUS_RANK.get(status, 0):
                return
        item.setText(1, status)
        item.setForeground(1, QColor(STATUS_COLORS.get(status, "#f8fafc")))

    def record_result(self, event: dict[str, Any]) -> None:
        base = event["nodeid"].split("[", 1)[0]
        entries = self.results.setdefault(base, [])
        existing = next((e for e in entries if e["nodeid"] == event["nodeid"]), None)
        if existing:
            existing.update({k: v for k, v in event.items() if v})
        else:
            entries.append(dict(event))
        if "result" in event:
            self.set_test_status(event["nodeid"], event["result"])
        if self.tree.currentItem() is self._items_by_node.get(base):
            self.show_details(self.tree.currentItem())

    def mark_unfinished_as_stopped(self) -> None:
        for item in self._test_items():
            if item.text(1) == "RUNNING":
                item.setText(1, "STOPPED")
                item.setForeground(1, QColor(STATUS_COLORS["STOPPED"]))

    def show_details(self, item: QTreeWidgetItem | None) -> None:
        self.screenshot_lbl.setVisible(False)
        if item is None or item.parent() is None:
            self.details_view.setHtml("<i style='color:#94a3b8'>Select a test to see its last result.</i>")
            return
        node_id, markers = item.data(0, Qt.ItemDataRole.UserRole)
        parts = [f"<b style='font-size:14px'>{html.escape(item.text(0))}</b><br>",
                 f"<span style='color:#94a3b8'>{html.escape(node_id)}<br>Tags: "
                 f"{html.escape(', '.join(sorted(markers)) or '-')}</span>"]
        entries = self.results.get(node_id, [])
        if not entries:
            parts.append("<p style='color:#94a3b8'>Not run in this session.</p>")
        shot = ""
        for e in entries:
            res = e.get("result", "RUNNING")
            color = STATUS_COLORS.get(res, "#f8fafc")
            label = e["nodeid"].split("[", 1)[1].rstrip("]") if "[" in e["nodeid"] else ""
            parts.append(f"<p><b style='color:{color}'>{res}</b> {html.escape(label)} "
                         f"<span style='color:#94a3b8'>{e.get('duration', '')}s</span></p>")
            if e.get("message"):
                parts.append(f"<pre style='color:#fca5a5;white-space:pre-wrap'>{html.escape(e['message'][-3000:])}</pre>")
            for key in ("screenshot", "trace"):
                if e.get(key):
                    url = QUrl.fromLocalFile(e[key]).toString()
                    parts.append(f"<a style='color:#60a5fa' href='{url}'>Open {key}</a> &nbsp;")
            shot = e.get("screenshot") or shot
        self.details_view.setHtml("".join(parts))
        if shot and Path(shot).exists():
            pix = QPixmap(shot)
            if not pix.isNull():
                self.screenshot_lbl.setPixmap(pix.scaled(max(200, self.details_view.width()), 170,
                                                         Qt.AspectRatioMode.KeepAspectRatio,
                                                         Qt.TransformationMode.SmoothTransformation))
                self.screenshot_lbl.setVisible(True)

    def append_log(self, line: str) -> None:
        self.log_view.appendPlainText(line)

    # ------------------------------------------------------------------
    # Run controls
    # ------------------------------------------------------------------

    def on_run_clicked(self):
        if self.controller:
            self.controller.start_execution(self.selected_node_ids())

    def on_run_all_clicked(self):
        if self.controller:
            self.controller.start_execution(self.all_node_ids())

    def on_stop_clicked(self):
        if self.controller:
            self.controller.stop()

    def set_running(self, running: bool) -> None:
        self.run_btn.setEnabled(not running)
        self.run_all_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)

    def set_last_report_dir(self, folder: str) -> None:
        self.last_report_dir = folder
        self.open_report_btn.setEnabled(bool(folder))
        self.open_report_btn.setToolTip(folder or "Open the report folder of the last run")

    def open_last_report(self) -> None:
        if self.last_report_dir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_report_dir))

    def update_backend_status(self):
        try:
            from Scripts.Helpers.api_client import c2_api
            if not c2_api.is_online():
                self.backend_status_lbl.setText("C2 backend offline")
                self.backend_status_lbl.setStyleSheet(PILL_BAD)
                return
            ver = c2_api.get_software_version()
            tester = c2_api.get_connection_info().get("testerStatus") or "unknown"
            self.backend_status_lbl.setText(f"C2 v{ver} | Tester: {tester}")
            self.backend_status_lbl.setStyleSheet(PILL_OK if tester == "Connected" else PILL_WARN)
        except Exception:
            self.backend_status_lbl.setText("C2 backend offline")
            self.backend_status_lbl.setStyleSheet(PILL_BAD)

    # ------------------------------------------------------------------
    # Persisted settings
    # ------------------------------------------------------------------

    def _restore_settings(self) -> None:
        s = self.settings
        if s.value("ip"):
            self.ip_input.setText(str(s.value("ip")))
        self.retries_combo.setCurrentText(str(s.value("retries", "0")))
        self.hw_actions_chk.setChecked(s.value("hw_actions", False, type=bool))
        self.headless_chk.setChecked(s.value("headless", False, type=bool))
        unchecked = set(s.value("unchecked", [], type=list) or [])
        for item in self._test_items():
            if item.data(0, Qt.ItemDataRole.UserRole)[0] in unchecked:
                item.setCheckState(0, Qt.CheckState.Unchecked)
        panel = s.value("panel", -1, type=int)
        self.show_panel(panel if 0 <= panel < len(self.suites) else None)
        geometry = s.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

    def save_settings(self) -> None:
        s = self.settings
        s.setValue("ip", self.ip_input.text().strip())
        s.setValue("retries", self.retries_combo.currentText())
        s.setValue("hw_actions", self.hw_actions_chk.isChecked())
        s.setValue("headless", self.headless_chk.isChecked())
        s.setValue("unchecked", [item.data(0, Qt.ItemDataRole.UserRole)[0] for item in self._test_items()
                                 if item.checkState(0) == Qt.CheckState.Unchecked])
        s.setValue("panel", -1 if self.current_panel is None else self.current_panel)
        s.setValue("geometry", self.saveGeometry())

    def closeEvent(self, event):  # noqa: N802 - Qt override
        if self.controller and self.controller.is_running():
            self.controller.stop()
        self.save_settings()
        super().closeEvent(event)


# ----------------------------------------------------------------------------
# Test discovery (static, no imports of test modules)
# ----------------------------------------------------------------------------

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
    return names - {"parametrize", "xfail", "skip", "skipif", "spec"}


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
