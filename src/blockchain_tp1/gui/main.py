from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from blockchain_tp1.gui.main_window import MainWindow
from blockchain_tp1.gui.styles import apply_theme


def main() -> None:
    app = QApplication(sys.argv)
    apply_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
