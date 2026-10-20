"""FINDIT - Find what matters. Run this file: python main.py"""
import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from dashboard.dashboard import Dashboard
from dashboard.theme import Theme, light_palette, make_stylesheet, pick_font
from database.database import Database


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # same look on every system
    app.setPalette(light_palette())
    app.setFont(QFont(pick_font(Theme.BODY_FONTS), 10))
    app.setStyleSheet(make_stylesheet())
    window = Dashboard(Database())
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
