import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QBrush, QColor, QPen, QIcon
from game import Game
from gui.widgets.board_widget import BoardWidget
from gui.widgets.sidebar import SidebarWidget
from gui.dialogs.settings import SettingsDialog


class SetGameGUI(QMainWindow):
    """Main application window for the SET game GUI."""
    
    def __init__(self):
        super().__init__()
        
        # Game instance
        self.game = Game()
        
        # Create sidebar widget
        self.sidebar = SidebarWidget()
        
        # Connect sidebar signals
        self.sidebar.settings_requested.connect(self.open_settings)
        
        # Set up window
        self.setWindowTitle("Nunu SET")
        self.resize(800, 600)
        
        # Set window icon
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo.png')
        self.setWindowIcon(QIcon(logo_path))
        
        # Center window on screen
        screen = self.screen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create top info bar
        self.create_info_bar(main_layout)
        
        # Create main content area with board and sidebar
        content_layout = QHBoxLayout()
        
        # Create board widget
        self.board_widget = BoardWidget()
        # Set the scene parent to this window for card selection handling
        self.board_widget.scene.setParent(self)
        
        # Connect card selection signals directly (backup connection)
        if hasattr(self.board_widget, 'card_selection_signal'):
            self.board_widget.card_selection_signal.connect(self.handle_card_selection)
        
        content_layout.addWidget(self.board_widget, 3)  # Board takes 3/4 of space
        
        # Create sidebar widget
        self.sidebar = SidebarWidget()
        
        # Connect sidebar signals
        self.sidebar.settings_requested.connect(self.open_settings)
        
        content_layout.addWidget(self.sidebar, 1)  # Sidebar takes 1/4 of space on right
        
        # Hide sidebar by default
        self.sidebar.hide()
        
        main_layout.addLayout(content_layout)
        
        # Create bottom controls
        self.create_controls(main_layout)
        
        # Start new game
        self.new_game()
        
        # Set up timer for updating game info
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game_info)
        self.timer.start(1000)  # Update every second
    
    def create_info_bar(self, layout):
        """Create the top information bar."""
        info_layout = QHBoxLayout()
        
        # Game info labels
        self.score_label = QLabel("Score: 0")
        self.sets_label = QLabel("Sets: 0")
        self.deck_label = QLabel("Deck: 69")
        self.available_sets_label = QLabel("Available: 0")
        
        # Set font
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        
        for label in [self.score_label, self.sets_label, self.deck_label, 
                     self.available_sets_label]:
            label.setFont(font)
            label.setStyleSheet("color: white; background-color: #1a3d2a; padding: 5px; border-radius: 3px;")
        
        # Show Identified Sets button
        self.show_sets_button = QPushButton("Show Identified Sets")
        self.show_sets_button.setFixedWidth(150)
        self.show_sets_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:pressed {
                background-color: #117a8b;
            }
        """)
        self.show_sets_button.clicked.connect(self.toggle_sidebar)
        
        # New Game button
        self.new_game_button = QPushButton("New Game")
        self.new_game_button.setFixedWidth(100)
        self.new_game_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.new_game_button.clicked.connect(self.new_game)
        
        # Settings button with gear unicode
        self.settings_button = QPushButton("⚙")
        self.settings_button.setFixedSize(30, 30)
        self.settings_button.setFont(QFont("Arial", 14))
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
        """)
        self.settings_button.clicked.connect(self.open_settings)
        
        # Add to layout
        info_layout.addWidget(self.score_label)
        info_layout.addWidget(self.sets_label)
        info_layout.addWidget(self.deck_label)
        info_layout.addWidget(self.available_sets_label)
        info_layout.addStretch()
        info_layout.addWidget(self.new_game_button)
        info_layout.addWidget(self.show_sets_button)
        info_layout.addWidget(self.settings_button)
        
        layout.addLayout(info_layout)
    
    def create_controls(self, layout):
        """Create the bottom control buttons."""
        controls_layout = QHBoxLayout()
        
        # Timer label at bottom left
        self.timer_label = QLabel("Time: 00:00")
        self.timer_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.timer_label.setStyleSheet("color: white; background-color: #1a3d2a; padding: 8px 15px; border-radius: 5px;")
        
        # Center the control buttons
        buttons_layout = QHBoxLayout()
        
        # Deal button
        self.deal_button = QPushButton("Deal 3 Cards")
        self.deal_button.clicked.connect(self.deal_cards)
        
        # Hint button
        self.hint_button = QPushButton("Hint")
        self.hint_button.clicked.connect(self.show_hint)
        
        # Set button (optional feature)
        self.set_button = QPushButton("Set")
        self.set_button.clicked.connect(self.submit_set)
        
        buttons_layout.addWidget(self.deal_button)
        buttons_layout.addWidget(self.hint_button)
        buttons_layout.addWidget(self.set_button)
        
        # Add to layout
        controls_layout.addWidget(self.timer_label)
        controls_layout.addStretch()
        controls_layout.addLayout(buttons_layout)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
    
    def new_game(self):
        """Start a new game."""
        self.game.new_game()
        self.update_board()
        self.update_game_info()
        self.sidebar.clear_history()
        self.deal_button.setEnabled(False)  # Disabled until no sets available
    
    def update_board(self):
        """Update the board display with current game cards."""
        # Convert game cards to card indices
        card_indices = []
        for card in self.game.table:
            # Find card index (this is simplified - would need proper mapping in full implementation)
            # For now, use a simple approach
            card_index = self._find_card_index(card)
            if card_index is not None:
                card_indices.append(card_index)
        
        self.board_widget.display_cards(card_indices)
    
    def _find_card_index(self, card):
        """Find the index of a card (simplified implementation)."""
        # This is a placeholder - in full implementation, we'd need proper card-to-index mapping
        # For now, return a simple calculation
        shape, color, number, shading = card
        return shape * 27 + color * 9 + number * 3 + shading
    
    def update_game_info(self):
        """Update the game information display."""
        self.score_label.setText(f"Score: {self.game.score}")
        self.sets_label.setText(f"Sets: {self.game.sets_found}")
        self.deck_label.setText(f"Deck: {len(self.game.deck)}")
        
        available_sets = self.game.available_set_count()
        self.available_sets_label.setText(f"Available: {available_sets}")
        
        # Enable/disable deal button based on available sets
        self.deal_button.setEnabled(available_sets == 0 and len(self.game.deck) > 0)
        
        # Update timer
        self.timer_label.setText(f"Time: {self.game.get_formatted_time()}")
    
    def deal_cards(self):
        """Deal 3 more cards."""
        if self.game.deck and len(self.game.table) < 21:  # Safety limit of 21 cards
            self.game.deal_more()
            self.update_board()
            self.update_game_info()
    
    def show_hint(self):
        """Show a hint based on current hint mode."""
        if not self.game.hint_enabled:
            return
        
        # Get hint cards from game logic
        hint_cards = self.game.get_hint_cards()
        if not hint_cards:
            return
        
        # Clear any existing glowing
        self.board_widget.clear_all_glowing()
        
        # Apply glowing to hint cards
        for card_pos in hint_cards:
            if card_pos < len(self.board_widget.card_items):
                card_item = self.board_widget.get_card_item(card_pos)
                if card_item:
                    card_item.set_glowing(True)
        
        # Clear glowing after 3 seconds
        QTimer.singleShot(3000, self.board_widget.clear_all_glowing)
    
    def handle_card_selection(self, board_position: int, selected: bool):
        """Handle card selection from board widget."""
        # Update game state with selection
        if selected:
            self.game.selected.add(board_position)
        else:
            self.game.selected.discard(board_position)
        
        # Enable/disable Set button based on selection count
        self.set_button.setEnabled(len(self.game.selected) == 3)
        
        # Auto-confirm mode: if Set button is disabled and 3 cards selected, auto-submit
        if not self.game.set_button_enabled and len(self.game.selected) == 3:
            self.submit_set()
    
    def submit_set(self):
        """Submit selected cards as a set."""
        if len(self.game.selected) != 3:
            return
        
        # Capture card indices BEFORE submit_set modifies the table
        selected_positions = sorted(self.game.selected)
        card_indices = []
        for pos in selected_positions:
            if pos < len(self.game.table):
                card_index = self._find_card_index(self.game.table[pos])
                card_indices.append(card_index)
        
        # Submit the set to game logic
        if self.game.submit_set():
            # Valid set - update board
            self.update_board()
            self.update_game_info()
            
            # Add found set to sidebar using pre-captured card indices
            self.add_found_set_to_sidebar(card_indices)
            
            # Check if game is over
            if self.game.is_game_over():
                self.show_game_over()
            else:
                # Update board to show remaining cards in proper layout
                self.update_board()
        else:
            # Invalid set - show visual feedback
            self.show_invalid_set_feedback()
    
    def show_invalid_set_feedback(self):
        """Show visual feedback for invalid set selection."""
        selected_cards = self.board_widget.get_selected_cards()
        for card_pos in selected_cards:
            card_item = self.board_widget.get_card_item(card_pos)
            if card_item:
                # Flash red border
                card_item.highlight_rect.setPen(QPen(QColor(255, 0, 0), 4))  # Red border for error
                card_item.is_in_error = True  # Mark as in error state
        
        # Reset after a short delay
        QTimer.singleShot(1000, self.clear_invalid_feedback)
    
    def clear_invalid_feedback(self):
        """Clear invalid set feedback."""
        # Clear error state from all cards
        for card_item in self.board_widget.card_items:
            card_item.is_in_error = False
            card_item.update_selection_highlight()
            
        # Update remaining selected cards to show yellow borders
        selected_cards = self.board_widget.get_selected_cards()
        for card_pos in selected_cards:
            card_item = self.board_widget.get_card_item(card_pos)
            if card_item and card_item.is_selected:
                # Ensure remaining selected cards show yellow borders
                card_item.update_selection_highlight()

    def add_found_set_to_sidebar(self, cards: List[int]):
        """Add a found set to the sidebar."""
        import time
        timestamp = time.strftime("%H:%M:%S")
        self.sidebar.add_found_set(cards, timestamp)

    def toggle_sidebar(self):
        """Toggle the visibility of the sidebar."""
        if self.sidebar.isVisible():
            self.sidebar.hide()
            self.show_sets_button.setText("Show Identified Sets")
        else:
            self.sidebar.show()
            self.show_sets_button.setText("Hide Identified Sets")
    
    def open_settings(self):
        """Open settings dialog."""
        settings_dialog = SettingsDialog(self)
        settings_dialog.settings_changed.connect(self.apply_settings_to_game)
        settings_dialog.exec()
    
    def apply_settings_to_game(self):
        """Apply settings from dialog to the game."""
        # Get the settings dialog to read current values
        # Since the dialog might be closed, read from QSettings directly
        from PySide6.QtCore import QSettings
        settings = QSettings("GameSet", "Settings")
        
        autodeal_enabled = settings.value("autodeal_enabled", False, type=bool)
        hints_enabled = settings.value("hints_enabled", True, type=bool)
        hint_mode = settings.value("hint_mode", "3", type=str)
        set_button_enabled = settings.value("set_button_enabled", False, type=bool)
        
        # Apply to game
        self.game.set_options(autodeal=autodeal_enabled, hint_enabled=hints_enabled)
        self.game.hint_mode = int(hint_mode)
        self.game.set_button_enabled = set_button_enabled
        
        # Update UI elements based on settings
        self.hint_button.setVisible(hints_enabled)
        self.deal_button.setVisible(not autodeal_enabled)
        self.set_button.setVisible(set_button_enabled)

    def show_game_over(self):
        """Show game over dialog with statistics."""
        stats = self.game.get_game_statistics()
        
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle("Game Over!")
        msg.setText(f"Congratulations! You've completed the game.\n\n"
                   f"Time: {stats['time_elapsed']}\n"
                   f"Sets Found: {stats['sets_found']}\n"
                   f"Final Score: {stats['final_score']}\n"
                   f"Accuracy Rate: {stats['accuracy_rate']:.1f}%")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.buttonClicked.connect(self.new_game)
        msg.exec()
    
    def keyPressEvent(self, event):
        """Handle keyboard events."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Enter key pressed - submit set if 3 cards selected
            if len(self.game.selected) == 3:
                self.submit_set()
        else:
            super().keyPressEvent(event)


def run_gui():
    """Entry point for GUI mode."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = SetGameGUI()
    window.show()
    
    sys.exit(app.exec())
