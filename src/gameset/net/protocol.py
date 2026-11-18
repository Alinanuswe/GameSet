"""Messages between the LAN host and its players: one JSON object per line over TCP.

Player -> host:
    hello   {name, version}       first message; the host answers welcome or error
    submit  {cards}               claim a SET, by its three cards
Host -> player:
    welcome {player, host}        your player number, and the host's name
    state   {...}                 the table, scores and clock (Game.public_state), plus
                                  started, round (game number) and connected (player numbers)
    result  {player, valid, cards, positions, message, counted}
                                  someone's claim; counted is False when it was refused
                                  without a penalty (too late, still locked out)
    error   {message}             the host refuses this player and closes the connection
"""

import json

PROTOCOL_VERSION = 1
GAME_PORT = 45455
DISCOVERY_PORT = 45454
MAX_LAN_PLAYERS = 8
MAX_NAME_LENGTH = 20
MAX_LINE_BYTES = 64 * 1024


class ProtocolError(Exception):
    pass


def encode(message: dict) -> bytes:
    return json.dumps(message, separators=(',', ':')).encode('utf-8') + b'\n'


class LineReader:
    """Collects bytes from a socket and returns each complete message."""

    def __init__(self) -> None:
        self._buffer = b''

    def feed(self, data: bytes) -> list[dict]:
        self._buffer += data
        *lines, self._buffer = self._buffer.split(b'\n')
        if len(self._buffer) > MAX_LINE_BYTES:
            raise ProtocolError('Message too long.')
        messages = []
        for line in lines:
            if not line.strip():
                continue
            try:
                message = json.loads(line)
            except ValueError as exc:
                raise ProtocolError('Unreadable message.') from exc
            if not isinstance(message, dict) or not isinstance(message.get('type'), str):
                raise ProtocolError('Unreadable message.')
            messages.append(message)
        return messages


def clean_name(name: object, fallback: str = 'Player') -> str:
    text = ' '.join(str(name or '').split())[:MAX_NAME_LENGTH]
    return text or fallback
