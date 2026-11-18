import sys
import time
from collections.abc import Set

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtNetwork import QHostAddress
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..card import Card
from ..game import HINT_PENALTY, SET_POINTS, WRONG_PENALTY, Game, GameMode
from ..net.client import LanClient
from ..net.discovery import local_ipv4_addresses
from ..net.host import LanHost
from ..scores import Leaderboard
from .dialogs import game_over
from .dialogs.leaderboard import LeaderboardDialog
from .dialogs.multiplayer import HostDialog, JoinDialog, LocalPlayersDialog
from .dialogs.settings import GuiSettings, SettingsDialog
from .sounds import SoundPlayer
from .theme import get_theme, stylesheet
from .widgets.board_widget import CARD_KEYS, BoardWidget
from .widgets.player_bar import PlayerBar
from .widgets.sidebar import SidebarWidget

SUCCESS_FLASH_MS = 350
ERROR_FLASH_MS = 800
HINT_SHOW_MS = 3000
MESSAGE_MS = 4000
PLAYER_KEYS = ['F1', 'F2', 'F3', 'F4']  # claim for player 1-4 in local multiplayer


class SetGameGUI(QMainWindow):
    """Main application window for the SET game GUI.

    Three ways to play:
    - single player;
    - local multiplayer: everyone shares this screen and claims a SET by clicking their name;
    - LAN: each player has their own computer. The host's window runs a LanHost, and every
      window (the host's too) plays through a LanClient. self.game is then a mirror of the
      host's game, updated from the host's messages.
    """

    def __init__(self, mode: GameMode = GameMode.CLASSIC, seed: int | None = None):
        super().__init__()
        self.game = Game()
        self.leaderboard = Leaderboard()
        self.sounds = SoundPlayer()
        self.settings = GuiSettings.load()
        self._overrides: dict[int, str] = {}  # temporary highlights: hint / error / success
        self._busy = False  # True while a found SET is flashing before it is replaced
        self._game_over_shown = False
        self._available_sets = 0

        # LAN
        self.lan_host: LanHost | None = None
        self.lan_client: LanClient | None = None  # set once the host has welcomed us
        self._connecting: LanClient | None = None
        self._lan_round = -1  # the host's game number, to notice when it starts a new game
        self._lan_connected: frozenset[int] = frozenset()
        self._lan_started = False
        self._awaiting_result = False
        self._pending_state: dict | None = None  # host update that arrived while a SET was flashing

        self.setWindowTitle('SET Game')
        self.resize(1000, 680)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        self._create_info_bar(main_layout)

        content = QHBoxLayout()
        self.board_widget = BoardWidget()
        self.board_widget.card_clicked.connect(self.on_card_clicked)
        content.addWidget(self.board_widget, 1)
        self.sidebar = SidebarWidget()
        self.sidebar.hide()
        content.addWidget(self.sidebar)
        main_layout.addLayout(content, 1)

        self.player_bar = PlayerBar()
        self.player_bar.claim_clicked.connect(self.claim)
        main_layout.addWidget(self.player_bar)
        self._create_controls(main_layout)
        self._create_shortcuts()
        self.statusBar().setSizeGripEnabled(False)

        self.apply_settings(self.settings)
        self.mode_combo.setCurrentIndex(self.mode_combo.findData(mode))
        self.new_game(mode, seed)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(250)

    # ------------------------------------------------------------------ layout

    def _create_info_bar(self, layout):
        bar = QHBoxLayout()
        self.mode_combo = QComboBox()
        for mode in GameMode:
            self.mode_combo.addItem(mode.label, mode)
        self.mode_combo.setFocusPolicy(Qt.NoFocus)
        self.mode_combo.setToolTip('Game mode (starts a new game)')
        self.mode_combo.activated.connect(lambda _: self.new_game(self.mode_combo.currentData()))
        bar.addWidget(self.mode_combo)

        self.score_label = QLabel()
        self.score_label.setToolTip(f'+{SET_POINTS} per SET, -{WRONG_PENALTY} per wrong guess, '
                                    f'-{HINT_PENALTY} per hint')
        self.sets_label = QLabel()
        self.deck_label = QLabel()
        self.available_sets_label = QLabel()
        self.available_sets_label.setToolTip('Number of SETs among the cards on the table')
        for label in (self.score_label, self.sets_label, self.deck_label, self.available_sets_label):
            label.setObjectName('chip')
            bar.addWidget(label)
        self.lan_label = QLabel()
        self.lan_label.setObjectName('lan')
        self.lan_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bar.addWidget(self.lan_label)
        bar.addStretch()

        self.players_button = self._button('Players', None)
        self.players_button.setToolTip('Single player, local multiplayer or a LAN game')
        menu = QMenu(self.players_button)
        menu.addAction('Single player', self.play_single)
        menu.addAction('Local multiplayer…', self.choose_local_players)
        menu.addSeparator()
        menu.addAction('Host LAN game…', self.choose_host_lan)
        menu.addAction('Join LAN game…', self.choose_join_lan)
        self.players_button.setMenu(menu)

        self.new_game_button = self._button('New Game', lambda: self.new_game(), 'primary', 'Ctrl+N')
        self.scores_button = self._button('Best Scores', self.show_leaderboard)
        self.show_sets_button = self._button('Show Found SETs', self.toggle_sidebar, 'accent')
        self.settings_button = self._button('⚙', self.open_settings)
        self.settings_button.setToolTip('Settings')
        for button in (self.players_button, self.new_game_button, self.scores_button,
                       self.show_sets_button, self.settings_button):
            bar.addWidget(button)
        layout.addLayout(bar)

    def _create_controls(self, layout):
        controls = QHBoxLayout()
        self.deal_button = self._button('Deal 3 Cards', self.deal_cards, shortcut='D')
        self.hint_button = self._button('Hint', self.show_hint, shortcut='H')
        self.set_button = self._button('Set', lambda: self.submit_set(), 'primary', 'Enter')
        for button in (self.deal_button, self.hint_button, self.set_button):
            controls.addWidget(button)
        controls.addStretch()
        self.keys_help = QLabel()
        self.keys_help.setStyleSheet('font-size: 8pt;')
        controls.addWidget(self.keys_help)
        self.timer_label = QLabel()
        self.timer_label.setObjectName('timer')
        controls.addWidget(self.timer_label)
        layout.addLayout(controls)

    @staticmethod
    def _button(text, slot, object_name=None, shortcut=None) -> QPushButton:
        button = QPushButton(text)
        button.setFocusPolicy(Qt.NoFocus)  # keep keyboard shortcuts working
        if slot:
            button.clicked.connect(slot)
        if object_name:
            button.setObjectName(object_name)
        if shortcut:
            button.setToolTip(f'Shortcut: {shortcut}')
        return button

    def _create_shortcuts(self):
        for position, key in enumerate(CARD_KEYS):
            QShortcut(QKeySequence(key), self, activated=lambda p=position: self.on_card_clicked(p))
        for key in ('Return', 'Enter', 'Space'):
            QShortcut(QKeySequence(key), self, activated=lambda: self.submit_set())
        for player, key in enumerate(PLAYER_KEYS):
            QShortcut(QKeySequence(key), self, activated=lambda p=player: self.claim(p))
        QShortcut(QKeySequence('H'), self, activated=self.show_hint)
        QShortcut(QKeySequence('D'), self, activated=self.deal_cards)
        QShortcut(QKeySequence('Escape'), self, activated=self.clear_selection)
        QShortcut(QKeySequence('Ctrl+N'), self, activated=lambda: self.new_game())

    # ------------------------------------------------------------------ modes

    @property
    def is_lan(self) -> bool:
        return self.lan_client is not None

    @property
    def is_local_multiplayer(self) -> bool:
        return self.game.is_multiplayer and not self.is_lan

    def _update_mode_controls(self):
        """Show the controls that make sense for single player, local multiplayer or LAN."""
        multiplayer = self.game.is_multiplayer or self.is_lan
        lan_guest = self.is_lan and self.lan_host is None
        self.hint_button.setVisible(self.settings.hints_enabled and not multiplayer)
        self.set_button.setVisible(self.settings.set_button_enabled and not self.is_local_multiplayer)
        self.deal_button.setVisible(not self.is_lan)  # the LAN host deals automatically
        self.player_bar.setVisible(multiplayer)
        self.score_label.setVisible(not multiplayer)
        self.scores_button.setVisible(not multiplayer)
        self.mode_combo.setEnabled(not lan_guest)  # the host chooses the mode and starts games
        self.new_game_button.setVisible(not lan_guest)
        self.new_game_button.setText('Start Game' if self.is_lan and not self._lan_started else 'New Game')
        if self.is_local_multiplayer:
            keys = 'Pick 3 cards, then click your name (or F1-F4) · Esc clear · D deal'
        else:
            keys = 'Keys: 1-0 / Q-P pick cards · Enter submit · Esc clear'
            keys += '' if multiplayer else ' · H hint · D deal'
        self.keys_help.setText(keys)

    def play_single(self):
        self.leave_lan()
        self.game.set_players([])
        self.apply_settings(self.settings)
        self.new_game()

    def choose_local_players(self):
        dialog = LocalPlayersDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.start_local_multiplayer(dialog.names())

    def start_local_multiplayer(self, names: list[str]):
        self.leave_lan()
        self.game.set_players(names)
        self.apply_settings(self.settings)
        self.new_game()

    def choose_host_lan(self):
        dialog = HostDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.host_lan(dialog.player_name())

    def choose_join_lan(self):
        dialog = JoinDialog(self)
        target = dialog.target() if dialog.exec() == QDialog.Accepted else None
        if target:
            self.join_lan(*target, dialog.player_name())

    def host_lan(self, name: str, address: QHostAddress | None = None, announce: bool = True) -> bool:
        """Host a LAN game and join it as its first player."""
        self.leave_lan()
        host = LanHost(name, address=address, announce=announce, parent=self)
        if not host.start():
            self._alert('Could not start hosting: no network port is available.')
            host.deleteLater()
            return False
        self.lan_host = host
        self.join_lan('127.0.0.1', host.port, name)
        return True

    def join_lan(self, address: str, port: int, name: str):
        if self._connecting:
            self._connecting.close()
        client = LanClient(self)
        client.welcomed.connect(lambda player, host_name: self._lan_welcomed(client, host_name))
        client.state_received.connect(self._lan_state)
        client.result_received.connect(self._lan_result)
        client.failed.connect(lambda message: self._lan_failed(client, message))
        self._connecting = client
        self.statusBar().showMessage(f'Connecting to {address}…')
        client.connect_to(address, port, name)

    def leave_lan(self):
        """Back to playing on this computer. Players on other computers are told the game ended."""
        was_playing = self.lan_client is not None
        for client in (self.lan_client, self._connecting):
            if client:
                client.close()
                client.deleteLater()
        self.lan_client = self._connecting = None
        if self.lan_host:
            self.lan_host.stop()
            self.lan_host.deleteLater()
            self.lan_host = None
        if was_playing:
            self.game = Game()  # drop the mirror of the host's game
        self._lan_round = -1
        self._lan_started = False
        self._awaiting_result = False
        self._pending_state = None
        self.lan_label.clear()

    def _lan_welcomed(self, client: LanClient, host_name: str):
        if client is not self._connecting:
            return
        self.lan_client, self._connecting = client, None
        self.game = Game()  # becomes a mirror of the host's game
        self._lan_round = -1
        self._lan_started = False
        self.sidebar.clear_history()
        self._overrides.clear()
        if self.lan_host:
            addresses = ', '.join(local_ipv4_addresses()) or 'this computer'
            self.lan_label.setText(f'Hosting · {addresses}')
            self.lan_label.setToolTip(f'Players can join from Players → Join LAN game, or by typing '
                                      f'this address (port {self.lan_host.port})')
            message = 'Waiting for players to join. Press Start Game when everyone is in.'
        else:
            self.lan_label.setText(f'LAN · {host_name}’s game')
            message = f'Joined {host_name}’s game. Waiting for the host to start.'
        self.apply_settings(self.settings)
        self.board_widget.display_cards([])
        self.statusBar().showMessage(message)

    def _lan_failed(self, client: LanClient, message: str):
        if client is self._connecting or client is self.lan_client:
            was_playing = self.is_lan
            self.leave_lan()
            if was_playing:
                self.game.set_players([])
                self.apply_settings(self.settings)
                self.new_game()
            self._alert(message)

    def _alert(self, message: str):
        self.statusBar().showMessage(message, MESSAGE_MS)
        box = QMessageBox(QMessageBox.Warning, 'SET Game', message, QMessageBox.Ok, self)
        box.setAttribute(Qt.WA_DeleteOnClose)
        box.open()

    def _lan_state(self, state: dict):
        if self._busy:
            self._pending_state = state  # applied once the found SET has been shown
            return
        self._apply_lan_state(state)

    def _apply_lan_state(self, state: dict):
        before = list(self.game.table)
        was_active = self.game.game_active
        selected = {p for p in self.game.selected if p < len(state['table'])
                    and p < len(before) and tuple(state['table'][p]) == before[p]}
        self.game.load_public_state(state)
        self.game.selected = selected
        self._lan_connected = frozenset(state['connected'])
        self._lan_started = state['started']
        new_round = state['round'] != self._lan_round
        self._lan_round = state['round']
        self.mode_combo.setCurrentIndex(self.mode_combo.findData(self.game.mode))
        self._update_mode_controls()

        if new_round and self._lan_started:
            self._overrides.clear()
            self._game_over_shown = False
            self._awaiting_result = False
            self.game.selected.clear()
            self.sidebar.clear_history()
            self.refresh_board(new_positions=set(range(len(self.game.table))))
            self.statusBar().showMessage(f'{self.game.mode.label} game started. Find a SET!', MESSAGE_MS)
            return
        self.refresh_board(new_positions=self._changed_positions(before))
        if was_active and not self.game.game_active and self._lan_started:
            self.show_game_over(time_up=self.game.time_remaining() == 0)

    def _lan_result(self, result: dict):
        game = self.game
        mine = result['player'] == (self.lan_client.player if self.lan_client else None)
        if mine:
            self._awaiting_result = False
        players = game.players
        who = players[result['player']].name if result['player'] < len(players) else 'Someone'
        if not result['counted']:
            if mine:
                self.statusBar().showMessage(result['message'], MESSAGE_MS)
                game.selected.clear()
                self.refresh_states()
            return
        positions = result['positions']
        cards = tuple(tuple(c) for c in result['cards'])
        if result['valid']:
            if any(p >= len(game.table) or game.table[p] != card for p, card in zip(positions, cards,
                                                                                    strict=True)):
                positions = []  # out of step with the host; the next state will put it right
            game.selected -= set(positions)
            self._show_found_set(positions, cards, 'You' if mine else who)
        elif mine:
            self._show_wrong_guess(positions, result['message'])
        else:
            self.statusBar().showMessage(f'{who} guessed wrong.', MESSAGE_MS)

    # ---------------------------------------------------------------- settings

    def apply_settings(self, settings: GuiSettings):
        self.settings = settings
        if self.is_lan:
            self.game.set_options(autodeal=False, hint_enabled=False)  # the host decides
        else:
            self.game.set_options(autodeal=settings.autodeal_enabled,
                                  hint_enabled=settings.hints_enabled and not self.game.is_multiplayer)
        self.game.set_hint_mode(settings.hint_mode)
        self.game.set_button_enabled = settings.set_button_enabled
        self.sounds.enabled = settings.sound_enabled
        self.available_sets_label.setVisible(settings.show_available)

        theme = get_theme(settings.theme)
        QApplication.instance().setStyleSheet(stylesheet(theme))
        self.board_widget.set_theme(theme.felt, {
            'selected': theme.selected, 'hint': theme.hint,
            'error': theme.error, 'success': theme.success,
        })
        self._update_mode_controls()
        if self.game.table:
            self.refresh_board()  # auto-deal may have added cards

    def open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        dialog.settings_changed.connect(self.apply_settings)
        dialog.exec()

    # -------------------------------------------------------------- game flow

    def new_game(self, mode: GameMode | None = None, seed: int | None = None):
        mode = mode or self.mode_combo.currentData()
        if self.is_lan:
            if self.lan_host:
                self.lan_host.start_game(mode, seed)  # everyone, us included, hears the new state
            return
        self.game.new_game(mode, seed)
        self.mode_combo.setCurrentIndex(self.mode_combo.findData(self.game.mode))
        self._overrides.clear()
        self._busy = False
        self._game_over_shown = False
        self.sidebar.clear_history()
        self._update_mode_controls()
        self.refresh_board(new_positions=set(range(len(self.game.table))))
        if self.is_local_multiplayer:
            message = 'Pick 3 cards, then click your name to claim the SET.'
        else:
            message = 'Find 3 cards where every feature is all the same or all different.'
        self.statusBar().showMessage(f'New {self.game.mode.label} game. {message}', MESSAGE_MS)

    def on_card_clicked(self, position: int):
        if self._busy or not self.game.game_active or position >= len(self.game.table):
            return
        if not self.game.toggle_selection(position):
            self.statusBar().showMessage('You can only select 3 cards. Deselect one first.', MESSAGE_MS)
            return
        self._overrides = {p: s for p, s in self._overrides.items() if s == 'hint'}
        self.refresh_states()
        if (len(self.game.selected) == 3 and not self.settings.set_button_enabled
                and not self.is_local_multiplayer):
            self.submit_set()

    def clear_selection(self):
        if not self._busy:
            self.game.selected.clear()
            self.refresh_states()

    def claim(self, player: int):
        """Local multiplayer: `player` claims the selected cards as a SET."""
        if self.is_local_multiplayer and player < len(self.game.players):
            self.submit_set(player)

    def submit_set(self, player: int | None = None):
        if self._busy or len(self.game.selected) != 3 or not self.game.game_active:
            return
        positions = sorted(self.game.selected)
        cards = tuple(self.game.table[p] for p in positions)
        if self.is_lan:
            if not self._awaiting_result and self.lan_client:
                self._awaiting_result = True
                self.lan_client.submit(list(cards))
            return
        if self.is_local_multiplayer and player is None:
            self.statusBar().showMessage('Click your name to claim the SET.', MESSAGE_MS)
            return

        table_before = list(self.game.table)
        result = self.game.submit_set(player)
        who = self.game.players[player].name if player is not None else None
        if not result.valid:
            if not result.penalised:  # locked out: the selection stays for someone else
                self.game.selected = set(positions)
                self.statusBar().showMessage(result.message, MESSAGE_MS)
                self.refresh_states()
                return
            message = f'{who}: {result.message}' if who else result.message
            self._show_wrong_guess(positions, message)
            return
        self._show_found_set(positions, cards, who, table_before)

    def _show_wrong_guess(self, positions, message: str):
        self.sounds.play('wrong')
        self.statusBar().showMessage(message, MESSAGE_MS)
        self._flash({p: 'error' for p in positions}, ERROR_FLASH_MS)
        self.update_game_info()

    def _show_found_set(self, positions, cards: tuple[Card, ...], who: str | None,
                        table_before: list[Card] | None = None):
        """Show the SET in place briefly, then replace it."""
        self.sounds.play('set')
        if who:
            self.statusBar().showMessage(f'SET! {who} +{SET_POINTS} points', MESSAGE_MS)
        else:
            self.statusBar().showMessage(f'SET! +{SET_POINTS} points', MESSAGE_MS)
        table_before = table_before if table_before is not None else list(self.game.table)
        self._busy = True
        self.board_widget.display_cards(table_before)
        self.board_widget.set_card_states(self.game.selected, {p: 'success' for p in positions})
        QTimer.singleShot(SUCCESS_FLASH_MS, lambda: self._after_set_found(cards, table_before, who))

    def _after_set_found(self, cards, table_before, who):
        self._busy = False
        self._overrides.clear()
        self.sidebar.add_found_set(cards, time.strftime('%H:%M:%S'), who)
        if self.is_lan:
            state, self._pending_state = self._pending_state, None
            if state:
                self._apply_lan_state(state)
            else:
                self.refresh_board()
            return
        self.refresh_board(new_positions=self._changed_positions(table_before))
        if not self.game.game_active:
            self.show_game_over(time_up=False)

    def _changed_positions(self, table_before) -> set[int]:
        table = self.game.table
        return {p for p, card in enumerate(table) if p >= len(table_before) or table_before[p] != card} \
            if len(table) >= len(table_before) else set()

    def deal_cards(self):
        if self._busy or not self.game.game_active or self.is_lan:
            return
        if not self.game.can_deal():
            if self.game.deck:
                self.statusBar().showMessage(
                    'There is a SET on the table. Find it before dealing more cards.', MESSAGE_MS)
            return
        before = list(self.game.table)
        if self.game.deal_more():
            self.sounds.play('deal')
            self._overrides.clear()
            self.refresh_board(new_positions=self._changed_positions(before))

    def show_hint(self):
        if self._busy or not self.game.hint_enabled or not self.game.game_active or self.is_lan:
            return
        positions = self.game.get_hint_cards()
        if not positions:
            message = 'There is no SET on the table.'
            if self.game.deck:
                message += ' Deal 3 more cards.'
            self.statusBar().showMessage(message, MESSAGE_MS)
            return
        self.sounds.play('hint')
        self.statusBar().showMessage(f'Hint: -{HINT_PENALTY} points', MESSAGE_MS)
        self._flash({p: 'hint' for p in positions}, HINT_SHOW_MS)
        self.update_game_info()

    def _flash(self, overrides: dict[int, str], duration_ms: int):
        self._overrides.update(overrides)
        self.refresh_states()
        table = list(self.game.table)

        def clear():
            if self.game.table != table:
                return  # the board changed; refresh_board already reset highlights
            for position, state in overrides.items():
                if self._overrides.get(position) == state:
                    del self._overrides[position]
            self.refresh_states()

        QTimer.singleShot(duration_ms, clear)

    def tick(self):
        # Over LAN the host keeps time and ends the game; this window only shows the clock.
        if not self.is_lan and self.game.check_time():
            self.refresh_board()
            self.show_game_over(time_up=True)
        self._update_timer()
        if self.game.is_multiplayer:
            self._update_player_bar()

    def show_game_over(self, time_up: bool):
        if self._game_over_shown:
            return
        self._game_over_shown = True
        self.sounds.play('game_over')
        self.update_game_info()
        stats = self.game.get_game_statistics()
        if self.game.is_multiplayer:
            can_restart = not self.is_lan or self.lan_host is not None
            result = game_over.GameOverDialog(stats, None, time_up, self, ranking=self.game.ranking(),
                                              can_restart=can_restart).exec()
            if result == game_over.NEW_GAME:
                self.new_game()
            return
        rank = self.leaderboard.add(self.game.mode.value, self.game.score, self.game.sets_found,
                                    self.game.elapsed_time)
        result = game_over.GameOverDialog(stats, rank, time_up, self).exec()
        if result == game_over.SHOW_SCORES:
            self.show_leaderboard(rank)
        elif result == game_over.NEW_GAME:
            self.new_game()

    def show_leaderboard(self, highlight_rank: int | None = None):
        LeaderboardDialog(self.leaderboard, self.game.mode, highlight_rank or None, self).exec()

    def closeEvent(self, event):
        self.leave_lan()  # tell the other players
        super().closeEvent(event)

    # ---------------------------------------------------------------- display

    def refresh_board(self, new_positions: Set[int] = frozenset()):
        """Redraw all cards after the table changed."""
        self._available_sets = self.game.available_set_count()
        self.board_widget.display_cards(self.game.table, new_positions)
        self.refresh_states()

    def refresh_states(self):
        self.board_widget.set_card_states(self.game.selected, self._overrides)
        self.update_game_info()

    def update_game_info(self):
        game = self.game
        self.score_label.setText(f'Score: {game.score}')
        self.sets_label.setText(f'SETs: {game.sets_found if not self.is_lan else self._lan_sets_found()}')
        self.deck_label.setText(f'Deck: {len(game.deck)}')
        self.available_sets_label.setText(f'SETs on table: {self._available_sets}')
        self.deal_button.setEnabled(game.game_active and bool(game.deck) and self._available_sets == 0)
        self.hint_button.setEnabled(game.game_active)
        self.set_button.setEnabled(game.game_active and len(game.selected) == 3 and not self._awaiting_result)
        self._update_player_bar()
        self._update_timer()

    def _lan_sets_found(self) -> int:
        return sum(p.sets_found for p in self.game.players)

    def _update_player_bar(self):
        game = self.game
        if not game.is_multiplayer:
            return
        local = self.is_local_multiplayer
        connected = self._lan_connected
        self.player_bar.update_players(
            game.players, [game.lockout_remaining(i) for i in range(len(game.players))],
            can_claim=local and game.game_active and not self._busy and len(game.selected) == 3,
            clickable=local,
            me=self.lan_client.player if self.lan_client else None,
            away=frozenset(i for i in range(len(game.players)) if self.is_lan and i not in connected))

    def _update_timer(self):
        remaining = self.game.time_remaining()
        prefix = 'Time left' if remaining is not None else 'Time'
        self.timer_label.setText(f'{prefix}: {self.game.get_formatted_time()}')
        urgent = remaining is not None and remaining <= 10 and self.game.game_active
        self.timer_label.setStyleSheet('background-color: #c0392b;' if urgent else '')

    def toggle_sidebar(self):
        visible = not self.sidebar.isVisible()
        self.sidebar.setVisible(visible)
        self.show_sets_button.setText('Hide Found SETs' if visible else 'Show Found SETs')


def run_gui(mode: GameMode = GameMode.CLASSIC, seed: int | None = None):
    """Entry point for GUI mode."""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle('Fusion')
    window = SetGameGUI(mode, seed)
    window.show()
    sys.exit(app.exec())
