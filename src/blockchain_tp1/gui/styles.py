from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


DARK_BG = "#07111f"
PANEL_BG = "#101b2d"
PANEL_ALT = "#16253d"
ACCENT = "#38bdf8"
ACCENT_2 = "#60a5fa"
SUCCESS = "#34d399"
WARNING = "#fbbf24"
DANGER = "#f87171"
TEXT = "#e5eefb"
MUTED = "#9aa9c5"
BORDER = "#24354f"


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
            color: #e5eefb;
            background-color: #07111f;
            font-family: "DejaVu Sans", sans-serif;
        }
        QWidget {
            background-color: #07111f;
            color: #e5eefb;
        }
        QMainWindow, QDialog, QFrame, QStackedWidget {
            background-color: #07111f;
        }
        #sidebar {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #111f32, stop:1 #0b1523);
            border: 1px solid #24354f;
        }
        #card, #panel {
            background-color: #101b2d;
            border: 1px solid #24354f;
            border-radius: 12px;
        }
        QListWidget {
            background: transparent;
            border: none;
            outline: none;
            padding: 4px;
        }
        QListWidget::item {
            border-radius: 8px;
            padding: 10px 12px;
            margin: 3px 0px;
            color: #dfeafc;
        }
        QListWidget::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1d3a5f, stop:1 #16314d);
            border: 1px solid #38bdf8;
            color: #ffffff;
        }
        QTextEdit, QComboBox, QLineEdit, QPlainTextEdit {
            background-color: #101b2d;
            color: #e5eefb;
            border: 1px solid #24354f;
            border-radius: 10px;
            padding: 8px 10px;
        }
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1a2d46, stop:1 #143556);
            border: 1px solid #38bdf8;
            border-radius: 10px;
            padding: 9px 14px;
            color: #edf6ff;
            font-weight: 600;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1e3f66, stop:1 #1a3557);
            border-color: #60a5fa;
        }
        QPushButton:pressed {
            background: #122643;
        }
        QLabel {
            color: #e5eefb;
        }
        QLabel[status="success"] { color: #34d399; }
        QLabel[status="warning"] { color: #fbbf24; }
        QLabel[status="danger"] { color: #f87171; }
        QTabBar::tab { background: #101b2d; color: #e5eefb; padding: 8px 14px; }
        QTabBar::tab:selected { background: #16253d; border: 1px solid #38bdf8; }
        QHeaderView::section {
            background: #101b2d;
            color: #e5eefb;
            border: 1px solid #24354f;
            padding: 6px;
        }
        QTableWidget {
            gridline-color: #24354f;
        }
        """
    )
