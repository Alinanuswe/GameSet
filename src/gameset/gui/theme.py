"""Light and dark colour themes for the GUI."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    window: str
    panel: str
    text: str
    muted: str
    border: str
    felt: str
    chip: str
    selected: str
    hint: str
    error: str
    success: str


LIGHT = Theme('light', window='#eef1f4', panel='#ffffff', text='#1f2933', muted='#6c757d',
              border='#d0d7de', felt='#2a4d3a', chip='#1a3d2a', selected='#0064ff',
              hint='#00b140', error='#e00000', success='#ffb000')
DARK = Theme('dark', window='#1d2125', panel='#2a2f35', text='#e6e9ec', muted='#9aa4ae',
             border='#3d444c', felt='#18241e', chip='#24382c', selected='#4d94ff',
             hint='#3ddc6f', error='#ff5050', success='#ffc233')

THEMES = {LIGHT.name: LIGHT, DARK.name: DARK}


def get_theme(name: str) -> Theme:
    return THEMES.get(name, LIGHT)


def stylesheet(t: Theme) -> str:
    return f"""
        QMainWindow, QDialog {{ background-color: {t.window}; }}
        QWidget {{ color: {t.text}; }}
        QLabel#chip {{
            color: white; background-color: {t.chip};
            padding: 5px 8px; border-radius: 3px; font-weight: bold;
        }}
        QLabel#timer {{
            color: white; background-color: {t.chip};
            padding: 8px 15px; border-radius: 5px; font-size: 12pt; font-weight: bold;
        }}
        QPushButton {{
            background-color: {t.panel}; color: {t.text};
            border: 1px solid {t.border}; border-radius: 4px; padding: 6px 12px;
        }}
        QPushButton:hover {{ border-color: {t.selected}; }}
        QPushButton:disabled {{ color: {t.muted}; }}
        QPushButton#primary {{ background-color: #28a745; color: white; border: none; font-weight: bold; }}
        QPushButton#primary:hover {{ background-color: #218838; }}
        QPushButton#accent {{ background-color: #17a2b8; color: white; border: none; font-weight: bold; }}
        QPushButton#accent:hover {{ background-color: #138496; }}
        QComboBox, QTableWidget, QTabWidget::pane {{
            background-color: {t.panel}; color: {t.text}; border: 1px solid {t.border};
        }}
        QHeaderView::section {{ background-color: {t.window}; color: {t.text}; border: none; padding: 4px; }}
        QGroupBox {{
            font-weight: bold; border: 1px solid {t.border}; border-radius: 5px;
            margin-top: 10px; padding-top: 10px;
        }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
        QFrame#sidebar, QScrollArea#history {{
            background-color: {t.panel}; border: 1px solid {t.border}; border-radius: 6px;
        }}
        QWidget#historyContents {{ background-color: {t.panel}; }}
        QStatusBar {{ color: {t.text}; font-weight: bold; }}
    """
