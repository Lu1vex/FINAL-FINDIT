from PyQt6.QtGui import QColor, QFontDatabase, QPalette
from PyQt6.QtWidgets import QFrame

from dashboard import graphics


class Theme:
    # Colors
    SPRUCE = "#16302B"
    SPRUCE_SOFT = "#24463F"
    PAPER = "#EDF1EE"
    CARD = "#FFFFFF"
    LINE = "#CFD9D4"
    MUTED = "#5E6F69"
    TAG = "#F4B942"

    LOST = "#D9482B"
    FOUND = "#12877A"
    CLAIMED = "#3B4CA0"
    LOST_TINT = "#F7DDD5"
    FOUND_TINT = "#D3EEE9"
    CLAIMED_TINT = "#DADFF2"

    # Fonts (the first one that is installed is used)
    HEADING_FONTS = ["Bahnschrift", "DIN Alternate", "Trebuchet MS", "Segoe UI", "Helvetica Neue", "Arial"]
    BODY_FONTS = ["Segoe UI", "SF Pro Text", "Helvetica Neue", "Noto Sans", "Arial"]

    # Makes the inside of a scroll area see-through
    TRANSPARENT_SCROLL = ("QScrollArea { background: transparent; border: none; }"
                          "QScrollArea > QWidget > QWidget { background: transparent; }")


def pick_font(names):
    installed = QFontDatabase.families()
    for name in names:
        if name in installed:
            return name
    return names[-1]


def dashed_divider():
    line = QFrame()
    line.setFixedHeight(2)
    line.setStyleSheet(f"border: none; border-top: 2px dashed {Theme.LINE}; background: transparent;")
    return line


def fit_combo(combo, extra=70):
    widest = 0
    for i in range(combo.count()):
        widest = max(widest, combo.fontMetrics().horizontalAdvance(combo.itemText(i)))
    combo.setMinimumWidth(widest + extra)
    combo.view().setMinimumWidth(widest + extra)


def light_palette():
    palette = QPalette()
    colors = {
        QPalette.ColorRole.Window: Theme.PAPER,
        QPalette.ColorRole.WindowText: Theme.SPRUCE,
        QPalette.ColorRole.Base: "#FFFFFF",
        QPalette.ColorRole.AlternateBase: "#F6F9F7",
        QPalette.ColorRole.Text: Theme.SPRUCE,
        QPalette.ColorRole.Button: "#FFFFFF",
        QPalette.ColorRole.ButtonText: Theme.SPRUCE,
        QPalette.ColorRole.ToolTipBase: Theme.SPRUCE,
        QPalette.ColorRole.ToolTipText: "#FFFFFF",
        QPalette.ColorRole.Highlight: Theme.TAG,
        QPalette.ColorRole.HighlightedText: Theme.SPRUCE,
        QPalette.ColorRole.PlaceholderText: "#8A9A94",
    }
    for role, color in colors.items():
        palette.setColor(role, QColor(color))
    return palette


