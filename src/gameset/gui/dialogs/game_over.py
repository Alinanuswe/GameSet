from PySide6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from ...game import Player

# Result codes for exec()
CLOSE, NEW_GAME, SHOW_SCORES = 0, 1, 2


class GameOverDialog(QDialog):
    def __init__(self, stats: dict, rank: int | None, time_up: bool, parent=None,
                 ranking: list[Player] | None = None, can_restart: bool = True):
        """With a ranking (multiplayer), shows the players' results instead of personal statistics."""
        super().__init__(parent)
        self.setWindowTitle('Game Over')
        layout = QVBoxLayout(self)
        if ranking:
            self._multiplayer(layout, stats, ranking, time_up)
            self._buttons(layout, can_restart, show_scores=False)
            return

        heading = QLabel("Time's up!" if time_up else 'Congratulations, you cleared the deck!')
        heading.setStyleSheet('font-size: 14pt; font-weight: bold;')
        layout.addWidget(heading)
        if rank:
            badge = QLabel(f'New best score: #{rank} on the {stats["mode"]} leaderboard')
            badge.setStyleSheet('color: #d08700; font-weight: bold;')
            layout.addWidget(badge)

        grid = QGridLayout()
        rows = [
            ('Mode', stats['mode']),
            ('Time', stats['time_elapsed']),
            ('SETs found', stats['sets_found']),
            ('Wrong guesses', stats['wrong_attempts']),
            ('Hints used', stats['hints_used']),
            ('Accuracy', f"{stats['accuracy_rate']:.0f}%"),
            ('Final score', stats['final_score']),
        ]
        for row, (name, value) in enumerate(rows):
            grid.addWidget(QLabel(name), row, 0)
            value_label = QLabel(str(value))
            value_label.setStyleSheet('font-weight: bold;')
            grid.addWidget(value_label, row, 1)
        layout.addLayout(grid)
        self._buttons(layout, can_restart, show_scores=True)

    def _multiplayer(self, layout, stats: dict, ranking: list[Player], time_up: bool) -> None:
        best = ranking[0].score
        winners = [p.name for p in ranking if p.score == best]
        heading = QLabel(f'{winners[0]} wins!' if len(winners) == 1
                         else f"It's a draw: {' and '.join(winners)}")
        heading.setStyleSheet('font-size: 14pt; font-weight: bold;')
        layout.addWidget(heading)
        summary = f"{stats['mode']} · {stats['time_elapsed']}"
        layout.addWidget(QLabel(f"Time's up. {summary}" if time_up else summary))
        grid = QGridLayout()
        for column, title in enumerate(('', 'Player', 'Points', 'SETs', 'Wrong')):
            header = QLabel(title)
            header.setStyleSheet('font-weight: bold;')
            grid.addWidget(header, 0, column)
        place = 0
        for row, player in enumerate(ranking, start=1):
            if row == 1 or player.score != ranking[row - 2].score:
                place = row
            values = (f'{place}.', player.name, player.score, player.sets_found, player.wrong_attempts)
            for column, value in enumerate(values):
                grid.addWidget(QLabel(str(value)), row, column)
        layout.addLayout(grid)

    def _buttons(self, layout, can_restart: bool, show_scores: bool) -> None:
        buttons = QHBoxLayout()
        close = QPushButton('Close')
        close.clicked.connect(lambda: self.done(CLOSE))
        if can_restart:
            new_game = QPushButton('New Game')
            new_game.setObjectName('primary')
            new_game.setDefault(True)
            new_game.clicked.connect(lambda: self.done(NEW_GAME))
            buttons.addWidget(new_game)
        else:
            close.setDefault(True)
        if show_scores:
            scores = QPushButton('Best Scores')
            scores.clicked.connect(lambda: self.done(SHOW_SCORES))
            buttons.addWidget(scores)
        buttons.addWidget(close)
        layout.addLayout(buttons)
