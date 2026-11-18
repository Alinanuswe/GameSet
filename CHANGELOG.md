# Changelog

## Unreleased

### Added
- Local multiplayer for 2-4 players on one screen or touchscreen: pick 3 cards, then click your
  name (or press `F1`-`F4`) to claim the SET.
- LAN multiplayer: host a game, or join one found automatically on the network (or by address).
  The first claim to reach the host wins; players who drop out can rejoin with their score.
- In multiplayer, a wrong claim costs 2 points and a 3-second wait before claiming again.

### Changed
- Cards use the standard shapes: oval (pill), diamond and squiggle. The rounded-rectangle "bar" is replaced by the squiggle, and its terminal symbol changes from `B` to `S`.
- Dealing 3 more cards is only allowed when there is no SET on the table (GUI and terminal).

### Fixed
- On Windows, sound effects only played the first time (for example, no SET sound after the first SET). Windows now plays them with `winsound`.
- GUI tests saved their settings to the real Windows registry, turning hints off in the game and making the hint test fail.

## 0.2.0 - 2026-11-17

### Fixed
- Cards stayed highlighted after a wrong guess, leaving the selection stuck.
- The terminal version treated typos such as `1 2 99` or `1 1 2` as wrong guesses.
- Found SETs were recorded as board positions, so the record became wrong after new cards were dealt.
- Accuracy was always reported as 100%.

### Added
- Classic, timed (3 minutes) and daily-puzzle game modes, plus a `--seed` option.
- Local leaderboard and a game-over screen with statistics.
- Scoring: +10 per SET, -2 per wrong guess, -3 per hint.
- Explanations for wrong guesses ("colour is two-and-one").
- Keyboard controls, a board that scales with the window, and animations for found SETs and new cards.
- Working dark theme and sound effects.
- Tests, CI, linting and type checking.

### Changed
- Code moved into the `gameset` package (`src/gameset`); run with `python -m gameset` or `gameset`.
- The count of SETs on the table is optional and hidden by default.
- The Deal button is available whenever the deck has cards.
- Terminal shape symbols are now `O`/`D`/`B` (oval, diamond, bar).

## 0.1.0

- First version: CLI and PySide6 GUI.
