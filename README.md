# GameSet

A desktop and command-line version of the card game **SET**, written in Python with PySide6 (Qt).

Find three cards where each feature (shape, colour, number and shading) is either
**all the same** or **all different** on all three cards.

## Running it

Requires Python 3.10+.

```bash
pip install -r requirements.txt

# Windows
run.bat
# macOS / Linux
./run.sh
```

Or install it as a package, which adds a `gameset` command:

```bash
pip install -e .
gameset                      # desktop app
gameset --mode cli           # play in the terminal
gameset --game timed         # 3-minute challenge
gameset --game daily         # today's daily puzzle (same deal for everyone)
gameset --seed 42            # replay a specific shuffle
```

Without installing: `PYTHONPATH=src python -m gameset ...` (on Windows: `set PYTHONPATH=src` then `py -m gameset ...`).

## How to play

| Action | Mouse | Keyboard |
|---|---|---|
| Select / deselect a card | click it | the key shown in the card's corner (`1`-`0`, then `Q`-`P`, `A`) |
| Submit 3 selected cards | **Set** button | `Enter` or `Space` |
| Clear the selection | click the cards again | `Esc` |
| Hint | **Hint** | `H` |
| Deal 3 more cards | **Deal 3 Cards** | `D` |
| New game | **New Game** | `Ctrl+N` |

By default a SET is checked as soon as you pick the third card. Turn on
*Confirm SETs with the Set button* in Settings to check only when you submit.

A wrong guess tells you which features broke the rule, e.g.
*"Not a SET: colour is two-and-one"*.

### Scoring

* +10 for each SET
* −2 for each wrong guess
* −3 for each hint

### Game modes

* **Classic**: play through the whole deck. The game ends when the deck is empty and no SET is left.
* **Timed**: find as many SETs as you can in 3 minutes.
* **Daily puzzle**: everyone gets the same shuffle on a given day.

The best 10 scores in each mode are kept in `~/.gameset/scores.json` (set the
`GAMESET_SCORES` environment variable to use a different file). See them with **Best Scores**,
or `s` in the terminal version.

### Settings

Auto-deal, hints and how many cards a hint reveals, Set button vs. auto-confirm, showing
how many SETs are on the table, light/dark theme and sound effects. Settings are saved between runs.

## Development

```bash
pip install -r requirements-dev.txt
pre-commit install          # run the linter automatically on each commit

python -m pytest            # tests
ruff check src tests        # lint
mypy                        # type check
```

GitHub Actions runs the same checks on every push to `main` and on pull requests, on
Windows, macOS and Linux. Record user-visible changes in [CHANGELOG.md](CHANGELOG.md).

The GUI tests run headless (`QT_QPA_PLATFORM=offscreen` is set automatically). On a bare Linux
server Qt also needs a few system libraries, e.g. `apt-get install libegl1 libgl1 libxkbcommon0`.

See [docs/architecture.md](docs/architecture.md) for how the code is organised.
The original design notes are in [docs/design](docs/design).

## License

[MIT](LICENSE). PySide6 / Qt is used under the LGPL v3.
