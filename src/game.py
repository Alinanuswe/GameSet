from deck import create_deck, shuffle, deal
from card import Card
from set_logic import is_set, find_set
from board import Board


class Game:
    def __init__(self) -> None:
        self.deck: list[Card] = []
        self.table: list[Card] = []
        self.selected: set[int] = set()
        self.score = 0
        self.sets_found = 0
        self.board: Board | None = None
        self.autodeal = False
        self.hint_enabled = True

    def new_game(self) -> None:
        self.deck = create_deck()
        shuffle(self.deck)
        self.table = deal(self.deck, 12)
        self.selected.clear()
        self.score = 0
        self.sets_found = 0
        self.board = Board(self.table)
        self._auto_deal_if_needed()

    def set_options(self, autodeal: bool | None = None, hint_enabled: bool | None = None) -> None:
        if autodeal is not None:
            self.autodeal = autodeal
        if hint_enabled is not None:
            self.hint_enabled = hint_enabled
        self._auto_deal_if_needed()

    def _auto_deal_if_needed(self) -> None:
        while self.autodeal and self.deck and self.available_set_count() == 0:
            self.table.extend(deal(self.deck, 3))
            self.board = Board(self.table)
            self.selected.clear()

    def select_cards(self, indices: list[int]) -> None:
        self.selected.clear()
        for index in indices:
            if 0 <= index < len(self.table):
                self.selected.add(index)

    def submit_set(self) -> bool:
        if len(self.selected) != 3:
            return False
        chosen = sorted(self.selected)
        c1, c2, c3 = (self.table[i] for i in chosen)
        if is_set(c1, c2, c3):
            self.sets_found += 1
            self.score += 1
            self.table = [card for idx, card in enumerate(self.table) if idx not in chosen]
            self.table.extend(deal(self.deck, 3))
            self.board = Board(self.table)
            self.selected.clear()
            self._auto_deal_if_needed()
            return True
        self.selected.clear()
        return False

    def deal_more(self) -> None:
        self.table.extend(deal(self.deck, 3))
        self.board = Board(self.table)
        self.selected.clear()
        self._auto_deal_if_needed()

    def get_hint(self) -> tuple[int, int, int] | None:
        return find_set(self.table)

    def is_game_over(self) -> bool:
        if self.board is None:
            return True
        if self.deck:
            return False
        return find_set(self.table) is None

    def get_board_display(self) -> str:
        if self.board is None:
            return ''
        return self.board.render(self.selected)

    def available_set_count(self) -> int:
        count = 0
        table_len = len(self.table)
        for a in range(table_len - 2):
            for b in range(a + 1, table_len - 1):
                for c in range(b + 1, table_len):
                    if is_set(self.table[a], self.table[b], self.table[c]):
                        count += 1
        return count
