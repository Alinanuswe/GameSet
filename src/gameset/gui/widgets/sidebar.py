"""Sidebar listing the SETs found this game, most recent first."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from ...card import Card, card_to_index, describe_card
from ..card_renderer import shared_renderer

MINI_WIDTH = 60
MINI_HEIGHT = 40


class SidebarWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('sidebar')
        self.setFixedWidth(250)
        self.card_renderer = shared_renderer()
        self.found_sets: list[tuple[tuple[Card, ...], str]] = []

        layout = QVBoxLayout(self)
        self.title = QLabel('Found SETs')
        self.title.setStyleSheet('font-weight: bold; font-size: 11pt; border: none;')
        layout.addWidget(self.title)

        self.history_scroll = QScrollArea()
        self.history_scroll.setObjectName('history')
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_widget = QWidget()
        self.history_widget.setObjectName('historyContents')
        self.history_layout = QVBoxLayout(self.history_widget)
        self.history_layout.setAlignment(Qt.AlignTop)
        self.empty_label = QLabel('No SETs found yet')
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet('font-style: italic; padding: 20px; border: none;')
        self.history_layout.addWidget(self.empty_label)
        self.history_scroll.setWidget(self.history_widget)
        layout.addWidget(self.history_scroll)

    def add_found_set(self, cards: tuple[Card, ...], timestamp: str) -> None:
        self.found_sets.append((cards, timestamp))
        self.empty_label.hide()
        self.history_layout.insertWidget(0, self._create_set_widget(len(self.found_sets), cards, timestamp))
        self.title.setText(f'Found SETs ({len(self.found_sets)})')
        self.history_scroll.verticalScrollBar().setValue(0)

    def _create_set_widget(self, number: int, cards: tuple[Card, ...], timestamp: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        header = QLabel(f'#{number}  ·  {timestamp}')
        header.setStyleSheet('font-size: 8pt; border: none;')
        layout.addWidget(header)
        row = QHBoxLayout()
        row.setSpacing(4)
        for card in cards:
            label = QLabel()
            label.setFixedSize(MINI_WIDTH, MINI_HEIGHT)
            label.setPixmap(self.card_renderer.get_card_pixmap(card_to_index(card))
                            .scaled(MINI_WIDTH, MINI_HEIGHT, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            label.setToolTip(describe_card(card))
            row.addWidget(label)
        row.addStretch()
        layout.addLayout(row)
        return widget

    def clear_history(self) -> None:
        self.found_sets.clear()
        while self.history_layout.count() > 1:
            item = self.history_layout.takeAt(0)
            if item.widget() is self.empty_label:
                self.history_layout.addWidget(self.empty_label)
                continue
            item.widget().deleteLater()
        self.empty_label.show()
        self.title.setText('Found SETs')
