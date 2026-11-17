"""Local leaderboard of finished games, stored as JSON in the user's home directory."""

import datetime
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

MAX_ENTRIES_PER_MODE = 10


def default_scores_path() -> Path:
    override = os.environ.get('GAMESET_SCORES')
    if override:
        return Path(override)
    return Path.home() / '.gameset' / 'scores.json'


@dataclass
class ScoreEntry:
    mode: str
    score: int
    sets_found: int
    seconds: float
    date: str  # ISO date the game was played

    def sort_key(self) -> tuple:
        # Higher score first, then faster time.
        return (-self.score, self.seconds)


class Leaderboard:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_scores_path()
        self.entries: list[ScoreEntry] = self._load()

    def _load(self) -> list[ScoreEntry]:
        try:
            raw = json.loads(self.path.read_text(encoding='utf-8'))
            return [ScoreEntry(**item) for item in raw]
        except (OSError, ValueError, TypeError):
            return []

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps([asdict(e) for e in self.entries], indent=2), encoding='utf-8')
        except OSError:
            pass  # A leaderboard that can't be saved shouldn't crash the game.

    def top(self, mode: str, day: str | None = None, limit: int = MAX_ENTRIES_PER_MODE) -> list[ScoreEntry]:
        entries = [e for e in self.entries if e.mode == mode and (day is None or e.date == day)]
        return sorted(entries, key=ScoreEntry.sort_key)[:limit]

    def add(self, mode: str, score: int, sets_found: int, seconds: float,
            day: datetime.date | None = None) -> int | None:
        """Record a finished game. Returns its 1-based rank if it made the top list, else None."""
        entry = ScoreEntry(mode, score, sets_found, round(seconds, 1),
                           (day or datetime.date.today()).isoformat())
        self.entries.append(entry)
        # Keep only the best entries per mode so the file stays small.
        kept = []
        for m in {e.mode for e in self.entries}:
            kept.extend(sorted((e for e in self.entries if e.mode == m),
                               key=ScoreEntry.sort_key)[:MAX_ENTRIES_PER_MODE * 5])
        self.entries = kept
        self._save()
        ranking = self.top(mode, entry.date if mode == 'daily' else None)
        for rank, e in enumerate(ranking, start=1):
            if e is entry:
                return rank
        return None
