# GUI Design for SET Game

## User Story

"When I start the app, on my Mac or Linux or windows, a window opens that shows 12 cards in the center. Game info such as remaining cards in the deck, number of sets available on the board, number of sets identified are at the top center. on the top right there is a show identified sets which when clicked displays a scrollable sidebar on the left with a list of sets showing the cards in miniature portrait form form. Under the board (12 cards) there are two buttons, the deal button and the hint button. the deal button is inactive until number of possible sets is 0. The hint button has three modes specified in settings, either it makes three cards that make a set glow, or it makes 2 cards glow so the player can find the third or it makes 1 card glow so the user can find the other two. On the top right corner we have the settings button which displays some settings that can be toggled on or off such as Hints and Autodeal. in Autodeal, the deal button disappears and the app automatically deals the cards when there is 0 possible sets. When hints is off the hints button also disappears. Third button which can also be "removed" through settings is the Set button which I click once I have selected 3 cards they think is a set. If I am right, they are removed and replaced automatically, if I am wrong they glow red for a moment and don't go anywhere. If the Set button is off in settings, the moment I select 3 cards they either glow red or get removed and replaced automatically. When the game is over, a popup window with only a close button appears describing how the game has gone, in terms of time taken, number of sets discovered etc. When this window is closed it automatically starts a new game. This reminds me, there is also a timer at the bottom right and a New Game button at the top right used in case I want to start a new game even while in the middle of one."

## Architecture Overview

The application will use PySide6 (Qt for Python) to create a cross-platform GUI that can be commercially distributed without revealing source code. The architecture maintains the existing CLI functionality while adding a rich graphical interface.

### Key Design Decisions

1. **PySide6 Framework**: Chosen for commercial licensing and comprehensive Qt library access
2. **QGraphicsScene/QGraphicsView**: For smooth card rendering and interactions
3. **Pre-rendered Card Pixmaps**: All 81 cards generated as pixmaps at startup for performance
4. **Base-3 Indexing**: Card indices (0-80) map to 4-digit base-3 numbers representing card tuples
5. **QSettings Integration**: Persistent configuration storage
6. **Mode Selection**: CLI mode accessible via `--mode=cli` argument, GUI is default

## File Structure and Responsibilities

```
src/
├── main.py                    # Entry point - handles CLI/GUI mode routing
├── game.py                    # Core game logic (minimal changes - add timer support)
├── cli/
│   ├── __init__.py
│   └── runner.py              # Extracted CLI game loop and user interaction
└── gui/
    ├── __init__.py
    ├── app.py                 # Main QApplication and QMainWindow
    ├── card_renderer.py       # Card pixmap generation with base-3 indexing
    ├── widgets/
    │   ├── __init__.py
    │   ├── board_widget.py    # QGraphicsScene for 12-card display
    │   ├── card_item.py       # QGraphicsPixmapItem for individual cards
    │   ├── sidebar.py         # QScrollArea for found sets display
    │   ├── controls.py        # Deal/Hint/Set buttons and timer
    │   └── game_info.py       # Score, sets found, deck count display
    ├── dialogs/
    │   ├── __init__.py
    │   ├── settings.py        # Settings dialog with QSettings integration
    │   └── game_over.py       # Game over popup with statistics
    └── styles.py              # Qt stylesheets and visual theming
```

## Component Details

### Core Components

#### `main.py`
- Parse command line arguments (`--mode=cli` for CLI, default GUI)
- Route to appropriate runner (CLI or GUI)
- Handle application initialization and cleanup

#### `game.py` (Enhanced)
- Add timer tracking functionality
- Maintain existing game logic compatibility
- Add GUI-specific state management methods

### GUI Components

#### `gui/app.py`
- Main QApplication setup
- QMainWindow with central widget layout
- Menu bar and status bar
- Integration of all GUI components
- Game state synchronization

