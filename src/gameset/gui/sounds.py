"""Short synthesised sound effects. Falls back to silence if Qt Multimedia is unavailable."""

import math
import struct
import sys
import tempfile
import wave
from pathlib import Path

from PySide6.QtCore import QUrl

try:
    from PySide6.QtMultimedia import QSoundEffect
except ImportError:  # Qt Multimedia missing or its system libraries not installed
    QSoundEffect = None

# On Windows, QSoundEffect (FFmpeg backend) can report a sound as playing while staying
# silent after its first play. winsound uses the Windows player directly and is reliable.
if sys.platform == 'win32':
    import winsound
else:
    winsound = None

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
        self._files: dict[str, Path] = {}
        self._effects: dict[str, QSoundEffect] = {}
        if winsound is None and QSoundEffect is None:
            return
        folder = Path(tempfile.gettempdir()) / 'gameset-sounds'
        try:
            folder.mkdir(exist_ok=True)
            for name, notes in SOUNDS.items():
                path = folder / f'{name}.wav'
                if not path.exists():
                    _write_wav(path, notes)
                self._files[name] = path
        except OSError:
            self._files.clear()
            return
        if winsound is None:
            for name, path in self._files.items():
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(str(path)))
                effect.setVolume(0.5)
                self._effects[name] = effect

    def play(self, name: str) -> None:
        if not self.enabled or name not in self._files:
            return
        if winsound is not None:
            try:
                winsound.PlaySound(str(self._files[name]), winsound.SND_FILENAME | winsound.SND_ASYNC)
            except RuntimeError:
                pass  # no audio device
        elif name in self._effects:
            effect = self._effects[name]
            effect.stop()  # restart cleanly if the previous play has not been reset
            effect.play()
