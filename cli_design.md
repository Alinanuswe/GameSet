# SET Game - CLI Version Design

## Overview

A terminal-based implementation of SET Game with text-based card representation.

## Game Rules

A SET consists of 3 cards where each of the 4 features is either:

- **All the same** across all 3 cards, OR
- **All different** across all 3 cards

### Card Features

| Feature | Options |
|---------|---------|
| Shape | Oval, Squiggle, Diamond |
| Color | Red, Green, Purple |
| Number | 1, 2, 3 |
| Shading | Solid, Striped, Empty |

---

## Card Representation

Each card is displayed in an ASCII box showing all 4 features:

```text
+-----------+
| 1: O R 1 E|
|           |
+-----------+
```

Internally, each card is stored as a tuple of four integers `(shape, color, number, shading)`, where each value is `0`, `1`, or `2` and maps to the three options for that feature.

### Symbol Mapping

| Feature | Symbol | Display |
|---------|--------|---------|
| Shape | O 0 D | Circle, Zero (Oval), Diamond |
| Color | R G P | Red, Green, Purple |
| Number | 1 2 3 | Count of symbols |
| Shading | E S F | Empty, Striped, Filled |

### Example Card

```text
+-----------+
| 2: D R 2 F|
|           |
+-----------+
```

This represents: Diamond, Red, 2, Filled

---

## Board Layout

- 12 cards displayed in 4×3 grid
- Each card in an ASCII box with card number and 4 features
- Selected cards show a `*` marker inside the box
- Cards separated by box borders

---

## User Interactions

| Input | Action |
|-------|--------|
| `1 2 3` | Select exactly 3 cards by number, space-separated |
| Enter | Submit selected SET |
| `d` | Deal 3 more cards (if deck not empty) |
| `h` | Show hint (if hints enabled) |
| `o` | Open options menu to toggle auto-deal and hints |
| `n` | New game |
| `q` | Quit |

### Options Menu

- Toggle **Auto-deal**: Automatically deals 3 more cards when no SETs are available
- Toggle **Hints**: Enable/disable the hint command

---

## Game Flow

1. Display welcome message and instructions
2. Show 12 cards on board with current score and available SETs count
3. Prompt for 3 card numbers (space-separated)
4. Validate SET when 3 cards submitted
5. If valid SET: remove cards, deal replacements, trigger auto-deal if enabled
6. If invalid SET: clear selection, prompt again
7. Display score, SETs found, and count of possible SETs on board
8. Handle end-of-game when deck empty and no SETs available

---

## Scoring

- +1 point per SET found
- Display running score
- Show total SETs found / possible

---

## Technical Notes

- Pure Python, no external dependencies
- Use standard library only
- Cross-platform compatible
