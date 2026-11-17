"""
Settings dialog for SET game GUI.
Provides persistent configuration options using QSettings.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QComboBox, QGroupBox
from PySide6.QtCore import QSettings, Signal
from PySide6.QtGui import QFont


class SettingsDialog(QDialog):
    """Settings dialog with persistent configuration."""
    
    # Signal for settings changes
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.settings = QSettings("GameSet", "Settings")
        
        # Initialize settings values
        self.hints_enabled = self.settings.value("hints_enabled", True, type=bool)
        self.autodeal_enabled = self.settings.value("autodeal_enabled", False, type=bool)
        self.set_button_enabled = self.settings.value("set_button_enabled", False, type=bool)
        self.hint_mode = self.settings.value("hint_mode", "3", type=str)
        self.sound_enabled = self.settings.value("sound_enabled", True, type=bool)
        self.theme = self.settings.value("theme", "light", type=str)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Set up the settings dialog UI."""
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 450)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Game Settings Group
        game_group = QGroupBox("Game Settings")
        game_layout = QVBoxLayout()
        
        # Hints checkbox
        self.hints_checkbox = QCheckBox("Enable Hints")
        self.hints_checkbox.stateChanged.connect(self.on_hints_changed)
        game_layout.addWidget(self.hints_checkbox)
        
        # Autodeal checkbox
        self.autodeal_checkbox = QCheckBox("Enable Auto-deal")
        game_layout.addWidget(self.autodeal_checkbox)
        
        # Set button checkbox
        self.set_button_checkbox = QCheckBox("Enable Set Button")
        game_layout.addWidget(self.set_button_checkbox)
        
        game_group.setLayout(game_layout)
        layout.addWidget(game_group)
        
        # Hint Settings Group
        hint_group = QGroupBox("Hint Settings")
        hint_layout = QVBoxLayout()
        
        # Hint mode selection
        hint_mode_layout = QHBoxLayout()
        hint_mode_layout.addWidget(QLabel("Hint Mode:"))
        
        self.hint_mode_combo = QComboBox()
        self.hint_mode_combo.addItems(["3 cards", "2 cards", "1 card"])
        self.hint_mode_combo.currentTextChanged.connect(self.on_hint_mode_changed)
        hint_mode_layout.addWidget(self.hint_mode_combo)
        hint_layout.addLayout(hint_mode_layout)
        
        hint_group.setLayout(hint_layout)
        layout.addWidget(hint_group)
        
        # Appearance Settings Group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout()
        
        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        appearance_layout.addLayout(theme_layout)
        
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # Sound Settings Group
        sound_group = QGroupBox("Sound")
        sound_layout = QVBoxLayout()
        
        # Sound effects checkbox
        self.sound_checkbox = QCheckBox("Enable Sound Effects")
        sound_layout.addWidget(self.sound_checkbox)
        
        sound_group.setLayout(sound_layout)
        layout.addWidget(sound_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_and_save)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        self.apply_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.apply_button)
        
        layout.addLayout(button_layout)
        
        # Enable/disable hint mode based on hints checkbox
        self.on_hints_changed()
    
    def load_settings(self):
        """Load settings from QSettings."""
        self.hints_checkbox.setChecked(self.hints_enabled)
        self.autodeal_checkbox.setChecked(self.autodeal_enabled)
        self.set_button_checkbox.setChecked(self.set_button_enabled)
        self.sound_checkbox.setChecked(self.sound_enabled)
        
        # Set hint mode
        hint_mode_map = {"3": "3 cards", "2": "2 cards", "1": "1 card"}
        hint_mode_text = hint_mode_map.get(self.hint_mode, "3 cards")
        index = self.hint_mode_combo.findText(hint_mode_text)
        if index >= 0:
            self.hint_mode_combo.setCurrentIndex(index)
        
        # Set theme
        theme_text = self.theme.capitalize()
        index = self.theme_combo.findText(theme_text)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
    
    def save_settings(self):
        """Save settings to QSettings."""
        self.settings.setValue("hints_enabled", self.hints_checkbox.isChecked())
        self.settings.setValue("autodeal_enabled", self.autodeal_checkbox.isChecked())
        self.settings.setValue("set_button_enabled", self.set_button_checkbox.isChecked())
        self.settings.setValue("sound_enabled", self.sound_checkbox.isChecked())
        
        # Save hint mode
        hint_mode_text = self.hint_mode_combo.currentText()
        hint_mode_map = {"3 cards": "3", "2 cards": "2", "1 card": "1"}
        self.settings.setValue("hint_mode", hint_mode_map.get(hint_mode_text, "3"))
        
        # Save theme
        theme_text = self.theme_combo.currentText()
        self.settings.setValue("theme", theme_text.lower())
        
        self.settings.sync()
    
    def apply_settings(self):
        """Apply settings without closing dialog."""
        self.save_settings()
        self.settings_changed.emit()
    
    def accept_and_save(self):
        """Accept dialog and save settings."""
        self.save_settings()
        self.settings_changed.emit()
        self.accept()
    
    def on_hints_changed(self):
        """Handle hints checkbox state change."""
        hints_enabled = self.hints_checkbox.isChecked()
        self.hint_mode_combo.setEnabled(hints_enabled)
    
    def on_hint_mode_changed(self, text: str):
        """Handle hint mode change."""
        # This could trigger immediate hint mode update
        pass
    
    def on_theme_changed(self, text: str):
        """Handle theme change."""
        # This could trigger immediate theme update
        pass
    
    def get_settings(self) -> dict:
        """Get current settings as dictionary."""
        return {
            'hints_enabled': self.hints_checkbox.isChecked(),
            'autodeal_enabled': self.autodeal_checkbox.isChecked(),
            'set_button_enabled': self.set_button_checkbox.isChecked(),
            'sound_enabled': self.sound_checkbox.isChecked(),
            'hint_mode': self.hint_mode_combo.currentText(),
            'theme': self.theme_combo.currentText()
        }
