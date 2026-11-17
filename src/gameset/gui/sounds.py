"""Short synthesised sound effects. Falls back to silence if Qt Multimedia is unavailable."""

import math
import struct
import tempfile
import wave
from pathlib import Path

from PySide6.QtCore import QUrl

try:
    from PySide6.QtMultimedia import QSoundEffect
except ImportError:  # Qt Multimedia missing or its system libraries not installed
    QSoundEffect = None

SAMPLE_RATE = 44100

# Each sound is a list of (frequency Hz, duration s) notes.
SOUNDS = {
    'set': [(660, 0.08), (880, 0.12)],
    'wrong': [(220, 0.18)],
    'deal': [(520, 0.05)],
    'hint': [(740, 0.07)],
    'game_over': [(523, 0.12), (659, 0.12), (784, 0.25)],
}


def _write_wav(path: Path, notes: list[tuple[int, float]]) -> None:
    frames = bytearray()
    for frequency, duration in notes:
        count = int(SAMPLE_RATE * duration)
        for i in range(count):
            fade = min(1.0, (count - i) / (SAMPLE_RATE * 0.02))  # avoid clicks at note end
            value = int(9000 * fade * math.sin(2 * math.pi * frequency * i / SAMPLE_RATE))
            frames += struct.pack('<h', value)
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(bytes(frames))


class SoundPlayer:
    def __init__(self) -> None:
        self.enabled = True
        self._effects = {}
        if QSoundEffect is None:
            return
        folder = Path(tempfile.gettempdir()) / 'gameset-sounds'
        try:
            folder.mkdir(exist_ok=True)
            for name, notes in SOUNDS.items():
                path = folder / f'{name}.wav'
                if not path.exists():
                    _write_wav(path, notes)
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(str(path)))
                effect.setVolume(0.5)
                self._effects[name] = effect
        except OSError:
            self._effects.clear()

    def play(self, name: str) -> None:
        if self.enabled and name in self._effects:
            self._effects[name].play()
