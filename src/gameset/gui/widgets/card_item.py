from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsSimpleTextItem


class CardItem(QGraphicsPixmapItem):
    """One card on the board. It only displays state; the Game decides what is selected."""

    def __init__(self, pixmap: QPixmap, card_index: int, board_position: int,
                 key_label: str, on_click: Callable[[int], None]) -> None:
        super().__init__(pixmap)
        self.card_index = card_index
        self.board_position = board_position
        self._on_click = on_click
        self.setTransformationMode(Qt.SmoothTransformation)
        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptHoverEvents(True)
        self._hovered = False
        self._state = 'normal'
        self._colors = {'normal': QColor(Qt.black)}

        self.highlight_rect = QGraphicsRectItem(self.boundingRect().adjusted(2, 2, -2, -2), self)
        self.highlight_rect.setBrush(Qt.NoBrush)

        # Keyboard shortcut shown in the top-left corner.
        self.key_text = QGraphicsSimpleTextItem(key_label, self)
        font = QFont()
        font.setPixelSize(int(pixmap.height() * 0.13))
        font.setBold(True)
        self.key_text.setFont(font)
        self.key_text.setBrush(QBrush(QColor('#8a9097')))
        self.key_text.setPos(pixmap.height() * 0.06, pixmap.height() * 0.03)

        self._apply()

    def set_colors(self, colors: dict[str, QColor]) -> None:
        self._colors = {'normal': QColor(Qt.black), **colors}
        self._apply()

    def set_state(self, state: str) -> None:
        """One of: normal, selected, hint, error, success."""
        if state != self._state:
            self._state = state
            self._apply()

    @property
    def state(self) -> str:
        return self._state

    def _apply(self) -> None:
        width = 3 if self._state == 'normal' else 8
        color = self._colors.get(self._state, QColor(Qt.black))
        if self._state == 'normal' and self._hovered:
            color, width = QColor('#7a8a99'), 5
        self.highlight_rect.setPen(QPen(color, width))

    def hoverEnterEvent(self, event):
        self._hovered = True
        self._apply()

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self._apply()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._on_click(self.board_position)
            event.accept()
        else:
            super().mousePressEvent(event)
