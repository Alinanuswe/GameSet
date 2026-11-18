import csv
import datetime
import math
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from .board import Board
from .card import COLOR_SYMBOLS, SHADING_SYMBOLS, SHAPE_SYMBOLS, Card
from .deck import create_deck, deal, shuffle
from .set_logic import explain_not_set, find_all_sets, find_set, is_set

TABLE_SIZE = 12

SET_POINTS = 10
HINT_PENALTY = 3
WRONG_PENALTY = 2

TIMED_LIMIT_SECONDS = 180

# Multiplayer: after a wrong guess a player must wait this long before claiming again.
WRONG_LOCKOUT_SECONDS = 3.0

# Stands in for the cards a LAN player cannot see: only the host knows the deck's order.
HIDDEN_CARD: Card = (0, 0, 0, 0)


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
    positions: tuple[int, ...] = ()
    cards: tuple[Card, ...] = ()
    player: int | None = None
    penalised: bool = False  # False when the guess was refused without counting (locked, too late)


@dataclass
class Player:
    name: str
    score: int = 0
    sets_found: int = 0
    wrong_attempts: int = 0
    locked_until: float = 0.0  # clock time until which this player cannot claim a SET

    def reset(self) -> None:
        self.score = self.sets_found = self.wrong_attempts = 0
        self.locked_until = 0.0


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
        self.found_by: list[int | None] = []  # player index for each found SET (None in single player)
        self.players: list[Player] = []  # empty in single player
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
        self.found_by.clear()
        for player in self.players:
            player.reset()

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

    # ----------------------------------------------------------- multiplayer

    @property
    def is_multiplayer(self) -> bool:
        return bool(self.players)

    def set_players(self, names: list[str]) -> None:
        """Play with these players (an empty list means single player). Takes effect immediately."""
        self.players = [Player(name) for name in names]

    def add_player(self, name: str) -> int:
        self.players.append(Player(name))
        return len(self.players) - 1

    def lockout_remaining(self, player: int) -> float:
        return max(0.0, self.players[player].locked_until - self._clock())

    def ranking(self) -> list[Player]:
        """Players from first to last: most points, then most SETs."""
        return sorted(self.players, key=lambda p: (-p.score, -p.sets_found))

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

    def submit_set(self, player: int | None = None) -> SubmitResult:
        """Check the selected cards. In multiplayer, `player` is who claimed them."""
        if not self.game_active:
            return SubmitResult(False, 'The game is over.')
        if len(self.selected) != 3:
            return SubmitResult(False, 'Select exactly 3 cards.')
        if self.is_multiplayer:
            if player is None or not 0 <= player < len(self.players):
                return SubmitResult(False, 'Choose which player found the SET.')
            wait = self.lockout_remaining(player)
            if wait > 0:
                return SubmitResult(False, f'{self.players[player].name} must wait {math.ceil(wait)}s '
                                    'after a wrong guess.', player=player)
        else:
            player = None
        chosen = sorted(self.selected)
        c1, c2, c3 = (self.table[i] for i in chosen)
        self.selected.clear()
        claimant = self.players[player] if player is not None else None

        if not is_set(c1, c2, c3):
            self.wrong_attempts += 1
            self.score -= WRONG_PENALTY
            if claimant:
                claimant.wrong_attempts += 1
                claimant.score -= WRONG_PENALTY
                claimant.locked_until = self._clock() + WRONG_LOCKOUT_SECONDS
            return SubmitResult(False, explain_not_set(c1, c2, c3), tuple(chosen), (c1, c2, c3),
                                player, penalised=True)

        self.score += SET_POINTS
        if claimant:
            claimant.score += SET_POINTS
            claimant.sets_found += 1
        self.found_sets.append((c1, c2, c3))
        self.found_by.append(player)
        if len(self.table) <= TABLE_SIZE and self.deck:
            # Refill in place so the remaining cards keep their positions.
            new_cards = deal(self.deck, 3)
            for index, card in zip(chosen, new_cards, strict=False):
                self.table[index] = card
            for index in reversed(chosen[len(new_cards):]):
                del self.table[index]
        else:
            for index in reversed(chosen):
                del self.table[index]

        self._auto_deal_if_needed()
        self._check_finished()
        return SubmitResult(True, 'SET!', tuple(chosen), (c1, c2, c3), player, penalised=True)

    def submit_cards(self, cards: list[Card], player: int | None = None) -> SubmitResult:
        """Submit a SET by its cards rather than positions. Used over the network, where the table
        may have changed since the player chose: cards already taken do not count as a wrong guess."""
        wanted = [tuple(card) for card in cards]
        if len(wanted) != 3 or len(set(wanted)) != 3:
            return SubmitResult(False, 'Select exactly 3 cards.', player=player)
        if not all(card in self.table for card in wanted):
            return SubmitResult(False, 'Too late: another player already took one of those cards.',
                                player=player)
        self.selected = {self.table.index(card) for card in wanted}  # type: ignore[arg-type]
        return self.submit_set(player)

    def can_deal(self) -> bool:
        """Dealing is only allowed when the deck has cards and no SET is on the table."""
        return self.game_active and bool(self.deck) and find_set(self.table) is None

    def deal_more(self) -> bool:
        if not self.can_deal():
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

    # ------------------------------------------------- network (LAN) state

    def public_state(self) -> dict:
        """Everything players may see, as JSON-friendly data. The deck's order stays secret."""
        now = self._clock()
        return {
            'mode': self.mode.value,
            'table': [list(card) for card in self.table],
            'cards_left': len(self.deck),
            'active': self.game_active,
            'elapsed': self.get_elapsed_time(),
            'players': [{'name': p.name, 'score': p.score, 'sets_found': p.sets_found,
                         'wrong_attempts': p.wrong_attempts, 'locked': max(0.0, p.locked_until - now)}
                        for p in self.players],
        }

    def load_public_state(self, state: dict) -> None:
        """Mirror a host's game from public_state(). Unseen deck cards become HIDDEN_CARD."""
        now = self._clock()
        self.mode = GameMode(state['mode'])
        self.table = [tuple(card) for card in state['table']]  # type: ignore[misc]
        self.deck = [HIDDEN_CARD] * state['cards_left']
        self.game_active = state['active']
        self.elapsed_time = state['elapsed']
        self.start_time = now - state['elapsed']
        self.players = [Player(p['name'], p['score'], p['sets_found'], p['wrong_attempts'],
                               now + p['locked']) for p in state['players']]
        self.selected = {i for i in self.selected if i < len(self.table)}

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
