"""A player's connection to a LAN host."""

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtNetwork import QAbstractSocket, QTcpSocket

from ..card import Card
from .protocol import PROTOCOL_VERSION, LineReader, ProtocolError, encode

CONNECT_TIMEOUT_MS = 5000


class LanClient(QObject):
    welcomed = Signal(int, str)  # my player number, host name
    state_received = Signal(dict)
    result_received = Signal(dict)
    failed = Signal(str)  # could not connect, was refused, or lost the connection

    def __init__(self, parent=None):
        super().__init__(parent)
        self.player: int | None = None
        self._name = ''
        self._reader = LineReader()
        self._closing = False
        self._failed = False
        self._socket = QTcpSocket(self)
        self._socket.connected.connect(self._say_hello)
        self._socket.readyRead.connect(self._read)
        self._socket.errorOccurred.connect(self._socket_error)
        self._socket.disconnected.connect(self._disconnected)

    def connect_to(self, address: str, port: int, name: str) -> None:
        self._name = name
        self._socket.connectToHost(address, port)
        QTimer.singleShot(CONNECT_TIMEOUT_MS, self, self._check_connected)

    def _check_connected(self) -> None:
        if self.player is None:
            self._fail('Could not reach the host. Check the address, and that both computers '
                       'are on the same network.')

    def submit(self, cards: list[Card]) -> None:
        self._send({'type': 'submit', 'cards': [list(card) for card in cards]})

    def close(self) -> None:
        self._closing = True
        self._socket.abort()

    def _send(self, message: dict) -> None:
        if self._socket.state() == QAbstractSocket.ConnectedState:
            self._socket.write(encode(message))

    def _say_hello(self) -> None:
        self._send({'type': 'hello', 'name': self._name, 'version': PROTOCOL_VERSION})

    def _fail(self, message: str) -> None:
        if not self._failed and not self._closing:
            self._failed = True
            self.failed.emit(message)
        self._socket.abort()

    def _read(self) -> None:
        try:
            messages = self._reader.feed(bytes(self._socket.readAll().data()))
        except ProtocolError as exc:
            self._fail(f'The host sent something unexpected: {exc}')
            return
        for message in messages:
            kind = message['type']
            if kind == 'welcome':
                self.player = int(message['player'])
                self.welcomed.emit(self.player, str(message.get('host', '')))
            elif kind == 'state':
                self.state_received.emit(message)
            elif kind == 'result':
                self.result_received.emit(message)
            elif kind == 'error':
                self._fail(str(message.get('message', 'The host refused the connection.')))

    def _socket_error(self, _error) -> None:
        if self.player is None:
            self._fail(f'Could not connect: {self._socket.errorString()}')
        else:
            self._fail('Lost the connection to the host.')

    def _disconnected(self) -> None:
        self._fail('The host ended the game.' if self.player is not None
                   else 'The host closed the connection.')
