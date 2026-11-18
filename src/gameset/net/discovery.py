"""Finding LAN games: hosts announce themselves by UDP broadcast every second."""

import json
import time

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtNetwork import QAbstractSocket, QHostAddress, QNetworkInterface, QUdpSocket

from .protocol import DISCOVERY_PORT, PROTOCOL_VERSION

ANNOUNCE_INTERVAL_MS = 1000
FORGET_AFTER_SECONDS = 4.0


def local_ipv4_addresses() -> list[str]:
    """This computer's network addresses, for players who type the host's address in."""
    addresses = []
    for interface in QNetworkInterface.allInterfaces():
        flags = interface.flags()
        if not (flags & QNetworkInterface.IsUp and flags & QNetworkInterface.IsRunning) \
                or flags & QNetworkInterface.IsLoopBack:
            continue
        for entry in interface.addressEntries():
            ip = entry.ip()
            if ip.protocol() == QAbstractSocket.IPv4Protocol and not ip.isLoopback():
                addresses.append(ip.toString())
    return addresses


def _broadcast_addresses() -> list[QHostAddress]:
    targets = [QHostAddress(QHostAddress.Broadcast)]
    for interface in QNetworkInterface.allInterfaces():
        flags = interface.flags()
        if not (flags & QNetworkInterface.IsUp and flags & QNetworkInterface.CanBroadcast):
            continue
        for entry in interface.addressEntries():
            broadcast = entry.broadcast()
            if not broadcast.isNull() and broadcast.protocol() == QAbstractSocket.IPv4Protocol:
                targets.append(broadcast)
    return targets


class HostAnnouncer(QObject):
    """Broadcasts 'a SET game is hosted here on this port' until stopped."""

    def __init__(self, host_name: str, game_port: int, parent=None):
        super().__init__(parent)
        self._payload = json.dumps({'app': 'gameset', 'version': PROTOCOL_VERSION,
                                    'name': host_name, 'port': game_port}).encode('utf-8')
        self._socket = QUdpSocket(self)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._announce)

    def start(self) -> None:
        self._announce()
        self._timer.start(ANNOUNCE_INTERVAL_MS)

    def stop(self) -> None:
        self._timer.stop()

    def _announce(self) -> None:
        for address in _broadcast_addresses():
            self._socket.writeDatagram(self._payload, address, DISCOVERY_PORT)


class HostFinder(QObject):
    """Listens for announcements. `hosts` maps (address, port) to the host's name."""

    hosts_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._seen: dict[tuple[str, int], tuple[str, float]] = {}
        self._socket = QUdpSocket(self)
        self._socket.readyRead.connect(self._read)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._forget_old)

    def start(self) -> bool:
        """Start listening. Returns False if the discovery port could not be opened."""
        ok = self._socket.bind(QHostAddress(QHostAddress.AnyIPv4), DISCOVERY_PORT,
                               QUdpSocket.ShareAddress | QUdpSocket.ReuseAddressHint)
        self._timer.start(ANNOUNCE_INTERVAL_MS)
        return ok

    def stop(self) -> None:
        self._timer.stop()
        self._socket.close()

    @property
    def hosts(self) -> dict[tuple[str, int], str]:
        return {key: name for key, (name, _) in self._seen.items()}

    def _read(self) -> None:
        changed = False
        while self._socket.hasPendingDatagrams():
            datagram = self._socket.receiveDatagram()
            if datagram.senderAddress().isLoopback():
                continue  # a game on this computer also arrives from its network address
            try:
                info = json.loads(datagram.data().data().decode('utf-8'))
                if info.get('app') != 'gameset' or info.get('version') != PROTOCOL_VERSION:
                    continue
                key = (datagram.senderAddress().toString().removeprefix('::ffff:'), int(info['port']))
                name = str(info['name'])
            except (ValueError, KeyError, TypeError, AttributeError):
                continue
            changed |= key not in self._seen or self._seen[key][0] != name
            self._seen[key] = (name, time.monotonic())
        if changed:
            self.hosts_changed.emit()

    def _forget_old(self) -> None:
        cutoff = time.monotonic() - FORGET_AFTER_SECONDS
        old = [key for key, (_, seen) in self._seen.items() if seen < cutoff]
        for key in old:
            del self._seen[key]
        if old:
            self.hosts_changed.emit()
