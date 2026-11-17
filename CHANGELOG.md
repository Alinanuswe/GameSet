# Changelog

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
