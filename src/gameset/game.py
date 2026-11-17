import csv
import datetime
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .board import Board
from .card import Card, SHAPE_SYMBOLS, COLOR_SYMBOLS, SHADING_SYMBOLS
from .deck import create_deck, shuffle, deal
from .set_logic import is_set, find_set, find_all_sets, explain_not_set

TABLE_SIZE = 12

SET_POINTS = 10
HINT_PENALTY = 3
WRONG_PENALTY = 2

TIMED_LIMIT_SECONDS = 180


class GameMode(str, Enum):
    CLASSIC = 'classic'
    TIMED = 'timed'
    DAILY = 'daily'

    @property
    def label(self) -> str:
        return {
            GameMode.CLASSIC: 'Classic',
            GameMode.TIMED: f'Timed ({TIMED_LIMIT_SECONDS // 60} min)',
            GameMode.DAILY: 'Daily puzzle',
        }[self]


def daily_seed(day: datetime.date | None = None) -> int:
    """Seed shared by everyone playing the daily puzzle on a given date."""
    day = day or datetime.date.today()
    return int(day.strftime('%Y%m%d'))


@dataclass
class SubmitResult:
    valid: bool
    message: str


class Game:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self.mode = GameMode.CLASSIC
        self.seed: int | None = None
        self.deck: list[Card] = []
        self.table: list[Card] = []
        self.selected: set[int] = set()
        self.score = 0
        self.wrong_attempts = 0
        self.hints_used = 0
        self.found_sets: list[tuple[Card, Card, Card]] = []
        self.autodeal = False
        self.hint_enabled = True
        self.hint_mode: int = 3  # reveal 3, 2 or 1 card(s) of a SET
        self.set_button_enabled: bool = True  # False = auto-confirm when 3 cards are selected

        self.start_time: float | None = None
        self.elapsed_time: float = 0.0
        self.game_active: bool = False

    # ------------------------------------------------------------------ setup

    def new_game(self, mode: GameMode | str | None = None, seed: int | None = None) -> None:
        if mode is not None:
            self.mode = GameMode(mode)
        if seed is None and self.mode is GameMode.DAILY:
            seed = daily_seed()
        self.seed = seed

        self.deck = create_deck()
        shuffle(self.deck, random.Random(seed) if seed is not None else None)
        self.table = deal(self.deck, TABLE_SIZE)
        self.selected.clear()
        self.score = 0
        self.wrong_attempts = 0
        self.hints_used = 0
        self.found_sets.clear()

        self.start_time = self._clock()
        self.elapsed_time = 0.0
        self.game_active = True

        self._auto_deal_if_needed()

    def set_options(self, autodeal: bool | None = None, hint_enabled: bool | None = None) -> None:
        if autodeal is not None:
            self.autodeal = autodeal
        if hint_enabled is not None:
            self.hint_enabled = hint_enabled
        self._auto_deal_if_needed()

    def set_hint_mode(self, mode: int) -> None:
        """Set hint mode: 3 (3 cards), 2 (2 cards), or 1 (1 card)."""
        if mode in (1, 2, 3):
            self.hint_mode = mode

    # ------------------------------------------------------------- gameplay

    @property
    def sets_found(self) -> int:
        return len(self.found_sets)

    def select_cards(self, indices: list[int]) -> None:
        """Replace the selection. Raises ValueError for unknown or repeated positions."""
        if len(set(indices)) != len(indices):
            raise ValueError('Each card can only be selected once.')
        for index in indices:
            if not 0 <= index < len(self.table):
                raise ValueError(f'There is no card {index + 1} on the table.')
        self.selected = set(indices)

    def toggle_selection(self, index: int) -> bool:
        """Select or deselect one card. Returns False if the change is not allowed."""
        if not 0 <= index < len(self.table):
            return False
        if index in self.selected:
            self.selected.discard(index)
            return True
        if len(self.selected) >= 3:
            return False
        self.selected.add(index)
        return True

    def submit_set(self) -> SubmitResult:
        if not self.game_active:
            return SubmitResult(False, 'The game is over.')
        if len(self.selected) != 3:
            return SubmitResult(False, 'Select exactly 3 cards.')
        chosen = sorted(self.selected)
        c1, c2, c3 = (self.table[i] for i in chosen)
        self.selected.clear()

        if not is_set(c1, c2, c3):
            self.wrong_attempts += 1
            self.score -= WRONG_PENALTY
            return SubmitResult(False, explain_not_set(c1, c2, c3))

        self.score += SET_POINTS
        self.found_sets.append((c1, c2, c3))
        if len(self.table) <= TABLE_SIZE and self.deck:
            # Refill in place so the remaining cards keep their positions.
            new_cards = deal(self.deck, 3)
            for index, card in zip(chosen, new_cards):
                self.table[index] = card
            for index in reversed(chosen[len(new_cards):]):
                del self.table[index]
        else:
            for index in reversed(chosen):
                del self.table[index]

        self._auto_deal_if_needed()
        self._check_finished()
        return SubmitResult(True, 'SET!')

    def deal_more(self) -> bool:
        if not self.game_active or not self.deck:
            return False
        self.table.extend(deal(self.deck, 3))
        self.selected.clear()
        self._auto_deal_if_needed()
        return True

    def get_hint(self) -> tuple[int, int, int] | None:
        return find_set(self.table)

    def get_hint_cards(self) -> list[int]:
        """Positions of the cards to reveal for the current hint mode. Costs points."""
        if not self.hint_enabled or not self.game_active:
            return []
        hint = self.get_hint()
        if not hint:
            return []
        self.hints_used += 1
        self.score -= HINT_PENALTY
        return list(hint[:self.hint_mode])

    def available_set_count(self) -> int:
        return len(find_all_sets(self.table))

    def _auto_deal_if_needed(self) -> None:
        while self.autodeal and self.deck and find_set(self.table) is None:
            self.table.extend(deal(self.deck, 3))
            self.selected.clear()

    # ------------------------------------------------------- time and end

    def get_elapsed_time(self) -> float:
        if not self.game_active or self.start_time is None:
            return self.elapsed_time
        return self._clock() - self.start_time

    def time_remaining(self) -> float | None:
        """Seconds left in a timed game, or None for untimed modes."""
        if self.mode is not GameMode.TIMED:
            return None
        return max(0.0, TIMED_LIMIT_SECONDS - self.get_elapsed_time())

    def get_formatted_time(self) -> str:
        remaining = self.time_remaining()
        seconds = int(remaining if remaining is not None else self.get_elapsed_time())
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def is_game_over(self) -> bool:
        if not self.table and not self.deck:
            return True
        if self.mode is GameMode.TIMED and self.time_remaining() == 0:
            return True
        return not self.deck and find_set(self.table) is None

    def check_time(self) -> bool:
        """Call periodically; ends a timed game when time runs out. Returns True if it just ended."""
        if self.game_active and self.mode is GameMode.TIMED and self.time_remaining() == 0:
            self._finish()
            return True
        return False

    def _check_finished(self) -> None:
        if self.game_active and self.is_game_over():
            self._finish()

    def _finish(self) -> None:
        elapsed = self.get_elapsed_time()
        if self.mode is GameMode.TIMED:
            elapsed = min(elapsed, TIMED_LIMIT_SECONDS)
        self.elapsed_time = elapsed
        self.game_active = False
        self.selected.clear()

    # ------------------------------------------------------------- reporting

    def get_board_display(self) -> str:
        return Board(self.table).render(self.selected)

    def accuracy(self) -> float:
        """Percentage of submitted selections that were valid SETs."""
        attempts = self.sets_found + self.wrong_attempts
        return 100.0 * self.sets_found / attempts if attempts else 0.0

    def get_game_statistics(self) -> dict:
        return {
            'mode': self.mode.label,
            'time_elapsed': self.get_formatted_time() if self.mode is not GameMode.TIMED
            else f"{int(self.elapsed_time) // 60:02d}:{int(self.elapsed_time) % 60:02d}",
            'sets_found': self.sets_found,
            'final_score': self.score,
            'wrong_attempts': self.wrong_attempts,
            'hints_used': self.hints_used,
            'cards_remaining': len(self.deck),
            'accuracy_rate': self.accuracy(),
        }

    def export_table_csv(self, filename: str) -> None:
        """Export the current table to CSV, including numeric values and identified solutions."""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Shape', 'Color', 'Number', 'Shading',
                             'Shape-Digit', 'Color-Digit', 'Number-Digit', 'Shading-Digit'])
            for idx, (shape, color, number, shading) in enumerate(self.table, start=1):
                writer.writerow([idx, SHAPE_SYMBOLS[shape], COLOR_SYMBOLS[color], number + 1,
                                 SHADING_SYMBOLS[shading], shape, color, number, shading])
            writer.writerow([])
            writer.writerow(['Solutions identified:'])
            solutions = find_all_sets(self.table)
            if not solutions:
                writer.writerow(['None'])
            else:
                writer.writerow(['Solution', 'Card 1', 'Card 2', 'Card 3'])
                for solution_index, (a, b, c) in enumerate(solutions, start=1):
                    writer.writerow([solution_index, a + 1, b + 1, c + 1])
