"""The LAN host: runs the one real game and tells every player what happens."""

import time
from collections.abc import Callable

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtNetwork import QHostAddress, QTcpServer, QTcpSocket

from ..game import Game, GameMode
from .discovery import HostAnnouncer
from .protocol import (
    GAME_PORT,
    MAX_LAN_PLAYERS,
    PROTOCOL_VERSION,
    LineReader,
    ProtocolError,
    clean_name,
    encode,
)


class _Connection:
    def __init__(self, socket: QTcpSocket):
        self.socket = socket
        self.reader = LineReader()
        self.player: int | None = None  # set once the hello is accepted


class LanHost(QObject):
    """Accepts players, applies their claims to the game in arrival order and broadcasts the results.

    The host's own window joins as an ordinary player through a LanClient, so it has no head start.
    """

    players_changed = Signal()

    def __init__(self, host_name: str, address: QHostAddress | None = None, port: int = GAME_PORT,
                 announce: bool = True, clock: Callable[[], float] = time.monotonic, parent=None):
        super().__init__(parent)
        self.host_name = clean_name(host_name, 'Host')
        self.game = Game(clock)
        self.game.autodeal = True  # nobody has to agree on when to deal
        self.game.hint_enabled = False
        self.started = False
        self.round = 0  # increases with every new game, so players notice a restart
        self._address = address or QHostAddress(QHostAddress.AnyIPv4)
        self._wanted_port = port
        self._announce = announce
        self._announcer: HostAnnouncer | None = None
        self._connections: list[_Connection] = []
        self._server = QTcpServer(self)
        self._server.newConnection.connect(self._accept)
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._check_time)

    @property
    def port(self) -> int:
        return self._server.serverPort()

    def start(self) -> bool:
        """Start listening (on another free port if the usual one is taken). False on failure."""
        listening = (self._server.listen(self._address, self._wanted_port)
                     or self._server.listen(self._address, 0))
        if not listening:
            return False
        if self._announce:
            self._announcer = HostAnnouncer(self.host_name, self.port, self)
            self._announcer.start()
        self._clock_timer.start(250)
        return True

    def stop(self) -> None:
        if self._announcer:
            self._announcer.stop()
        self._clock_timer.stop()
        for connection in list(self._connections):
            connection.socket.abort()
        self._connections.clear()
        self._server.close()

    def connected_players(self) -> set[int]:
        return {c.player for c in self._connections if c.player is not None}

    def start_game(self, mode: GameMode | str = GameMode.CLASSIC, seed: int | None = None) -> None:
        self.game.new_game(mode, seed)
        self.started = True
        self.round += 1
        self._broadcast_state()

    # ------------------------------------------------------------ connections

    def _accept(self) -> None:
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            connection = _Connection(socket)
            self._connections.append(connection)
            socket.readyRead.connect(lambda c=connection: self._read(c))
            socket.disconnected.connect(lambda c=connection: self._drop(c))

    def _drop(self, connection: _Connection) -> None:
        if connection in self._connections:
            self._connections.remove(connection)
            try:
                connection.socket.deleteLater()
            except RuntimeError:
                return  # Qt is shutting down and has already deleted the socket
            if connection.player is not None:
                self.players_changed.emit()
                self._broadcast_state()

    def _refuse(self, connection: _Connection, message: str) -> None:
        connection.socket.write(encode({'type': 'error', 'message': message}))
        connection.socket.flush()
        connection.socket.disconnectFromHost()

    def _read(self, connection: _Connection) -> None:
        try:
            messages = connection.reader.feed(bytes(connection.socket.readAll().data()))
        except ProtocolError as exc:
            self._refuse(connection, str(exc))
            return
        for message in messages:
            if connection.player is None:
                self._hello(connection, message)
            elif message['type'] == 'submit':
                self._submit(connection, message)

    def _hello(self, connection: _Connection, message: dict) -> None:
        if message['type'] != 'hello':
            self._refuse(connection, 'Say hello first.')
            return
        if message.get('version') != PROTOCOL_VERSION:
            self._refuse(connection, 'This game is a different version from the host. '
                                     'Both players need the same version.')
            return
        name = clean_name(message.get('name'))
        players = self.game.players
        connected = self.connected_players()
        # Someone who dropped out can rejoin under the same name and keep their score.
        player = next((i for i, p in enumerate(players) if p.name == name and i not in connected), None)
        if player is None:
            if len(players) >= MAX_LAN_PLAYERS:
                self._refuse(connection, f'The game is full ({MAX_LAN_PLAYERS} players).')
                return
            taken = {p.name for p in players}
            unique, n = name, 2
            while unique in taken:
                unique, n = f'{name} {n}', n + 1
            player = self.game.add_player(unique)
        connection.player = player
        connection.socket.write(encode({'type': 'welcome', 'player': player, 'host': self.host_name}))
        self.players_changed.emit()
        self._broadcast_state()

    def _submit(self, connection: _Connection, message: dict) -> None:
        cards = message.get('cards')
        if not self.started or not isinstance(cards, list):
            return
        try:
            cards = [tuple(int(v) for v in card) for card in cards]
        except (TypeError, ValueError):
            return
        result = self.game.submit_cards(cards, connection.player)
        reply = {'type': 'result', 'player': connection.player, 'valid': result.valid,
                 'cards': [list(c) for c in result.cards], 'positions': list(result.positions),
                 'message': result.message, 'counted': result.penalised}
        if result.penalised:
            self._broadcast(reply)
            self._broadcast_state()
        else:
            connection.socket.write(encode(reply))

    # -------------------------------------------------------------- broadcast

    def _state_message(self) -> dict:
        return {'type': 'state', **self.game.public_state(), 'started': self.started,
                'round': self.round, 'connected': sorted(self.connected_players())}

    def _broadcast_state(self) -> None:
        self._broadcast(self._state_message())

    def _broadcast(self, message: dict) -> None:
        data = encode(message)
        for connection in self._connections:
            if connection.player is not None:
                connection.socket.write(data)

    def _check_time(self) -> None:
        if self.game.check_time():
            self._broadcast_state()
