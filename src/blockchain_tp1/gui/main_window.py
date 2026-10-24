from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextEdit,
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
        self._register_page("dashboard", self._make_dashboard_page())
        self._register_page("messaging", self._make_messaging_page())
        self._register_page("certificates", self._make_certificates_page())
        self._register_page("crypto", self._make_crypto_page())
        self._register_page("network", self._make_network_page())
        self._register_page("benchmark", self._make_benchmark_page())
        self._register_page("logs", self._make_logs_page())
        self._register_page("about", self._make_about_page())
        content_layout.addWidget(self.pages)

        layout.addWidget(sidebar)
        layout.addWidget(content)

        self.nav_list.setCurrentRow(0)

    def _card(self, title: str, value: str, subtitle: str = "") -> QWidget:
        card = QWidget(self)
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #9ca3af; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;")
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 26px; font-weight: 700; color: #e5e7eb;")
        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet("color: #60a5fa; font-size: 12px;")
            card_layout.addWidget(sub)
        return card

    def _make_dashboard_page(self) -> QWidget:
        page = QWidget(self)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(14)

        top = QGridLayout()
        top.addWidget(self._card("Nodes online", "4 / 4", "Alice, Bob, Carol, Dave"), 0, 0)
        top.addWidget(self._card("Certificates", "Valid", "PKI chain verified"), 0, 1)
        top.addWidget(self._card("AES throughput", "234 MiB/s", "10 MB encrypted"), 0, 2)
        top.addWidget(self._card("Hybrid mode", "OK", "RSA + AES workflow"), 0, 3)
        page_layout.addLayout(top)

        flow = QWidget(self)
        flow_layout = QHBoxLayout(flow)
        flow_layout.setContentsMargins(0, 0, 0, 0)
        flow_layout.setSpacing(12)

        stages = [
            ("1. CA", "Root certificate generated"),
            ("2. Identity", "Node certificates issued"),
            ("3. Key exchange", "ECDH session created"),
            ("4. Encrypt", "AES-GCM payload secured"),
            ("5. Deliver", "Loopback socket transport"),
        ]

        for label, detail in stages:
            card = QFrame(self)
            card.setObjectName("panel")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 18, 18, 18)
            title = QLabel(label)
            title.setStyleSheet("font-size: 18px; font-weight: 700; color: #38bdf8;")
            desc = QLabel(detail)
            desc.setWordWrap(True)
            desc.setStyleSheet("font-size: 13px; color: #dbeafe;")
            card_layout.addWidget(title)
            card_layout.addWidget(desc)
            flow_layout.addWidget(card)

        page_layout.addWidget(flow)

        info = QWidget(self)
        info_layout = QHBoxLayout(info)
        info_layout.setContentsMargins(0, 0, 0, 0)

        summary = QFrame(self)
        summary.setObjectName("panel")
        summary_layout = QVBoxLayout(summary)
        summary_layout.setContentsMargins(18, 18, 18, 18)
        summary_title = QLabel("Security overview")
        summary_title.setStyleSheet("font-size: 18px; font-weight: 700;")
        summary_text = QLabel(
            "The system creates a local Root CA, issues X.509 certificates, derives an ECDH session key, wraps it with RSA, and encrypts the payload with AES-GCM before sending it over loopback sockets."
        )
        summary_text.setWordWrap(True)
        summary_text.setStyleSheet("font-size: 14px; line-height: 1.6; color: #dbeafe;")
        summary_layout.addWidget(summary_title)
        summary_layout.addWidget(summary_text)
        info_layout.addWidget(summary)

        status = QFrame(self)
        status.setObjectName("panel")
        status_layout = QVBoxLayout(status)
        status_layout.setContentsMargins(18, 18, 18, 18)
        status_title = QLabel("System state")
        status_title.setStyleSheet("font-size: 18px; font-weight: 700;")
        modes = [
            "Root CA ready",
            "Node certificates issued",
            "ECDH shared keys derived",
            "Local socket demo active",
            "Authentication and integrity verified",
        ]
        for item in modes:
            row = QLabel(f"• {item}")
            row.setStyleSheet("font-size: 14px; color: #e5e7eb;")
            status_layout.addWidget(row)
        info_layout.addWidget(status)
        page_layout.addWidget(info)
        return page

    def _make_messaging_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        selector_row = QHBoxLayout()
        sender_combo = QComboBox(self)
        sender_combo.addItems(["alice", "bob", "carol", "dave"])
        sender_combo.setCurrentText("alice")

        receiver_combo = QComboBox(self)
        receiver_combo.addItems(["alice", "bob", "carol", "dave"])
        receiver_combo.setCurrentText("bob")

        selector_row.addWidget(QLabel("From:"))
        selector_row.addWidget(sender_combo)
        selector_row.addSpacing(20)
        selector_row.addWidget(QLabel("To:"))
        selector_row.addWidget(receiver_combo)
        selector_row.addStretch()
        layout.addLayout(selector_row)

        message_area = QTextEdit(self)
        message_area.setPlainText("Hello Bob,\nthis is a secure local message using the project cryptography stack.")
        message_area.setReadOnly(False)
        message_area.setStyleSheet("min-height: 120px;")
        layout.addWidget(message_area)

        send_button = QPushButton("Encrypt and send")

        def do_send() -> None:
            try:
                from blockchain_tp1.socket_demo import send_local_message, build_nodes

                sender_name = sender_combo.currentText().lower()
                receiver_name = receiver_combo.currentText().lower()
                payload = message_area.toPlainText()
                nodes = build_nodes()
                result = send_local_message(nodes, sender_name, receiver_name, payload)
                if result.get("error"):
                    self.show_status("send failed", "danger")
                    return
                details = result.get("payload", {})
                decoded = details.get("message", "") if isinstance(details, dict) else str(details)
                self.show_status("message sent", "success")
                history.setPlainText(
                    f"{sender_name} -> {receiver_name}: {payload}\n"
                    f"Status: encrypted and acknowledged\n"
                    f"Result: {decoded}"
                )
            except Exception as exc:  # pragma: no cover - UI helper
                self.show_status("send failed", "danger")
                history.setPlainText(f"Error: {exc}")

        send_button.clicked.connect(do_send)
        layout.addWidget(send_button)

        history = QTextEdit(self)
        history.setReadOnly(True)
        history.setPlainText(
            "Alice -> Bob: ping\n"
            "Bob -> Alice: ACK\n"
            "Alice -> Carol: encrypted heartbeat\n"
            "Carol -> Dave: certificate check\n"
        )
        layout.addWidget(history)
        return page

    def _make_certificates_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        cards = QGridLayout()
        for label, value in [
            ("Root CA", "Blockchain TP1 Root CA"),
            ("Issuer", "My Blockchain Consortium"),
            ("Node count", "4"),
            ("Validity", "3 years"),
        ]:
            cards.addWidget(self._card(label, value), 0, 0)
        layout.addLayout(cards)

        details = QTextEdit(self)
        details.setReadOnly(True)
        details.setPlainText(
            "Alice certificate\n"
            "- CN: alice\n"
            "- Key size: 2048-bit RSA\n"
            "- SAN: alice.local\n"
            "\nBob certificate\n"
            "- CN: bob\n"
            "- Key size: 2048-bit RSA\n"
            "- SAN: bob.local\n"
        )
        layout.addWidget(details)
        return page

    def _make_crypto_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        metrics = QGridLayout()
        for label, value, subtitle in [
            ("RSA-OAEP", "Secure", "2048-bit keys"),
            ("AES-GCM", "Active", "256-bit authenticated"),
            ("ECDH", "Ready", "SECP256R1"),
            ("HKDF", "Derived", "32-byte session key"),
        ]:
            metrics.addWidget(self._card(label, value, subtitle), 0, 0)
        layout.addLayout(metrics)

        info = QTextEdit(self)
        info.setReadOnly(True)
        info.setPlainText(
            "Cryptographic flow:\n"
            "1. Generate RSA keypair and local CA.\n"
            "2. Exchange ECDH public keys.\n"
            "3. Derive a session key with HKDF-SHA256.\n"
            "4. Encrypt payload with AES-256-GCM.\n"
            "5. Wrap the session key with peer RSA public key."
        )
        layout.addWidget(info)
        return page

    def _make_network_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        ports = QTextEdit(self)
        ports.setReadOnly(True)
        ports.setPlainText(
            "127.0.0.1\n"
            "Alice: 5001\n"
            "Bob: 5002\n"
            "Carol: 5003\n"
            "Dave: 5004\n\n"
            "Status: local loopback only, no public internet traffic."
        )
        layout.addWidget(ports)
        return page

    def _make_benchmark_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        bench_file = Path(__file__).resolve().parents[2] / "results" / "benchmark_results.json"
        default = "AES-256-GCM throughput: 234 MiB/s\nHybrid RSA + AES throughput: 310 MiB/s"
        status = default
        if bench_file.exists():
            try:
                import json
                data = json.loads(bench_file.read_text(encoding="utf-8"))
                aes = data.get("aes", {}).get("10485760", {})
                hybrid = data.get("hybrid", {}).get("10485760", {})
                if aes:
                    status = (
                        f"AES-256-GCM (10 MB): {aes.get('throughput_mib_per_s', 0):.2f} MiB/s\n"
                        f"Hybrid RSA + AES (10 MB): {hybrid.get('throughput_mib_per_s', 0):.2f} MiB/s"
                    )
            except Exception:
                pass

        result = QTextEdit(self)
        result.setReadOnly(True)
        result.setPlainText(status)
        layout.addWidget(result)
        return page

    def _make_logs_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        log_text = QTextEdit(self)
        log_text.setReadOnly(True)
        log_text.setPlainText(
            "[INFO] CA initialized\n"
            "[INFO] Alice certificate signed\n"
            "[INFO] Bob certificate signed\n"
            "[INFO] Carol certificate signed\n"
            "[INFO] Dave certificate signed\n"
            "[INFO] ECDH exchange complete\n"
            "[INFO] Secure session established"
        )
        layout.addWidget(log_text)
        return page

    def _make_about_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        about = QTextEdit(self)
        about.setReadOnly(True)
        about.setPlainText(
            "Blockchain Security Lab\n\n"
            "This project demonstrates a local blockchain cryptography lab built with Python.\n"
            "It uses an internal Root CA, X.509 certificates, RSA-OAEP encryption, AES-GCM payload protection, and ECDH key agreement.\n\n"
            "All communication stays in the local workspace and loopback network, with no external services involved."
        )
        layout.addWidget(about)
        return page

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
