from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import QApplication

from blockchain_tp1.gui.main_window import MainWindow


def test_gui_main_window_builds():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    assert window is not None
    assert window.app_title.text() == "Dashboard"