#### `gui/card_renderer.py`
**Critical Performance Component**
- Generate all 81 card pixmaps at application startup
- Base-3 indexing system: `index → (shape, color, number, shading)`
  - Convert index to 4-digit base-3: `index = d3*27 + d2*9 + d1*3 + d0`
  - Map to card tuple: `(shape, color, number, shading) = (d3, d2, d1, d0)`
- Cache pixmaps in list for instant access
- Handle card scaling and quality optimization

#### `gui/widgets/board_widget.py`
- QGraphicsScene containing 12 CardItem objects
- 3x4 grid layout for cards
- Handle card selection, highlighting, and animations
- Implement drag-and-drop (optional feature)
- Coordinate with game logic for set validation

#### `gui/widgets/card_item.py`
- QGraphicsPixmapItem representing individual cards
- Selection state management (normal, selected, glowing)
- Animation effects for hints and wrong sets
- Click event handling
- Visual feedback for valid/invalid sets

#### `gui/widgets/sidebar.py`
- QScrollArea with vertical layout
- Display found sets in miniature form
- Each set shows 3 small card images
- Scrollable for many found sets
- Toggle visibility via "Show Identified Sets" button

#### `gui/widgets/controls.py`
- Deal button (inactive when sets available, auto-hidden in autodeal mode)
- Hint button with three modes (3 cards, 2 cards, 1 card glow)
- Set button (optional via settings)
- Timer display (bottom right)
- New Game button (top right)

#### `gui/widgets/game_info.py`
- Score display
- Sets found counter
- Cards remaining in deck
- Available sets on board
- Auto-deal and hints status indicators

#### `gui/dialogs/settings.py`
- QSettings integration for persistence
- Toggle switches for:
  - Hints (on/off)
  - Autodeal (on/off)
  - Set button (on/off)
  - Hint mode selection (3/2/1 card)
- Apply/Cancel/OK buttons

#### `gui/dialogs/game_over.py`
- Modal dialog with game statistics
- Time taken, sets discovered, accuracy rate
- Close button that triggers new game
- Automatic new game start on close

#### `gui/styles.py`
- Qt stylesheets for consistent theming
- Card appearance and sizing
- Button styling and hover effects
- Color schemes for different game states

### CLI Components

#### `cli/runner.py`
- Extract existing CLI game loop from `main.py`
- Maintain all current CLI functionality
- Ensure compatibility with enhanced `game.py`

## Technical Implementation Details

### Card Pixmap Generation Strategy
```python
# Base-3 indexing example
def index_to_card_tuple(index: int) -> tuple:
    # Convert 0-80 to 4-digit base-3
    d3 = index // 27  # shape (0-2)
    d2 = (index % 27) // 9  # color (0-2)
    d1 = (index % 9) // 3   # number (0-2)
    d0 = index % 3          # shading (0-2)
    return (d3, d2, d1, d0)
```

### Performance Optimizations
1. **Pre-rendered Pixmaps**: All cards generated once at startup
2. **QGraphicsItem Caching**: Efficient rendering of static card images
3. **Lazy Loading**: Sidebar images generated only when needed
4. **Efficient Updates**: Only redraw changed components

### State Management
- Game state centralized in `Game` class
- GUI components observe game state changes
- Qt signals/slots for component communication
- QSettings for persistent configuration

### Cross-Platform Considerations
- PySide6 handles platform differences
- Consistent card rendering across platforms
- DPI-aware scaling for high-resolution displays
- Platform-specific file dialogs if needed

## Development Phases

1. **Phase 1**: Structure setup and CLI extraction
2. **Phase 2**: Basic GUI framework and card rendering
3. **Phase 3**: Game mechanics and user interactions
4. **Phase 4**: Advanced features (sidebar, animations, settings)
5. **Phase 5**: Polish, testing, and optimization

This architecture provides a solid foundation for implementing the complete user story while maintaining code quality, performance, and commercial viability.
