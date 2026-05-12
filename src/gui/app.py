import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QBrush, QColor, QPen
from game import Game
from gui.widgets.board_widget import BoardWidget


class SetGameGUI(QMainWindow):
    """Main application window for the SET game GUI."""
    
    def __init__(self):
        super().__init__()
        
        # Game instance
        self.game = Game()
        
        # Set up window
        self.setWindowTitle("SET Game")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create top info bar
        self.create_info_bar(main_layout)
        
        # Create board widget
        self.board_widget = BoardWidget()
        # Set the scene parent to this window for card selection handling
        self.board_widget.scene.setParent(self)
        main_layout.addWidget(self.board_widget, 1)  # Takes most space
        
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
        self.timer_label = QLabel("Time: 00:00")
        
        # Set font
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        
        for label in [self.score_label, self.sets_label, self.deck_label, 
                     self.available_sets_label, self.timer_label]:
            label.setFont(font)
            label.setStyleSheet("color: white; background-color: #1a3d2a; padding: 5px; border-radius: 3px;")
        
        # Add to layout
        info_layout.addWidget(self.score_label)
        info_layout.addWidget(self.sets_label)
        info_layout.addWidget(self.deck_label)
        info_layout.addWidget(self.available_sets_label)
        info_layout.addStretch()
        info_layout.addWidget(self.timer_label)
        
        layout.addLayout(info_layout)
    
    def create_controls(self, layout):
        """Create the bottom control buttons."""
        controls_layout = QHBoxLayout()
        
        # Deal button
        self.deal_button = QPushButton("Deal 3 Cards")
        self.deal_button.clicked.connect(self.deal_cards)
        
        # Hint button
        self.hint_button = QPushButton("Hint")
        self.hint_button.clicked.connect(self.show_hint)
        
        # New Game button
        self.new_game_button = QPushButton("New Game")
        self.new_game_button.clicked.connect(self.new_game)
        
        # Set button (optional feature)
        self.set_button = QPushButton("Set")
        self.set_button.clicked.connect(self.submit_set)
        
        # Add to layout
        controls_layout.addWidget(self.deal_button)
        controls_layout.addWidget(self.hint_button)
        controls_layout.addWidget(self.set_button)
        controls_layout.addStretch()
        controls_layout.addWidget(self.new_game_button)
        
        layout.addLayout(controls_layout)
    
    def new_game(self):
        """Start a new game."""
        self.game.new_game()
        self.update_board()
        self.update_game_info()
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
    
    def submit_set(self):
        """Submit selected cards as a set."""
        if len(self.game.selected) != 3:
            return
        
        # Submit the set to game logic
        if self.game.submit_set():
            # Valid set - update board
            self.update_board()
            self.update_game_info()
            
            # Check if game is over
            if self.game.is_game_over():
                self.show_game_over()
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
    
    def show_game_over(self):
        """Show game over dialog with statistics."""
        stats = self.game.get_game_statistics()
        
        # Simple message box for now (will be enhanced in Phase 4)
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


def run_gui():
    """Entry point for GUI mode."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = SetGameGUI()
    window.show()
    
    sys.exit(app.exec())
