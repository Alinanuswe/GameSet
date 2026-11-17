import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QDialogButtonBox, QAbstractItemView)

from ...game import GameMode
from ...scores import Leaderboard


def _format_seconds(seconds: float) -> str:
    seconds = int(seconds)
    return f'{seconds // 60:02d}:{seconds % 60:02d}'


class LeaderboardDialog(QDialog):
    def __init__(self, leaderboard: Leaderboard, current_mode: GameMode, highlight_rank: int | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Best Scores')
        self.resize(460, 380)
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        today = datetime.date.today().isoformat()
        for mode in GameMode:
            day = today if mode is GameMode.DAILY else None
            entries = leaderboard.top(mode.value, day)
            table = QTableWidget(len(entries), 5)
            table.setHorizontalHeaderLabels(['#', 'Score', 'SETs', 'Time', 'Date'])
            table.verticalHeader().hide()
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.setSelectionMode(QAbstractItemView.NoSelection)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for row, e in enumerate(entries):
                values = [row + 1, e.score, e.sets_found, _format_seconds(e.seconds), e.date]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    if mode is current_mode and highlight_rank == row + 1:
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                    table.setItem(row, col, item)
            title = mode.label + (' (today)' if day else '')
            tabs.addTab(table, title)
            if mode is current_mode:
                tabs.setCurrentWidget(table)
        layout.addWidget(tabs)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