def make_stylesheet():
    T = Theme
    heading = pick_font(T.HEADING_FONTS)
    body = pick_font(T.BODY_FONTS)
    arrow = (graphics.ART_DIR / "arrow_down.png").as_posix()
    return f"""
* {{ font-family: "{body}"; }}
QMainWindow, QWidget#root, QDialog {{ background: {T.PAPER}; }}
QLabel {{ color: {T.SPRUCE}; }}
QToolTip {{ background: {T.SPRUCE}; color: white; border: none; padding: 5px 8px; }}

QLabel#pageTitle {{ font-family: "{heading}"; font-size: 30px; font-weight: 700; }}
QLabel#pageSub {{ color: {T.MUTED}; font-size: 14px; }}
QLabel#h1 {{ font-family: "{heading}"; font-size: 30px; font-weight: 700; }}
QLabel#h2 {{ font-family: "{heading}"; font-size: 20px; font-weight: 700; }}
QLabel#formTitle {{ font-family: "{heading}"; font-size: 22px; font-weight: 700; }}
QLabel#fieldLabel {{ color: {T.MUTED}; font-size: 12px; font-weight: 600; }}
QLabel#hint {{ color: {T.MUTED}; font-size: 13px; }}

QFrame#sidebar {{ background: {T.SPRUCE}; }}
QFrame#sideHeader, QFrame#topbar {{ background: transparent; }}
QFrame#footer {{ background: transparent; border-top: 1px solid {T.LINE}; }}
QLabel#brand {{ font-family: "{heading}"; font-size: 24px; font-weight: 700; color: white; }}
QLabel#tagline {{ color: #9DB5AE; font-size: 11px; }}
QPushButton#nav {{ background: transparent; color: #C9D8D3; text-align: left; padding: 11px 14px;
    border-radius: 8px; font-size: 14px; font-weight: 500; }}
QPushButton#nav:hover {{ background: {T.SPRUCE_SOFT}; color: white; }}
QPushButton#nav:checked {{ background: {T.TAG}; color: {T.SPRUCE}; font-weight: 700; }}
QPushButton#icon {{ background: transparent; border-radius: 8px; padding: 6px; }}
QPushButton#icon:hover {{ background: white; }}

QFrame#panel {{ background: {T.CARD}; border: 1px solid {T.LINE}; border-radius: 12px; }}
QFrame#hero {{ background: {T.SPRUCE}; border-radius: 14px; }}
QFrame#tipCard {{ background: {T.SPRUCE}; border-radius: 16px; }}
QFrame#recentRow {{ background: #F6F9F7; border-radius: 10px; }}
QFrame#recentRow:hover {{ background: #FBE7B5; }}

QLineEdit, QComboBox, QDateEdit, QTextEdit {{ background: white; border: 1px solid {T.LINE};
    border-radius: 8px; padding: 7px 9px; color: {T.SPRUCE}; font-size: 14px;
    selection-background-color: {T.TAG}; selection-color: {T.SPRUCE}; }}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {{ border: 2px solid {T.SPRUCE}; }}
QComboBox, QDateEdit {{ min-height: 22px; padding-right: 34px; }}
QComboBox::drop-down, QDateEdit::drop-down {{ subcontrol-origin: padding; subcontrol-position: center right;
    width: 30px; border: none; }}
QComboBox::down-arrow, QDateEdit::down-arrow {{ image: url("{arrow}"); width: 12px; height: 12px; }}
QComboBox QAbstractItemView {{ background: white; color: {T.SPRUCE}; border: 1px solid {T.LINE}; outline: 0;
    padding: 4px; selection-background-color: {T.TAG}; selection-color: {T.SPRUCE}; }}
QComboBox QAbstractItemView::item {{ min-height: 30px; padding: 4px 8px; color: {T.SPRUCE}; background: white; }}
QComboBox QAbstractItemView::item:hover {{ background: #FBE7B5; }}
QComboBox QAbstractItemView::item:selected {{ background: {T.TAG}; }}
QCalendarWidget QWidget, QCalendarWidget QAbstractItemView {{ color: {T.SPRUCE}; background: white;
    selection-background-color: {T.TAG}; selection-color: {T.SPRUCE}; }}
QCalendarWidget QToolButton {{ color: {T.SPRUCE}; background: transparent; }}

QPushButton {{ background: {T.SPRUCE}; color: white; border: none; border-radius: 8px;
    padding: 10px 18px; font-weight: 600; }}
QPushButton:hover {{ background: {T.SPRUCE_SOFT}; }}
QPushButton:disabled {{ background: #E3EAE6; color: #9DB0A9; }}
QPushButton#ghost {{ background: white; color: {T.SPRUCE}; border: 1px solid {T.LINE}; }}
QPushButton#ghost:hover {{ border-color: {T.SPRUCE}; }}
QPushButton#danger {{ background: white; color: {T.LOST}; border: 1px solid {T.LOST_TINT}; }}
QPushButton#danger:hover {{ background: {T.LOST_TINT}; }}
QPushButton#saveLost {{ background: {T.LOST}; }}
QPushButton#saveLost:hover {{ background: #B93A21; }}
QPushButton#saveFound {{ background: {T.FOUND}; }}
QPushButton#saveFound:hover {{ background: #0E6B61; }}

QTableWidget {{ background: white; alternate-background-color: #F6F9F7; border: 1px solid {T.LINE};
    border-radius: 12px; gridline-color: transparent; outline: 0; }}
QTableWidget::item {{ padding: 6px; border: none; }}
QTableWidget::item:selected {{ background: #FBE7B5; color: {T.SPRUCE}; }}
QHeaderView::section {{ background: #E3EAE6; color: {T.SPRUCE}; padding: 9px 8px; border: none;
    border-bottom: 1px solid {T.LINE}; font-weight: 700; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {T.LINE}; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QLabel#tagValue {{ font-family: "{heading}"; font-size: 40px; font-weight: 700; }}
QLabel#tagCaption {{ color: {T.MUTED}; font-size: 14px; }}
QLabel#stepNum {{ background: {T.TAG}; color: {T.SPRUCE}; border-radius: 17px;
    font-family: "{heading}"; font-size: 16px; font-weight: 700; }}
QLabel#stepTitle {{ font-family: "{heading}"; font-size: 17px; font-weight: 700; }}
QLabel#sideTitle {{ font-family: "{heading}"; font-size: 20px; font-weight: 700; color: white; }}
QLabel#sideTip {{ color: #D5E3DE; font-size: 13px; }}
QLabel#rowName {{ font-size: 14px; font-weight: 700; }}
QLabel#rowMeta {{ color: {T.MUTED}; font-size: 12px; }}
QLabel#techChip {{ background: #E3EAE6; color: {T.SPRUCE}; border-radius: 12px; padding: 4px 12px; font-weight: 600; }}

QLabel#heroTitle {{ color: white; font-size: 26px; font-weight: 700; }}
QLabel#heroSub, QLabel#heroCount {{ color: #B7CBC5; font-size: 14px; }}
QLineEdit#bigSearch {{ font-size: 17px; padding: 12px 20px; border-radius: 24px; border: 2px solid white; }}
QLineEdit#bigSearch:focus {{ border: 2px solid {T.TAG}; }}
QFrame#hero QComboBox {{ min-width: 130px; border: none; }}
QFrame#resultCard {{ background: white; border: 1px solid {T.LINE}; border-radius: 10px; }}
QFrame#resultCard:hover {{ border: 1px solid {T.SPRUCE}; }}
QLabel#cardName {{ font-size: 16px; font-weight: 700; }}
QLabel#cardMeta {{ color: {T.MUTED}; }}
QLabel#chip {{ background: #E3EAE6; color: {T.MUTED}; border-radius: 9px; padding: 2px 10px; font-size: 12px; }}
QLabel#emptyTitle {{ font-size: 18px; font-weight: 700; }}
"""
