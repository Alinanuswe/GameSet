import sys
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QComboBox)

from ..game import Game, GameMode, SET_POINTS, HINT_PENALTY, WRONG_PENALTY
from ..scores import Leaderboard
from .dialogs import game_over
from .dialogs.leaderboard import LeaderboardDialog
from .dialogs.settings import GuiSettings, SettingsDialog
from .sounds import SoundPlayer
from .theme import get_theme, stylesheet
from .widgets.board_widget import BoardWidget, CARD_KEYS
from .widgets.sidebar import SidebarWidget

MAX_TABLE_CARDS = 21  # any 20 cards contain a SET, so dealing past 21 is never needed
SUCCESS_FLASH_MS = 350
ERROR_FLASH_MS = 800
HINT_SHOW_MS = 3000
MESSAGE_MS = 4000


class SetGameGUI(QMainWindow):
    """Main application window for the SET game GUI."""

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

        self.setWindowTitle('SET Game')
        self.resize(1000, 640)

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
        for label in (self.score_label, self.sets_label, self.deck_label, self.available_sets_label):
            label.setObjectName('chip')
            bar.addWidget(label)
        bar.addStretch()

        self.new_game_button = self._button('New Game', lambda: self.new_game(), 'primary', 'Ctrl+N')
        self.scores_button = self._button('Best Scores', self.show_leaderboard)
        self.show_sets_button = self._button('Show Found SETs', self.toggle_sidebar, 'accent')
        self.settings_button = self._button('⚙', self.open_settings)
        self.settings_button.setToolTip('Settings')
        for button in (self.new_game_button, self.scores_button, self.show_sets_button, self.settings_button):
            bar.addWidget(button)
        layout.addLayout(bar)

    def _create_controls(self, layout):
        controls = QHBoxLayout()
        self.deal_button = self._button('Deal 3 Cards', self.deal_cards, shortcut='D')
        self.hint_button = self._button('Hint', self.show_hint, shortcut='H')
        self.set_button = self._button('Set', self.submit_set, 'primary', 'Enter')
        for button in (self.deal_button, self.hint_button, self.set_button):
            controls.addWidget(button)
        controls.addStretch()
        keys_help = QLabel('Keys: 1-0 / Q-P pick cards · Enter submit · Esc clear · H hint · D deal')
        keys_help.setStyleSheet('font-size: 8pt;')
        controls.addWidget(keys_help)
        self.timer_label = QLabel()
        self.timer_label.setObjectName('timer')
        controls.addWidget(self.timer_label)
        layout.addLayout(controls)

    @staticmethod
    def _button(text, slot, object_name=None, shortcut=None) -> QPushButton:
        button = QPushButton(text)
        button.setFocusPolicy(Qt.NoFocus)  # keep keyboard shortcuts working
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
            QShortcut(QKeySequence(key), self, activated=self.submit_set)
        QShortcut(QKeySequence('H'), self, activated=self.show_hint)
        QShortcut(QKeySequence('D'), self, activated=self.deal_cards)
        QShortcut(QKeySequence('Escape'), self, activated=self.clear_selection)
        QShortcut(QKeySequence('Ctrl+N'), self, activated=lambda: self.new_game())

    # ---------------------------------------------------------------- settings

    def apply_settings(self, settings: GuiSettings):
        self.settings = settings
        self.game.set_options(autodeal=settings.autodeal_enabled, hint_enabled=settings.hints_enabled)
        self.game.set_hint_mode(settings.hint_mode)
        self.game.set_button_enabled = settings.set_button_enabled
        self.sounds.enabled = settings.sound_enabled

        theme = get_theme(settings.theme)
        QApplication.instance().setStyleSheet(stylesheet(theme))
        self.board_widget.set_theme(theme.felt, {
            'selected': theme.selected, 'hint': theme.hint,
            'error': theme.error, 'success': theme.success,
        })

        self.hint_button.setVisible(settings.hints_enabled)
        self.set_button.setVisible(settings.set_button_enabled)
        self.available_sets_label.setVisible(settings.show_available)
        if self.game.table:
            self.refresh_board()  # auto-deal may have added cards

    def open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        dialog.settings_changed.connect(self.apply_settings)
        dialog.exec()

    # -------------------------------------------------------------- game flow

    def new_game(self, mode: GameMode | None = None, seed: int | None = None):
        self.game.new_game(mode or self.mode_combo.currentData(), seed)
        self.mode_combo.setCurrentIndex(self.mode_combo.findData(self.game.mode))
        self._overrides.clear()
        self._busy = False
        self._game_over_shown = False
        self.sidebar.clear_history()
        self.refresh_board(new_positions=set(range(len(self.game.table))))
        self.statusBar().showMessage(f'New {self.game.mode.label} game. Find 3 cards where every feature '
                                     'is all the same or all different.', MESSAGE_MS)

    def on_card_clicked(self, position: int):
        if self._busy or not self.game.game_active or position >= len(self.game.table):
            return
        if not self.game.toggle_selection(position):
            self.statusBar().showMessage('You can only select 3 cards. Deselect one first.', MESSAGE_MS)
            return
        self._overrides = {p: s for p, s in self._overrides.items() if s == 'hint'}
        self.refresh_states()
        if len(self.game.selected) == 3 and not self.settings.set_button_enabled:
            self.submit_set()

    def clear_selection(self):
        if not self._busy:
            self.game.selected.clear()
            self.refresh_states()

    def submit_set(self):
        if self._busy or len(self.game.selected) != 3:
            return
        positions = sorted(self.game.selected)
        found_cards = tuple(self.game.table[p] for p in positions)
        table_before = list(self.game.table)
        result = self.game.submit_set()

        if not result.valid:
            self.sounds.play('wrong')
            self.statusBar().showMessage(result.message, MESSAGE_MS)
            self._flash({p: 'error' for p in positions}, ERROR_FLASH_MS)
            self.update_game_info()
            return

        # Show the SET in place briefly, then replace it.
        self.sounds.play('set')
        self.statusBar().showMessage(f'SET! +{SET_POINTS} points', MESSAGE_MS)
        self._busy = True
        self.board_widget.display_cards(table_before)
        self.board_widget.set_card_states(set(), {p: 'success' for p in positions})
        QTimer.singleShot(SUCCESS_FLASH_MS, lambda: self._after_set_found(found_cards, table_before))

    def _after_set_found(self, cards, table_before):
        self._busy = False
        self._overrides.clear()
        self.sidebar.add_found_set(cards, time.strftime('%H:%M:%S'))
        self.refresh_board(new_positions=self._changed_positions(table_before))
        if not self.game.game_active:
            self.show_game_over(time_up=False)

    def _changed_positions(self, table_before) -> set[int]:
        table = self.game.table
        return {p for p, card in enumerate(table) if p >= len(table_before) or table_before[p] != card} \
            if len(table) >= len(table_before) else set()

    def deal_cards(self):
        if self._busy or not self.deal_button.isEnabled():
            return
        before = list(self.game.table)
        if self.game.deal_more():
            self.sounds.play('deal')
            self._overrides.clear()
            self.refresh_board(new_positions=self._changed_positions(before))

    def show_hint(self):
        if self._busy or not self.game.hint_enabled or not self.game.game_active:
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
        if self.game.check_time():
            self.refresh_board()
            self.show_game_over(time_up=True)
        self._update_timer()

    def show_game_over(self, time_up: bool):
        if self._game_over_shown:
            return
        self._game_over_shown = True
        self.sounds.play('game_over')
        self.update_game_info()
        rank = self.leaderboard.add(self.game.mode.value, self.game.score, self.game.sets_found,
                                    self.game.elapsed_time)
        result = game_over.GameOverDialog(self.game.get_game_statistics(), rank, time_up, self).exec()
        if result == game_over.SHOW_SCORES:
            self.show_leaderboard(rank)
        elif result == game_over.NEW_GAME:
            self.new_game()

    def show_leaderboard(self, highlight_rank: int | None = None):
        LeaderboardDialog(self.leaderboard, self.game.mode, highlight_rank or None, self).exec()

    # ---------------------------------------------------------------- display

    def refresh_board(self, new_positions: set[int] = frozenset()):
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
        self.sets_label.setText(f'SETs: {game.sets_found}')
        self.deck_label.setText(f'Deck: {len(game.deck)}')
        self.available_sets_label.setText(f'On table: {self._available_sets}')
        self.deal_button.setEnabled(game.game_active and bool(game.deck)
                                    and len(game.table) < MAX_TABLE_CARDS)
        self.hint_button.setEnabled(game.game_active)
        self.set_button.setEnabled(game.game_active and len(game.selected) == 3)
        self._update_timer()

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
