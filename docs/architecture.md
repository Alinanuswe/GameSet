# Architecture

```text
src/gameset/
├── __main__.py         # python -m gameset
├── main.py             # argument parsing; starts the CLI or GUI
├── card.py             # Card = (shape, color, number, shading); index <-> card; text formats
├── deck.py             # create 81 cards, (seeded) shuffle, deal
├── set_logic.py        # is_set, find_set, find_all_sets, explain why 3 cards are not a SET
├── board.py            # ASCII rendering of the table for the CLI
├── game.py             # Game: table, selection, scoring, hints, modes, timer, end of game
├── scores.py           # Leaderboard stored as JSON
├── cli/runner.py       # terminal game loop
└── gui/
    ├── app.py          # SetGameGUI main window: wires the Game to the widgets
    ├── card_renderer.py# draws the 81 card images once (shared_renderer())
    ├── theme.py        # light and dark colour themes + stylesheet
    ├── sounds.py       # synthesised sound effects (optional Qt Multimedia)
    ├── widgets/
    │   ├── board_widget.py  # QGraphicsView that lays out and scales the cards
    │   ├── card_item.py     # one card; shows its state, reports clicks
    │   └── sidebar.py       # list of SETs found
    └── dialogs/
        ├── settings.py      # GuiSettings (persisted with QSettings) + dialog
        ├── leaderboard.py   # best scores per mode
        └── game_over.py     # end-of-game statistics
```

## Key ideas

* **Cards are tuples** of four values 0-2. `card_to_index` / `index_to_card` convert to the
  0-80 index the renderer uses. Three cards form a SET when each feature sums to a multiple of 3.
* **`Game` is the single source of truth.** The GUI never keeps its own selection: a click calls
  `Game.toggle_selection`, then the board is redrawn from `game.selected`. Temporary highlights
  (hint, wrong guess, found SET) are layered on top in `SetGameGUI._overrides`.
* **Card positions are stable.** After a SET is found on a 12-card table, the new cards are dealt
  into the same positions. Cards are laid out column by column, so dealing extra cards adds a
  column on the right without moving the others.
* `Game` takes an injectable `clock`, so timed games can be tested without waiting.

## Tests

`tests/test_core.py` covers cards and SET logic, `tests/test_game.py` the game rules,
`tests/test_scores.py` the leaderboard and `tests/test_gui.py` the main window (headless).
