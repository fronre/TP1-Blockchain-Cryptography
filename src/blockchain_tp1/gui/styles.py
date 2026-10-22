from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


DARK_BG = "#0f172a"
PANEL_BG = "#111827"
PANEL_ALT = "#1f2937"
ACCENT = "#38bdf8"
ACCENT_2 = "#60a5fa"
SUCCESS = "#22c55e"
WARNING = "#fbbf24"
DANGER = "#ef4444"
TEXT = "#e5e7eb"
MUTED = "#9ca3af"
BORDER = "#374151"


def apply_theme(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(DARK_BG))
    palette.setColor(QPalette.WindowText, QColor(TEXT))
    palette.setColor(QPalette.Base, QColor(PANEL_BG))
    palette.setColor(QPalette.AlternateBase, QColor(PANEL_ALT))
    palette.setColor(QPalette.ToolTipBase, QColor(PANEL_ALT))
    palette.setColor(QPalette.ToolTipText, QColor(TEXT))
    palette.setColor(QPalette.Text, QColor(TEXT))
    palette.setColor(QPalette.Button, QColor(PANEL_BG))
    palette.setColor(QPalette.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.Light, QColor(BORDER))
    palette.setColor(QPalette.Midlight, QColor(PANEL_ALT))
    palette.setColor(QPalette.Dark, QColor(BORDER))
    palette.setColor(QPalette.Mid, QColor(PANEL_ALT))
    palette.setColor(QPalette.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    app.setStyleSheet(
        """
        * {
            color: #e5e7eb;
            background-color: #0f172a;
            font-family: "DejaVu Sans", sans-serif;
        }
        QWidget {
            background-color: #0f172a;
            color: #e5e7eb;
        }
        QMainWindow, QDialog, QFrame, QStackedWidget {
            background-color: #0f172a;
        }
        QSidebar {
            background-color: #111827;
            border: 1px solid #374151;
        }
        QPushButton {
            background-color: #111827;
            border: 1px solid #374151;
            border-radius: 8px;
            padding: 8px 12px;
            color: #e5e7eb;
        }
        QPushButton:hover {
            border-color: #38bdf8;
            color: #dbeafe;
        }
        QPushButton:pressed {
            background-color: #1f2937;
        }
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QTableWidget, QListWidget {
            background-color: #111827;
            color: #e5e7eb;
            border: 1px solid #374151;
            border-radius: 8px;
            padding: 6px 8px;
        }
        QLabel {
            color: #e5e7eb;
        }
        QLabel[status="success"] { color: #22c55e; }
        QLabel[status="warning"] { color: #fbbf24; }
        QLabel[status="danger"] { color: #ef4444; }
        QTabBar::tab { background: #111827; color: #e5e7eb; padding: 8px 14px; }
        QTabBar::tab:selected { background: #1f2937; border: 1px solid #38bdf8; }
        QHeaderView::section {
            background: #111827;
            color: #e5e7eb;
            border: 1px solid #374151;
            padding: 6px;
        }
        QTableWidget {
            gridline-color: #374151;
        }
        """
    )
