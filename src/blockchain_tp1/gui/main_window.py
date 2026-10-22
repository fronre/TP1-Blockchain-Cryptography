from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .styles import apply_theme


class SidebarButton(QPushButton):
    def __init__(self, text: str, page_name: str):
        super().__init__(text)
        self.page_name = page_name


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blockchain Security Lab")
        self.resize(1200, 750)
        self._build_ui()

    def _build_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QWidget(self)
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(10)

        title = QLabel("Blockchain Security Lab")
        title.setStyleSheet("font-size: 18px; font-weight: 700; margin-bottom: 8px;")
        sidebar_layout.addWidget(title)

        self.nav_items = [
            ("Dashboard", "dashboard"),
            ("Secure Messaging", "messaging"),
            ("Certificates & PKI", "certificates"),
            ("Cryptography Lab", "crypto"),
            ("Network Monitor", "network"),
            ("Benchmark", "benchmark"),
            ("Logs & Diagnostics", "logs"),
            ("About Project", "about"),
        ]

        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(220)
        self.nav_list.setAlternatingRowColors(False)
        for label, page_name in self.nav_items:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, page_name)
            self.nav_list.addItem(item)
        self.nav_list.currentRowChanged.connect(self._switch_page)
        sidebar_layout.addWidget(self.nav_list)
        sidebar_layout.addStretch()

        content = QWidget(self)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(12)

        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        self.app_title = QLabel("Dashboard")
        self.app_title.setStyleSheet("font-size: 22px; font-weight: 700;")
        self.status_label = QLabel("System status: ready")
        self.status_label.setProperty("status", "success")
        self.status_label.setStyleSheet("font-weight: 600;")
        header_layout.addWidget(self.app_title)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        content_layout.addWidget(header)

        self.pages = QStackedWidget(self)
        self.page_widgets = {}
        self._register_page("dashboard", self._make_placeholder("Dashboard"))
        self._register_page("messaging", self._make_placeholder("Secure Messaging"))
        self._register_page("certificates", self._make_placeholder("Certificates & PKI"))
        self._register_page("crypto", self._make_placeholder("Cryptography Lab"))
        self._register_page("network", self._make_placeholder("Network Monitor"))
        self._register_page("benchmark", self._make_placeholder("Benchmark"))
        self._register_page("logs", self._make_placeholder("Logs & Diagnostics"))
        self._register_page("about", self._make_placeholder("About Project"))
        content_layout.addWidget(self.pages)

        layout.addWidget(sidebar)
        layout.addWidget(content)

        self.nav_list.setCurrentRow(0)

    def _make_placeholder(self, title: str):
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        label = QLabel(f"{title} page is active. Integration with the existing backend is in progress.")
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 16px; color: #dbeafe;")
        layout.addWidget(label)
        return panel

    def _register_page(self, key: str, widget: QWidget):
        self.page_widgets[key] = widget
        self.pages.addWidget(widget)

    def _switch_page(self, row: int):
        if row < 0:
            return
        page_name = self.nav_items[row][1]
        self.app_title.setText(self.nav_items[row][0])
        self.pages.setCurrentWidget(self.page_widgets[page_name])

    def show_status(self, message: str, color_name: str = "success"):
        self.status_label.setText(f"System status: {message}")
        self.status_label.setProperty("status", color_name)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def show_message(self, title: str, text: str):
        QMessageBox.information(self, title, text)
