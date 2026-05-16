"""
Sidebar widget for SET game GUI.
Displays found sets in miniature form with scrollable history.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from typing import List, Dict
from gui.card_renderer import CardRenderer


class SidebarWidget(QWidget):
    """Sidebar widget for displaying found sets history."""
    
    # Signal for settings request
    settings_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Card renderer for miniature cards
        self.card_renderer = CardRenderer()
        self.found_sets: List[Dict] = []
        
        # Set up main layout
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)
        
        # Create sections
        #self.create_header_section()
        self.create_found_sets_section()
        self.create_controls_section()
        
        # Set sidebar styling
        self.setFixedWidth(260)
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
    
    def create_header_section(self):
        """Create header with title."""
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("Found Sets")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background-color: transparent;
                border: none;
                padding: 8px;
            }
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        self.main_layout.addLayout(header_layout)
    
    def create_found_sets_section(self):
        """Create scrollable found sets display section."""
        # Scrollable history area
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        #self.history_scroll.setFixedHeight(400)
        self.history_scroll.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin: 5px;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #6c757d;
                border-radius: 6px;
                min-height: 20px;
            }
        """)
        
        self.history_widget = QWidget()
        self.history_layout = QVBoxLayout(self.history_widget)
        self.history_layout.setSpacing(10)
        
        # Add empty state message
        self.empty_label = QLabel("No sets found yet")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-style: italic;
                padding: 20px;
            }
        """)
        self.history_layout.addWidget(self.empty_label)
        
        self.history_widget.setLayout(self.history_layout)
        self.history_scroll.setWidget(self.history_widget)
        
        self.main_layout.addWidget(self.history_scroll)
    
    def create_controls_section(self):
        """Create control buttons section."""
        # No control buttons - only display found sets
        pass
    
    def add_found_set(self, cards: List[int], timestamp: str = None):
        """Add a found set to the history."""
        import time
        
        set_data = {
            'cards': cards,
            'timestamp': timestamp or time.strftime("%H:%M:%S"),
            'set_number': len(self.found_sets) + 1
        }
        
        self.found_sets.append(set_data)
        self.update_history_display()
    
    def update_history_display(self):
        """Update the found sets history display."""
        # Clear existing widgets except empty label
        for i in reversed(range(self.history_layout.count())):
            item = self.history_layout.itemAt(i)
            widget = item.widget() if item else None
            if widget and widget != self.empty_label:
                self.history_layout.removeItem(item)
                widget.deleteLater()
        
        # Hide empty label if there are sets
        if self.found_sets:
            self.empty_label.hide()
        else:
            self.empty_label.show()
            return
        
        # Add recent sets (show most recent first)
        for set_data in reversed(self.found_sets):
            set_widget = self.create_set_widget(set_data)
            self.history_layout.addWidget(set_widget)
        
        # Scroll to top to show latest set
        self.history_scroll.ensureVisible(0, 0)
    
    def create_set_widget(self, set_data: Dict) -> QWidget:
        """Create a widget for displaying a single found set."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)
        
        # Card display area
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(5)
        
        # Create miniature card representations
        for card_pos in set_data['cards']:
            card_label = self.create_miniature_card(card_pos)
            cards_layout.addWidget(card_label)
        
        layout.addLayout(cards_layout)
        
        # Set widget styling
        widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin: 2px;
            }
        """)
        
        return widget
    
    def create_miniature_card(self, card_index: int) -> QLabel:
        """Create a miniature card representation using actual card image."""
        card_label = QLabel()
        card_label.setFixedSize(60, 40)
        card_label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border: 1px solid #6c757d;
                border-radius: 2px;
            }
        """)
        
        # Get the actual card pixmap from the card renderer
        try:
            # Get the card pixmap and scale it to miniature size
            original_pixmap = self.card_renderer.get_card_pixmap(card_index)
            miniature_pixmap = original_pixmap.scaled(60, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            card_label.setPixmap(miniature_pixmap)
        except Exception as e:
            # Fallback: show the card index if image loading fails
            card_label.setText(str(card_index))
            card_label.setAlignment(Qt.AlignCenter)
            card_label.setStyleSheet("""
                QLabel {
                    background-color: #f8f9fa;
                    border: 1px solid #6c757d;
                    border-radius: 2px;
                    color: #495057;
                    font-size: 8px;
                    font-weight: bold;
                }
            """)
        
        return card_label
    
    def toggle_visibility(self):
        """Toggle the visibility of the found sets history."""
        if self.history_scroll.isVisible():
            self.history_scroll.hide()
            self.toggle_button.setText("Show Found Sets")
        else:
            self.history_scroll.show()
            self.toggle_button.setText("Hide Found Sets")
    
    def clear_history(self):
        """Clear the found sets history."""
        self.found_sets.clear()
        self.update_history_display()
    
    def get_found_sets_count(self) -> int:
        """Get the number of found sets."""
        return len(self.found_sets)
