# SET Game - CLI Code Organization

## Module Structure

```text
GameSet/
├── cli_design.md
├── design.md
├── modules.md
└── src/
    ├── __init__.py
    ├── card.py          # Card class & features
    ├── deck.py          # Deck creation, shuffle, deal
    ├── set_logic.py     # SET detection algorithm
    ├── board.py         # Board display & card selection
    ├── game.py          # Game state, scoring, flow
    └── main.py          # Entry point
```

---

## Module Responsibilities

| Module | Purpose |
|--------|---------|
| `card.py` | `Card` class with shape, color, number, shading |
| `deck.py` | Generate 81 unique cards, shuffle, deal |
| `set_logic.py` | `is_set(card1, card2, card3) → bool` |
| `board.py` | Render cards, handle selection display |
| `game.py` | Game loop, score, hints, end detection |
| `main.py` | CLI entry point, input parsing |

---

## Key Classes and Functions

### card.py

```python
# Card represented as tuple of 4 integers (0, 1, 2)
# (shape, color, number, shading)
# Example: (0, 1, 2, 0) = Oval, Green, 3, Empty

Card = tuple[int, int, int, int]  # shape, color, number, shading

# Display mapping for rendering
SHAPE_SYMBOLS = ['●', '○', '◆']   # Circle, Oval, Diamond
COLOR_SYMBOLS = ['R', 'G', 'P']   # Red, Green, Purple
SHADING_SYMBOLS = ['░', '▒', '█'] # Empty, Striped, Solid
```

### set_logic.py

```python
from itertools import combinations

def is_set(c1: Card, c2: Card, c3: Card) -> bool:
    """
    Returns True if the 3 cards form a valid SET.

    A SET is valid when for each of the 4 features,
    the sum of the three values mod 3 equals 0.
    This works because:
    - All same: (0+0+0) % 3 = 0, (1+1+1) % 3 = 0, (2+2+2) % 3 = 0
    - All different: (0+1+2) % 3 = 0
    """
    for i in range(4):
        if (c1[i] + c2[i] + c3[i]) % 3 != 0:
            return False
    return True


def find_set(cards: list[Card]) -> tuple[int, int, int] | None:
    """Return the first valid set of indices on the board, or None."""
    for a, b, c in combinations(range(len(cards)), 3):
        if is_set(cards[a], cards[b], cards[c]):
            return a, b, c
    return None
```

### deck.py

```python
def create_deck() -> list[Card]:
    """Generate all 81 unique cards."""


def shuffle(deck: list[Card]) -> None:
    """Randomize deck in place."""
```

### game.py

```python
class Game:
    def new_game() -> None: ...
    def select_cards(nums: list[int]) -> None: ...
    def submit_set() -> bool: ...
    def deal_more() -> None: ...
    def get_hint() -> tuple[int, int, int]: ...
    def export_table_csv(filename: str) -> None: ...
    def is_game_over() -> bool: ...
```

---

## Data Flow

```text
main.py (entry point)
    ↓
game.py (game loop)
    ├── deck.py (create/shuffle)
    ├── card.py (Card objects)
    ├── set_logic.py (validate SETs)
    └── board.py (render output)
```

---

## Design Principles

- **Pure Python**: No external dependencies
- **Single responsibility**: Each module does one thing
- **Testable**: Logic separated from display
- **Simple**: Straightforward implementation first
