from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QPixmap, QPen, QBrush, QColor, QFont, QPainterPath
from PySide6.QtWidgets import QApplication
import math


class CardRenderer:
    """Generates and caches all 81 SET game cards using base-3 indexing."""
    
    # Card dimensions
    CARD_WIDTH = 120
    CARD_HEIGHT = 80
    
    # Colors for cards
    COLORS = [
        QColor(255, 0, 0),    # Red
        QColor(0, 128, 0),    # Green  
        QColor(128, 0, 128)   # Purple
    ]
    
    def __init__(self):
        self.card_pixmaps = []
        self._generate_all_cards()
    
    def _generate_all_cards(self):
        """Generate all 81 cards using base-3 indexing."""
        for index in range(81):
            pixmap = self._create_card_pixmap(index)
            self.card_pixmaps.append(pixmap)
    
    def _create_card_pixmap(self, index: int) -> QPixmap:
        """Create a single card pixmap from its base-3 index."""
        # Convert index to 4-digit base-3: shape, color, number, shading
        d3 = index // 27          # shape (0-2)
        d2 = (index % 27) // 9    # color (0-2)  
        d1 = (index % 9) // 3     # number (0-2)
        d0 = index % 3            # shading (0-2)
        
        shape, color, number, shading = d3, d2, d1, d0
        
        # Create pixmap
        pixmap = QPixmap(self.CARD_WIDTH, self.CARD_HEIGHT)
        pixmap.fill(Qt.white)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw card border
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(2, 2, self.CARD_WIDTH - 4, self.CARD_HEIGHT - 4)
        
        # Set up drawing properties
        color_obj = self.COLORS[color]
        painter.setPen(QPen(color_obj, 2))
        
        # Set brush based on shading
        if shading == 0:  # Empty
            painter.setBrush(Qt.NoBrush)
        elif shading == 1:  # Striped
            painter.setBrush(QBrush(color_obj, Qt.Dense4Pattern))
        else:  # Filled
            painter.setBrush(QBrush(color_obj))
        
        # Draw shapes based on number (1, 2, or 3)
        self._draw_shapes(painter, shape, number + 1)
        
        painter.end()
        return pixmap
    
    def _draw_shapes(self, painter: QPainter, shape_type: int, count: int):
        """Draw the specified number of shapes on the card."""
        # Calculate shape dimensions
        shape_width = 25
        shape_height = 50
        spacing = 5
        
        # Calculate total width occupied by shapes
        total_shapes_width = count * shape_width + (count - 1) * spacing
        
        # Calculate horizontal centering offset
        available_width = self.CARD_WIDTH - 20  # Leave 10px margin on each side
        x_offset = (available_width - total_shapes_width) // 2
        
        # Calculate vertical centering offset
        y_center = self.CARD_HEIGHT // 2
        y_offset = y_center - (shape_height // 2) + 8  # Move shapes down to reduce space above
        
        # Starting X position (centered horizontally)
        start_x = 10 + x_offset
        
        for i in range(count):
            x = start_x + i * (shape_width + spacing)
            
            if shape_type == 0:  # Oval
                self._draw_oval(painter, x, y_center - y_offset, shape_width, shape_height)
            elif shape_type == 1:  # Diamond
                self._draw_diamond(painter, x, y_center - y_offset, shape_width, shape_height)
            else:  # RoundedRect (shape_type == 2)
                self._draw_rounded_rect(painter, x, y_center - y_offset, shape_width, shape_height)
    
    def _draw_oval(self, painter: QPainter, x: int, y: int, width: int, height: int):
        """Draw an oval shape."""
        painter.drawEllipse(x, y, width, height)
    
    def _draw_diamond(self, painter: QPainter, x: int, y: int, width: int, height: int):
        """Draw a diamond shape using a polygon."""
        path = QPainterPath()
        center_x = x + width // 2
        center_y = y + height // 2
        
        path.moveTo(center_x, y)  # Top point
        path.lineTo(x + width, center_y)  # Right point
        path.lineTo(center_x, y + height)  # Bottom point
        path.lineTo(x, center_y)  # Left point
        path.closeSubpath()
        
        painter.drawPath(path)
    
    def _draw_rounded_rect(self, painter: QPainter, x: int, y: int, width: int, height: int):
        """Draw a rounded rectangle shape."""
        painter.drawRoundedRect(x, y, width, height, 5, 5)
    
    def get_card_pixmap(self, index: int) -> QPixmap:
        """Get the pixmap for a card by its index (0-80)."""
        if 0 <= index < len(self.card_pixmaps):
            return self.card_pixmaps[index]
        raise ValueError(f"Card index {index} out of range (0-80)")
    
    def get_card_size(self) -> QSize:
        """Get the standard card size."""
        return QSize(self.CARD_WIDTH, self.CARD_HEIGHT)
    
    @staticmethod
    def index_to_card_tuple(index: int) -> tuple:
        """Convert card index to (shape, color, number, shading) tuple."""
        d3 = index // 27          # shape (0-2)
        d2 = (index % 27) // 9    # color (0-2)
        d1 = (index % 9) // 3     # number (0-2)
        d0 = index % 3            # shading (0-2)
        return (d3, d2, d1, d0)
