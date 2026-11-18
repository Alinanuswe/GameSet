"""One large button per player. In local multiplayer, a player claims the selected SET by
clicking (or tapping) their name. Over LAN the buttons only show the scores."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from ...game import Player


class PlayerBar(QWidget):
    claim_clicked = Signal(int)  # player index

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.buttons: list[QPushButton] = []

    def update_players(self, players: list[Player], lockouts: list[float], *, can_claim: bool,
                       clickable: bool, me: int | None = None, away: frozenset[int] = frozenset()) -> None:
        """can_claim: 3 cards are selected; clickable: False shows scores only (LAN)."""
        while len(self.buttons) < len(players):
            button = QPushButton()
            button.setFocusPolicy(Qt.NoFocus)
            button.setMinimumHeight(56)  # a comfortable target on a touchscreen
            button.setObjectName('player')
            index = len(self.buttons)
            button.clicked.connect(lambda _=False, i=index: self.claim_clicked.emit(i))
            self._layout.addWidget(button, 1)
            self.buttons.append(button)
        while len(self.buttons) > len(players):
            self.buttons.pop().deleteLater()

        for index, (player, button) in enumerate(zip(players, self.buttons, strict=True)):
            wait = lockouts[index]
            if wait > 0:
                status = f'wait {wait:.0f}s'
            elif index in away:
                status = 'away'
            else:
                status = f'{player.score} pts · {player.sets_found} SETs'
            label = f'{player.name} (you)' if index == me else player.name
            button.setText(f'{label}\n{status}')
            button.setProperty('me', index == me)
            button.setAttribute(Qt.WA_TransparentForMouseEvents, not clickable)
            claimable = clickable and can_claim and wait <= 0
            button.setEnabled(not clickable or claimable)
            button.setProperty('claimable', claimable)
            button.setToolTip('Select 3 cards, then click your name to claim the SET' if clickable else '')
            button.style().unpolish(button)
            button.style().polish(button)
