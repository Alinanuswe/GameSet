import csv
import time
from deck import create_deck, shuffle, deal
from card import Card, SHAPE_SYMBOLS, COLOR_SYMBOLS, SHADING_SYMBOLS
from set_logic import is_set, find_set, find_all_sets
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
        
        # Timer support
        self.start_time: float | None = None
        self.elapsed_time: float = 0.0
        
        # GUI-specific state
        self.found_sets: list[tuple[int, int, int]] = []  # Store found sets for sidebar display
        self.hint_mode: int = 3  # 3 cards, 2 cards, or 1 card hint
        self.set_button_enabled: bool = True  # Whether Set button is shown
        self.game_active: bool = False  # Whether a game is currently active

    def new_game(self) -> None:
        self.deck = create_deck()
        shuffle(self.deck)
        self.table = deal(self.deck, 12)
        self.selected.clear()
        self.score = 0
        self.sets_found = 0
        self.board = Board(self.table)
        
        # Reset timer
        self.start_time = time.time()
        self.elapsed_time = 0.0
        
        # Reset GUI-specific state
        self.found_sets.clear()
        self.game_active = True
        
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
            
            # Record found set for GUI sidebar display
            self.found_sets.append(tuple(chosen))
            
            self.table = [card for idx, card in enumerate(self.table) if idx not in chosen]
            
            # Apply SET game rules for dealing cards
            # Only deal cards if remaining cards < 12, or if remaining >= 12 but no sets available
            remaining_cards = len(self.table)
            if remaining_cards < 12:
                # Deal enough cards to get back to 12 (or as many as available)
                cards_needed = 12 - remaining_cards
                cards_to_deal = min(cards_needed, len(self.deck))
                if cards_to_deal > 0:
                    self.table.extend(deal(self.deck, cards_to_deal))
            elif self.available_set_count() == 0 and self.deck:
                # No sets available with 12+ cards, deal 3 more
                self.table.extend(deal(self.deck, 3))
            
            self.board = Board(self.table)
            self.selected.clear()
            self._auto_deal_if_needed()
            
            # Check if game is over
            if self.is_game_over():
                self.game_active = False
                self.elapsed_time = time.time() - (self.start_time or 0)
            
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

    def export_table_csv(self, filename: str) -> None:
        """Export the current table to CSV, including numeric values and identified solutions."""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'ID',
                'Shape',
                'Color',
                'Number',
                'Shading',
                'Shape-Digit',
                'Color-Digit',
                'Number-Digit',
                'Shading-Digit',
            ])
            for idx, card in enumerate(self.table, start=1):
                shape, color, number, shading = card
                writer.writerow([
                    idx,
                    SHAPE_SYMBOLS[shape],
                    COLOR_SYMBOLS[color],
                    number + 1,
                    SHADING_SYMBOLS[shading],
                    shape,
                    color,
                    number,
                    shading,
                ])
            writer.writerow([])
            writer.writerow(['Solutions identified:'])
            solutions = find_all_sets(self.table)
            if not solutions:
                writer.writerow(['None'])
            else:
                writer.writerow(['Solution', 'Card 1', 'Card 2', 'Card 3'])
                for solution_index, (a, b, c) in enumerate(solutions, start=1):
                    writer.writerow([solution_index, a + 1, b + 1, c + 1])

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

    # GUI-specific methods
    def get_elapsed_time(self) -> float:
        """Get the current elapsed time in seconds."""
        if not self.game_active:
            return self.elapsed_time
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def get_formatted_time(self) -> str:
        """Get the elapsed time formatted as MM:SS."""
        elapsed = self.get_elapsed_time()
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def set_hint_mode(self, mode: int) -> None:
        """Set hint mode: 3 (3 cards), 2 (2 cards), or 1 (1 card)."""
        if mode in [1, 2, 3]:
            self.hint_mode = mode

    def get_hint_cards(self) -> list[int]:
        """Get hint cards based on current hint mode."""
        hint = self.get_hint()
        if not hint:
            return []
        
        if self.hint_mode == 3:
            return list(hint)
        elif self.hint_mode == 2:
            return list(hint[:2])
        else:  # hint_mode == 1
            return [hint[0]]

    def get_card_by_index(self, index: int) -> Card | None:
        """Get card at specified index, safe for GUI access."""
        if 0 <= index < len(self.table):
            return self.table[index]
        return None

    def get_found_set_cards(self, set_index: int) -> list[Card] | None:
        """Get the cards for a previously found set by index."""
        if 0 <= set_index < len(self.found_sets):
            card_indices = self.found_sets[set_index]
            cards = []
            for idx in card_indices:
                if idx < len(self.table):  # Original card indices may be invalid after dealing
                    cards.append(self.table[idx])
            return cards if len(cards) == 3 else None
        return None

    def get_game_statistics(self) -> dict:
        """Get comprehensive game statistics for game over dialog."""
        return {
            'time_elapsed': self.get_formatted_time(),
            'sets_found': self.sets_found,
            'final_score': self.score,
            'cards_remaining': len(self.deck),
            'accuracy_rate': self._calculate_accuracy()
        }

    def _calculate_accuracy(self) -> float:
        """Calculate accuracy rate (successful sets / total attempts)."""
        # This would need to track failed attempts in a real implementation
        # For now, return a placeholder
        return 100.0 if self.sets_found > 0 else 0.0
