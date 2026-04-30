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

Each card displayed as a compact text block showing all 4 features:

```text
[Shape] [Color] [Number] [Shading]
```

### Symbol Mapping

| Feature | Symbol | Display |
|---------|--------|---------|
| Shape | ● ○ ◆ | Circle, Oval, Diamond |
| Color | R G P | Red, Green, Purple |
| Number | 1 2 3 | Count of symbols |
| Shading | ░ ▒ █ | Empty, Striped, Solid |

### Example Card

```text
◆ R 2 █
```

This represents: Diamond, Red, 2, Solid

---

## Board Layout

- 12 cards displayed in 4×3 grid
- Each card numbered (1-12) for selection
- Clear visual separation between cards

---

## User Interactions

| Input | Action |
|-------|--------|
| `1-12` | Select cards by number (space-separated, e.g., `1 5 9`) |
| Enter | Submit selected SET |
| `d` | Deal 3 more cards |
| `n` | New game |
| `h` | Show hint (highlight one available SET) |
| `q` | Quit |

---

## Game Flow

1. Display welcome message and instructions
2. Show 12 cards on board
3. Prompt for card selection
4. Validate SET when 3 cards selected
5. Remove matched SET, deal new cards if needed
6. Display score and SETs found
7. Handle end-of-game when deck empty

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
