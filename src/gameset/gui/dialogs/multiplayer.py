"""Dialogs for setting up local and LAN multiplayer games."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QVBoxLayout,
)

from ...net.discovery import HostFinder
from ...net.protocol import GAME_PORT, MAX_NAME_LENGTH, clean_name
from . import settings

MAX_LOCAL_PLAYERS = 4


def _remembered(key: str, default: str) -> str:
    return str(settings.open_settings_store().value(key, default))


def _remember(key: str, value: str) -> None:
    store = settings.open_settings_store()
    store.setValue(key, value)
    store.sync()


def _name_field(text: str) -> QLineEdit:
    field = QLineEdit(text)
    field.setMaxLength(MAX_NAME_LENGTH)
    return field


class LocalPlayersDialog(QDialog):
    """Names for 2-4 players sharing this screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Local Multiplayer')
        layout = QVBoxLayout(self)
        intro = QLabel('Everyone plays on this screen. Pick 3 cards, then click or tap your name '
                       'to claim the SET. A wrong claim costs points and a short wait.')
        intro.setWordWrap(True)
        layout.addWidget(intro)

        saved = _remembered('local_players', '').split('\n')
        form = QFormLayout()
        self.fields = []
        for i in range(MAX_LOCAL_PLAYERS):
            field = _name_field(saved[i] if i < len(saved) and saved[i] else f'Player {i + 1}')
            self.fields.append(field)
            form.addRow(f'Player {i + 1}', field)
        self.count = QSpinBox()
        self.count.setRange(2, MAX_LOCAL_PLAYERS)
        self.count.setValue(2)
        self.count.valueChanged.connect(self._show_fields)
        form.insertRow(0, 'Players', self.count)
        layout.addLayout(form)
        self._show_fields()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText('Start')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _show_fields(self) -> None:
        for i, field in enumerate(self.fields):
            field.setEnabled(i < self.count.value())

    def names(self) -> list[str]:
        names: list[str] = []
        for i, field in enumerate(self.fields[:self.count.value()]):
            name = clean_name(field.text(), f'Player {i + 1}')
            while name in names:
                name += '+'
            names.append(name)
        return names

    def accept(self) -> None:
        _remember('local_players', '\n'.join(field.text() for field in self.fields))
        super().accept()


class HostDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Host a LAN Game')
        layout = QVBoxLayout(self)
        intro = QLabel('Other players on the same network can join your game. You start it once '
                       'everyone is in. Windows may ask you to allow the game through the firewall.')
        intro.setWordWrap(True)
        layout.addWidget(intro)
        form = QFormLayout()
        self.name = _name_field(_remembered('lan_name', 'Host'))
        form.addRow('Your name', self.name)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText('Host')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def player_name(self) -> str:
        return clean_name(self.name.text(), 'Host')

    def accept(self) -> None:
        _remember('lan_name', self.name.text())
        super().accept()


class JoinDialog(QDialog):
    """Lists games found on the network; an address can also be typed in."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Join a LAN Game')
        self.resize(420, 360)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = _name_field(_remembered('lan_name', 'Player'))
        form.addRow('Your name', self.name)
        layout.addLayout(form)

        layout.addWidget(QLabel('Games on your network:'))
        self.games = QListWidget()
        self.games.itemSelectionChanged.connect(self._game_picked)
        self.games.itemDoubleClicked.connect(lambda _: self.accept())
        layout.addWidget(self.games)
        self.searching = QLabel('Looking for games…')
        self.searching.setStyleSheet('font-style: italic;')
        layout.addWidget(self.searching)

        address_form = QFormLayout()
        self.address = QLineEdit()
        self.address.setPlaceholderText('for example 192.168.1.20')
        self.address.textEdited.connect(lambda _: self.games.clearSelection())
        address_form.addRow('Or host address', self.address)
        layout.addLayout(address_form)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText('Join')
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.finder = HostFinder(self)
        self.finder.hosts_changed.connect(self._list_games)
        if not self.finder.start():
            self.searching.setText('Cannot look for games on this computer. Type the host address instead.')

    def _list_games(self) -> None:
        current = self.games.currentItem()
        chosen = current.data(Qt.UserRole) if current else None
        self.games.clear()
        for (address, port), name in sorted(self.finder.hosts.items(), key=lambda kv: kv[1].lower()):
            item = QListWidgetItem(f'{name}’s game  ({address})')
            item.setData(Qt.UserRole, (address, port))
            self.games.addItem(item)
            if (address, port) == chosen:
                self.games.setCurrentItem(item)
        found = self.games.count()
        self.searching.setText(f'Found {found} game(s).' if found else 'Looking for games…')

    def _game_picked(self) -> None:
        item = self.games.currentItem()
        if item and item.isSelected():
            self.address.setText(item.data(Qt.UserRole)[0])

    def target(self) -> tuple[str, int] | None:
        """(address, port) to connect to, or None if nothing was chosen."""
        item = self.games.currentItem()
        if item and item.isSelected():
            return item.data(Qt.UserRole)
        text = self.address.text().strip()
        if not text:
            return None
        address, _, port = text.rpartition(':') if text.count(':') == 1 else (text, '', '')
        try:
            return address, int(port) if port else GAME_PORT
        except ValueError:
            return text, GAME_PORT

    def player_name(self) -> str:
        return clean_name(self.name.text())

    def accept(self) -> None:
        if self.target() is None:
            self.searching.setText('Pick a game from the list or type the host address.')
            return
        _remember('lan_name', self.name.text())
        self.finder.stop()
        super().accept()

    def reject(self) -> None:
        self.finder.stop()
        super().reject()
