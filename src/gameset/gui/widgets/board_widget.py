import math
from collections.abc import Set

from PySide6.QtCore import QEasingCurve, QRectF, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QBrush, QColor, QPainter
from PySide6.QtWidgets import QFrame, QGraphicsScene, QGraphicsView

from ...card import Card, card_to_index
from ..card_renderer import shared_renderer
from .card_item import CardItem

# Keys for picking cards, numbered down each column: 1-9, 0, then the QWERTY row, then A.
# Covers the 21-card maximum.
CARD_KEYS = list('1234567890QWERTYUIOPA')

ROWS = 3


class BoardWidget(QGraphicsView):
    """The table of cards. Scales to fill the available space."""

    card_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.card_renderer = shared_renderer()
        self.card_items: list[CardItem] = []
        self.card_size = self.card_renderer.get_card_size()
        self.card_spacing = self.card_size.width() // 8
        self._colors: dict[str, QColor] = {}
        self._animations: list[QVariantAnimation] = []

        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)  # keyboard shortcuts belong to the main window
        self.setMinimumSize(480, 300)

    def set_theme(self, felt: str, colors: dict[str, str]) -> None:
        self.setBackgroundBrush(QBrush(QColor(felt)))
        self._colors = {state: QColor(value) for state, value in colors.items()}
        for item in self.card_items:
            item.set_colors(self._colors)

    def display_cards(self, cards: list[Card], new_positions: Set[int] = frozenset()) -> None:
        """Lay out cards in 3 rows; cards at new_positions fade in."""
        for animation in self._animations:
            animation.stop()  # its card is about to be deleted
        self._animations.clear()
        self.scene.clear()
        self.card_items.clear()
        cols = max(4, math.ceil(len(cards) / ROWS))
        step_x = self.card_size.width() + self.card_spacing
        step_y = self.card_size.height() + self.card_spacing

        for position, card in enumerate(cards):
            index = card_to_index(card)
            key = CARD_KEYS[position] if position < len(CARD_KEYS) else ''
            item = CardItem(self.card_renderer.get_card_pixmap(index), index, position, key,
                            self.card_clicked.emit)
            item.set_colors(self._colors)
            # Fill column by column so extra cards add a column on the right without moving the rest.
            col, row = divmod(position, ROWS)
            item.setPos(col * step_x, row * step_y)
            self.scene.addItem(item)
            self.card_items.append(item)
            if position in new_positions:
                self._fade_in(item)

        width = cols * step_x - self.card_spacing
        height = ROWS * step_y - self.card_spacing
        margin = self.card_spacing
        self.scene.setSceneRect(QRectF(-margin, -margin, width + 2 * margin, height + 2 * margin))
        self._fit()

    def _fade_in(self, item: CardItem) -> None:
        item.setOpacity(0.0)
        animation = QVariantAnimation(self)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setDuration(350)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.valueChanged.connect(item.setOpacity)

        def forget():
            if animation in self._animations:
                self._animations.remove(animation)

        animation.finished.connect(forget)
        self._animations.append(animation)
        animation.start()

    def _fit(self) -> None:
        if not self.scene.sceneRect().isEmpty():
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit()

    def showEvent(self, event):
        super().showEvent(event)
        self._fit()

    def set_card_states(self, selected: set[int], overrides: dict[int, str] | None = None) -> None:
        """Highlight cards: overrides (hint/error/success) win over selection."""
        overrides = overrides or {}
        for position, item in enumerate(self.card_items):
            if position in overrides:
                item.set_state(overrides[position])
            elif position in selected:
                item.set_state('selected')
            else:
                item.set_state('normal')
