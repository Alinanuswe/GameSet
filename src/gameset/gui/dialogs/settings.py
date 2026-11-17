"""Settings dialog and the persisted settings it edits."""

from dataclasses import dataclass, fields

from PySide6.QtCore import QSettings, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

HINT_MODES = {3: '3 cards', 2: '2 cards', 1: '1 card'}
THEMES = {'light': 'Light', 'dark': 'Dark'}


def open_settings_store() -> QSettings:
    return QSettings('GameSet', 'Settings')


@dataclass
class GuiSettings:
    hints_enabled: bool = True
    hint_mode: int = 3
    autodeal_enabled: bool = False
    set_button_enabled: bool = False  # False: a correct SET is confirmed as soon as 3 cards are picked
    show_available: bool = False
    sound_enabled: bool = True
    theme: str = 'light'

    @classmethod
    def load(cls, store: QSettings | None = None) -> 'GuiSettings':
        store = store or open_settings_store()
        values = {}
        for f in fields(cls):
            default = getattr(cls, f.name)
            values[f.name] = store.value(f.name, default, type=type(default))
        settings = cls(**values)
        if settings.hint_mode not in HINT_MODES:
            settings.hint_mode = 3
        if settings.theme not in THEMES:
            settings.theme = 'light'
        return settings

    def save(self, store: QSettings | None = None) -> None:
        store = store or open_settings_store()
        for f in fields(self):
            store.setValue(f.name, getattr(self, f.name))
        store.sync()


class SettingsDialog(QDialog):
    settings_changed = Signal(object)  # GuiSettings

    def __init__(self, settings: GuiSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        self.setMinimumWidth(380)
        layout = QVBoxLayout(self)

        game_group = QGroupBox('Game')
        game_layout = QVBoxLayout(game_group)
        self.autodeal_checkbox = QCheckBox('Auto-deal 3 cards when there is no SET on the table')
        self.set_button_checkbox = QCheckBox('Confirm SETs with the Set button / Enter key')
        self.set_button_checkbox.setToolTip('When off, 3 selected cards are checked immediately.')
        self.show_available_checkbox = QCheckBox('Show how many SETs are on the table')
        for checkbox in (self.autodeal_checkbox, self.set_button_checkbox, self.show_available_checkbox):
            game_layout.addWidget(checkbox)
        layout.addWidget(game_group)

        hint_group = QGroupBox('Hints')
        hint_layout = QVBoxLayout(hint_group)
        self.hints_checkbox = QCheckBox('Enable hints (each hint costs points)')
        self.hints_checkbox.toggled.connect(self._on_hints_toggled)
        hint_layout.addWidget(self.hints_checkbox)
        row = QHBoxLayout()
        row.addWidget(QLabel('A hint reveals:'))
        self.hint_mode_combo = QComboBox()
        for mode, text in HINT_MODES.items():
            self.hint_mode_combo.addItem(text, mode)
        row.addWidget(self.hint_mode_combo)
        hint_layout.addLayout(row)
        layout.addWidget(hint_group)

        look_group = QGroupBox('Appearance and sound')
        look_layout = QVBoxLayout(look_group)
        row = QHBoxLayout()
        row.addWidget(QLabel('Theme:'))
        self.theme_combo = QComboBox()
        for key, text in THEMES.items():
            self.theme_combo.addItem(text, key)
        row.addWidget(self.theme_combo)
        look_layout.addLayout(row)
        self.sound_checkbox = QCheckBox('Sound effects')
        look_layout.addWidget(self.sound_checkbox)
        layout.addWidget(look_group)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.ok_button = QPushButton('OK')
        self.ok_button.setObjectName('primary')
        self.ok_button.clicked.connect(self.accept_and_save)
        self.apply_button = QPushButton('Apply')
        self.apply_button.clicked.connect(self.apply_settings)
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.reject)
        for button in (self.ok_button, self.apply_button, self.cancel_button):
            buttons.addWidget(button)
        layout.addLayout(buttons)

        self._load(settings)

    def _load(self, s: GuiSettings) -> None:
        self.autodeal_checkbox.setChecked(s.autodeal_enabled)
        self.set_button_checkbox.setChecked(s.set_button_enabled)
        self.show_available_checkbox.setChecked(s.show_available)
        self.hints_checkbox.setChecked(s.hints_enabled)
        self.hint_mode_combo.setCurrentIndex(self.hint_mode_combo.findData(s.hint_mode))
        self.theme_combo.setCurrentIndex(self.theme_combo.findData(s.theme))
        self.sound_checkbox.setChecked(s.sound_enabled)
        self._on_hints_toggled(s.hints_enabled)

    def current_settings(self) -> GuiSettings:
        return GuiSettings(
            hints_enabled=self.hints_checkbox.isChecked(),
            hint_mode=self.hint_mode_combo.currentData(),
            autodeal_enabled=self.autodeal_checkbox.isChecked(),
            set_button_enabled=self.set_button_checkbox.isChecked(),
            show_available=self.show_available_checkbox.isChecked(),
            sound_enabled=self.sound_checkbox.isChecked(),
            theme=self.theme_combo.currentData(),
        )

    def _on_hints_toggled(self, enabled: bool) -> None:
        self.hint_mode_combo.setEnabled(enabled)

    def apply_settings(self) -> None:
        settings = self.current_settings()
        settings.save()
        self.settings_changed.emit(settings)

    def accept_and_save(self) -> None:
        self.apply_settings()
        self.accept()
