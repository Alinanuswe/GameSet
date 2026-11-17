from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPixmap

from ..card import DECK_SIZE, index_to_card


class CardRenderer:
    """Generates and caches all 81 SET game cards using base-3 indexing."""

    # Logical card size. Pixmaps are drawn at SCALE times this so they stay sharp
    # when the board is scaled up to fill a large window.
    CARD_WIDTH = 120
    CARD_HEIGHT = 80
    SCALE = 2

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
        for index in range(DECK_SIZE):
            pixmap = self._create_card_pixmap(index)
            self.card_pixmaps.append(pixmap)

    def _create_card_pixmap(self, index: int) -> QPixmap:
        """Create a single card pixmap from its base-3 index."""
        shape, color, number, shading = index_to_card(index)

        pixmap = QPixmap(self.CARD_WIDTH * self.SCALE, self.CARD_HEIGHT * self.SCALE)
        pixmap.fill(Qt.white)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(self.SCALE, self.SCALE)

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
            # Create custom horizontal line pattern
            pattern = QPixmap(4, 4)
            pattern.fill(Qt.transparent)
            pattern_painter = QPainter(pattern)
            pattern_painter.setPen(QPen(color_obj, 1))
            pattern_painter.drawLine(0, 1, 4, 1)
            pattern_painter.end()
            painter.setBrush(QBrush(pattern))
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
            else:  # Squiggle (shape_type == 2)
                self._draw_squiggle(painter, x, y_center - y_offset, shape_width, shape_height)

    def _draw_oval(self, painter: QPainter, x: float, y: float, width: float, height: float):
        """Draw an oval: a pill shape with straight sides and fully rounded ends."""
        radius = width / 2
        painter.drawRoundedRect(QRectF(x, y, width, height), radius, radius)

    def _draw_diamond(self, painter: QPainter, x: float, y: float, width: float, height: float):
        """Draw a diamond shape using a polygon."""
        path = QPainterPath()
        center_x = x + width / 2
        center_y = y + height / 2

        path.moveTo(center_x, y)  # Top point
        path.lineTo(x + width, center_y)  # Right point
        path.lineTo(center_x, y + height)  # Bottom point
        path.lineTo(x, center_y)  # Left point
        path.closeSubpath()

        painter.drawPath(path)

    # One edge of the squiggle, in a unit box where the squiggle lies horizontally:
    # start point, then (control 1, control 2, end) for each cubic curve. The other
    # edge is this one rotated 180 degrees, which makes the shape point-symmetric.
    _SQUIGGLE_EDGE = (
        (0.03, 0.92),
        ((0.00, 0.25), (0.25, -0.05), (0.48, 0.25)),
        ((0.64, 0.46), (0.90, -0.35), (0.97, 0.08)),
    )

    def _draw_squiggle(self, painter: QPainter, x: float, y: float, width: float, height: float):
        """Draw a squiggle: a wavy shape with rounded, offset ends."""

        def point(u: float, v: float) -> QPointF:
            # The unit box is horizontal; stand it upright to fit the shape's box.
            return QPointF(x + v * width, y + u * height)

        def rotated(u: float, v: float) -> QPointF:
            return point(1 - u, 1 - v)

        start, *curves = self._SQUIGGLE_EDGE
        path = QPainterPath(point(*start))
        for c1, c2, end in curves:
            path.cubicTo(point(*c1), point(*c2), point(*end))
        for c1, c2, end in curves:
            path.cubicTo(rotated(*c1), rotated(*c2), rotated(*end))
        path.closeSubpath()

        painter.drawPath(path)

    def get_card_pixmap(self, index: int) -> QPixmap:
        """Get the pixmap for a card by its index (0-80)."""
        if 0 <= index < len(self.card_pixmaps):
            return self.card_pixmaps[index]
        raise ValueError(f"Card index {index} out of range (0-80)")

    def get_card_size(self) -> QSize:
        """Size of a card pixmap in pixels."""
        return QSize(self.CARD_WIDTH * self.SCALE, self.CARD_HEIGHT * self.SCALE)


_shared: CardRenderer | None = None


def shared_renderer() -> CardRenderer:
    """One renderer for the whole app, so the 81 card images are only drawn once."""
    global _shared
    if _shared is None:
        _shared = CardRenderer()
    return _shared
