from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QGraphicsRectItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPixmap, QColor, QPen, QBrush
from typing import Optional


class CardItem(QGraphicsPixmapItem):
    """Represents a single card in the game board."""
    
    def __init__(self, pixmap: QPixmap, card_index: int, parent=None):
        super().__init__(pixmap, parent)
        self.card_index = card_index
        self.board_position = -1  # Position on the board (0-11+)
        self.is_selected = False
        self.is_glowing = False
        self.is_in_error = False  # Track error state for invalid sets
        
        # Highlight border rectangle
        self.highlight_rect = QGraphicsRectItem(self.boundingRect(), self)
        self.highlight_rect.setPen(QPen(Qt.black, 3))  # Default black border
        self.highlight_rect.setBrush(Qt.NoBrush)
        self.highlight_rect.setVisible(True)  # Always visible for border
        
        # Enable mouse events
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        
        # Set cursor to pointing hand
        self.setCursor(Qt.PointingHandCursor)
    
    def mousePressEvent(self, event):
        """Handle mouse press events for card selection."""
        if event.button() == Qt.LeftButton:
            # Check if we're trying to select a 4th card
            if not self.is_selected:
                # Count currently selected cards
                selected_count = 0
                if self.scene():
                    for item in self.scene().items():
                        if hasattr(item, 'is_selected') and item.is_selected:
                            selected_count += 1
                
                # Prevent selecting 4th card
                if selected_count >= 3:
                    return  # Don't allow selection
            
            # Toggle selection
            self.is_selected = not self.is_selected
            self.update_selection_highlight()
            
            # Emit signal or notify parent (to be implemented in Phase 3)
            if self.scene() and self.scene().parent() is not None:
                self.scene().parent().handle_card_selection(self.board_position, self.is_selected)
            event.accept()
            return
    
    def set_board_position(self, position: int):
        """Set the card's position on the board."""
        self.board_position = position
    
    def set_selected(self, selected: bool):
        """Set the card's selection state."""
        if self.is_selected != selected:
            self.is_selected = selected
            self.update_selection_highlight()
    
    def set_glowing(self, glowing: bool):
        """Set the card's glowing state for hints."""
        if self.is_glowing != glowing:
            self.is_glowing = glowing
            self.update_selection_highlight()
    
    def update_selection_highlight(self):
        """Update the visual appearance based on selection and glow states."""
        if self.is_in_error:
            self.highlight_rect.setPen(QPen(QColor(255, 0, 0), 4))  # Red border for error
        elif self.is_selected:
            self.highlight_rect.setPen(QPen(QColor(0, 100, 255), 4))  # Blue border for selected
        elif self.is_glowing:
            self.highlight_rect.setPen(QPen(QColor(0, 255, 0), 3))  # Green border for hint glow
        else:
            self.highlight_rect.setPen(QPen(Qt.black, 3))  # Black border for normal
    
    def reset_state(self):
        """Reset card to default state."""
        self.is_selected = False
        self.is_glowing = False
        self.is_in_error = False
        self.update_selection_highlight()
    
    def get_card_index(self) -> int:
        """Get the card's index (0-80)."""
        return self.card_index
    
    def get_board_position(self) -> int:
        """Get the card's position on the board."""
        return self.board_position
