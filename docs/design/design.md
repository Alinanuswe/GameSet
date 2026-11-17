# SET Game - Desktop Application Design

## Project Overview

A desktop implementation of the popular card game SET using PySide6 (Qt for Python).

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

## Core Features

### 1. Game Board

- Display 12 cards in a 4×3 grid layout
- "Deal 3 More" button to add additional cards when needed
- **Auto-Deal Feature** (optional): Automatically deals 3 more cards when no SET is available on the board
- User choice between manual "Deal 3 More" button or automatic dealing
- Visual indication when a SET is found
- Timer display showing elapsed time

### 2. Card Display

- Custom-drawn cards using Qt graphics
- Clear visual distinction between shapes, colors, and shadings
- Hover effects on cards
- Click to select/deselect cards (highlight selected cards)

### 3. SET Detection

- Automatic detection when 3 selected cards form a SET
- Visual feedback (glow/highlight) on valid SETs
- Automatic removal of matched SET and dealing new cards if needed

### 4. SET Confirmation Modes

- **Auto-Confirm Mode**: Selecting 3 correct cards automatically confirms the SET
- **Submit Mode**: User must press Enter or click Submit button to confirm selection
  - Submit button in UI
  - Enter key submits
  - Once 3 cards are selected, cannot select another card until one is deselected
- Mode selection in settings

### 5. Found SETs List

- Side panel displaying all correctly identified SETs
- Shows the cards in each found SET (visual or text representation)
- Counter showing total SETs found
- Updates in real-time as SETs are discovered

### 6. Scoring System

- Points for finding SETs
- Bonus points for quick finds
- Penalty for incorrect SET claims (optional)
- High score tracking

### 7. Game Modes

- **Classic Mode**: Find as many SETs as possible from 12 cards
- **Timed Mode**: Find maximum SETs in fixed time
- **Practice Mode**: No time pressure, hints available

### 8. User Interface

- Clean, modern card design
- Score display
- SET counter (how many SETs are on the board)
- New Game button
- Hint button (highlights one available SET)

### 9. SET Counter (Optional Display)

- Shows the number of possible SETs currently on the board
- Toggle on/off in settings
- Updates automatically when cards are dealt or removed
- Helps players verify their observations

### 10. Game State Management

- Track remaining cards in deck
- Handle end-of-game scenarios
- Detect when no SETs are available and auto-deal

---

## Technical Features

### 11. Keyboard Shortcuts

- Number keys 1-3 to select cards
- Enter to submit SET
- Escape to deselect all
- N for new game
- H for hint

### 12. Sound Effects (Optional)

- Card selection sound
- SET found celebration
- Incorrect selection feedback

### 13. Settings

- Sound on/off toggle
- Hint availability toggle
- Card back design options
- Card fron background options
- Auto-deal toggle (automatically deal 3 cards when no SET is available)
- SET counter display toggle
- SET confirmation mode (auto-confirm vs. submit mode)

---

## Future Enhancements

- Multiplayer support (local pass-and-play)
- Online leaderboards
- Statistics tracking (games played, average time, etc.)
- Tutorial mode for new players
