from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter
from typing import List, Optional
from gui.card_renderer import CardRenderer
from gui.widgets.card_item import CardItem


class BoardWidget(QGraphicsView):
    """Main game board displaying cards in a grid layout."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up the scene
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Card management
        self.card_renderer = CardRenderer()
        self.card_items: List[CardItem] = []
        
        # Layout settings
        self.cards_per_row = 4
        self.card_spacing = 15
        self.card_size = self.card_renderer.get_card_size()
        
        # View settings
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Set minimum size to show at least 3x4 grid
        min_width = self.cards_per_row * (self.card_size.width() + self.card_spacing) + self.card_spacing
        min_height = 3 * (self.card_size.height() + self.card_spacing) + self.card_spacing
        self.setMinimumSize(min_width, min_height)
        
        # Background
        self.setStyleSheet("background-color: #2a4d3a;")  # Dark green felt color
    
    def display_cards(self, card_indices: List[int]):
        """Display a list of cards on the board."""
        self.clear_board()
        
        # Calculate optimal layout
        total_cards = len(card_indices)
        if total_cards <= 12:
            # Standard 4x3 layout
            self._display_cards_in_grid(card_indices, 4, 3)
        elif total_cards == 15:
            # 5x3 layout for 15 cards
            self._display_cards_in_grid(card_indices, 5, 3)
        else:
            # Multi-column layout for more cards
            self._display_multi_column_layout(card_indices)
    
        
    def _display_cards_in_grid(self, card_indices: List[int], cols: int, rows: int):
        """Display cards in a grid layout."""
        for i, card_index in enumerate(card_indices):
            if card_index < 0 or card_index >= 81:
                continue
                
            # Get card pixmap
            pixmap = self.card_renderer.get_card_pixmap(card_index)
            
            # Create card item
            card_item = CardItem(pixmap, card_index)
            card_item.set_board_position(i)
            
            # Calculate position
            row = i // cols
            col = i % cols
            x = self.card_spacing + col * (self.card_size.width() + self.card_spacing)
            y = self.card_spacing + row * (self.card_size.height() + self.card_spacing)
            
            # Add to scene
            self.scene.addItem(card_item)
            card_item.setPos(x, y)
            self.card_items.append(card_item)
    
    def _display_multi_column_layout(self, card_indices: List[int]):
        """Display cards in optimized multi-column layout."""
        total_cards = len(card_indices)
        
        # Calculate optimal columns and rows
        if total_cards <= 16:
            cols = 4
            rows = (total_cards + 3) // 4  # Round up
        elif total_cards <= 21:
            cols = 5
            rows = (total_cards + 4) // 5
        else:
            cols = 6
            rows = (total_cards + 5) // 6
        
        # Calculate board dimensions
        board_width = cols * (self.card_size.width() + self.card_spacing) + self.card_spacing
        board_height = rows * (self.card_size.height() + self.card_spacing) + self.card_spacing
        
        # Calculate centering offset with better handling for 15 cards
        view_width = self.width() if hasattr(self, 'width') else 800
        view_height = self.height() if hasattr(self, 'height') else 600
        
        # For 15 cards (5x3), ensure better centering
        if total_cards == 15:
            x_offset = max(0, (view_width - board_width) // 2)
            y_offset = max(0, (view_height - board_height) // 2)
        else:
            x_offset = max(0, (view_width - board_width) // 2)
            y_offset = max(0, (view_height - board_height) // 2)
        
        # Place cards
        for i, card_index in enumerate(card_indices):
            if card_index < 0 or card_index >= 81:
                continue
                
            # Get card pixmap
            pixmap = self.card_renderer.get_card_pixmap(card_index)
            
            # Create card item
            card_item = CardItem(pixmap, card_index)
            card_item.set_board_position(i)
            
            # Calculate position
            row = i // cols
            col = i % cols
            x = x_offset + self.card_spacing + col * (self.card_size.width() + self.card_spacing)
            y = y_offset + self.card_spacing + row * (self.card_size.height() + self.card_spacing)
            
            # Add to scene
            self.scene.addItem(card_item)
            card_item.setPos(x, y)
            self.card_items.append(card_item)
    
    def _center_board(self):
        """Center the board in the view."""
        if not self.card_items:
            return
        
        # Calculate bounding rectangle of all cards
        min_x = min(item.pos().x() for item in self.card_items)
        min_y = min(item.pos().y() for item in self.card_items)
        max_x = max(item.pos().x() + self.card_size.width() for item in self.card_items)
        max_y = max(item.pos().y() + self.card_size.height() for item in self.card_items)
        
        # Center the view on the cards
        board_width = max_x - min_x + self.card_spacing
        board_height = max_y - min_y + self.card_spacing
        
        view_width = self.width() if hasattr(self, 'width') else 800
        view_height = self.height() if hasattr(self, 'height') else 600
        
        x_offset = max(0, (view_width - board_width) // 2)
        y_offset = max(0, (view_height - board_height) // 2)
        
        # Update scene rect to be centered
        self.scene.setSceneRect(-x_offset, -y_offset, view_width, view_height)
    
    def clear_board(self):
        """Clear all cards from the board."""
        self.scene.clear()
        self.card_items.clear()
    
    def update_scene_rect(self):
        """Update the scene rectangle to fit all cards."""
        if not self.card_items:
            self.scene.setSceneRect(QRectF(0, 0, 100, 100))
            return
        
        # Calculate bounding rectangle
        max_row = (len(self.card_items) - 1) // self.cards_per_row
        max_col = min(len(self.card_items) % self.cards_per_row, self.cards_per_row) - 1
        if max_col < 0:
            max_col = self.cards_per_row - 1
        
        width = (max_col + 1) * (self.card_size.width() + self.card_spacing) + self.card_spacing
        height = (max_row + 1) * (self.card_size.height() + self.card_spacing) + self.card_spacing
        
        self.scene.setSceneRect(QRectF(0, 0, width, height))
    
    def get_card_item(self, board_position: int) -> Optional[CardItem]:
        """Get card item by board position."""
        if 0 <= board_position < len(self.card_items):
            return self.card_items[board_position]
        return None
    
    def get_selected_cards(self) -> List[int]:
        """Get indices of currently selected cards."""
        selected = []
        for i, card_item in enumerate(self.card_items):
            if card_item.is_selected:
                selected.append(i)
        return selected
    
    def clear_selection(self):
        """Clear all card selections."""
        for card_item in self.card_items:
            card_item.set_selected(False)
    
    def set_card_glowing(self, board_position: int, glowing: bool):
        """Set glowing state for a specific card."""
        card_item = self.get_card_item(board_position)
        if card_item:
            card_item.set_glowing(glowing)
    
    def clear_all_glowing(self):
        """Clear glowing state from all cards."""
        for card_item in self.card_items:
            card_item.set_glowing(False)
    
    def handle_card_selection(self, board_position: int, selected: bool):
        """Handle card selection by notifying parent window."""
        # Get the parent window (main GUI) and notify it of selection
        parent = self.scene().parent()
        
        if hasattr(parent, 'handle_card_selection'):
            parent.handle_card_selection(board_position, selected)
