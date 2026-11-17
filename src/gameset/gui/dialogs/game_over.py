from PySide6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

# Result codes for exec()
CLOSE, NEW_GAME, SHOW_SCORES = 0, 1, 2


class GameOverDialog(QDialog):
    def __init__(self, stats: dict, rank: int | None, time_up: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Game Over')
        layout = QVBoxLayout(self)

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

        buttons = QHBoxLayout()
        new_game = QPushButton('New Game')
        new_game.setObjectName('primary')
        new_game.setDefault(True)
        new_game.clicked.connect(lambda: self.done(NEW_GAME))
        scores = QPushButton('Best Scores')
        scores.clicked.connect(lambda: self.done(SHOW_SCORES))
        close = QPushButton('Close')
        close.clicked.connect(lambda: self.done(CLOSE))
        for button in (new_game, scores, close):
            buttons.addWidget(button)
        layout.addLayout(buttons)
