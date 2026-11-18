"""LAN play: a real host and players talking over the loopback network."""

import os
import time

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
QtWidgets = pytest.importorskip('PySide6.QtWidgets', exc_type=ImportError)

from PySide6.QtNetwork import QHostAddress
from PySide6.QtTest import QTest

from gameset.game import SET_POINTS, WRONG_PENALTY
from gameset.net import protocol
from gameset.net.client import LanClient
from gameset.net.host import LanHost
from gameset.net.protocol import LineReader, ProtocolError, encode
from gameset.set_logic import find_set, is_set


@pytest.fixture(scope='module')
def qapp():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def wait_until(condition, timeout=3.0):
    end = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > end:
            raise AssertionError('timed out waiting')
        QTest.qWait(10)


class Player:
    """A LanClient plus everything it has heard."""

    def __init__(self, host: LanHost, name: str):
        self.client = LanClient()
        self.states: list[dict] = []
        self.results: list[dict] = []
        self.failures: list[str] = []
        self.client.state_received.connect(self.states.append)
        self.client.result_received.connect(self.results.append)
        self.client.failed.connect(self.failures.append)
        self.client.connect_to('127.0.0.1', host.port, name)

    @property
    def state(self) -> dict:
        return self.states[-1]


@pytest.fixture
def host(qapp):
    h = LanHost('Host', address=QHostAddress(QHostAddress.LocalHost), port=0, announce=False)
    assert h.start()
    yield h
    h.stop()


def join(host, name):
    player = Player(host, name)
    wait_until(lambda: player.client.player is not None or player.failures)
    return player


def table_cards(state, positions):
    return [tuple(state['table'][p]) for p in positions]


def a_set(state):
    return table_cards(state, find_set([tuple(c) for c in state['table']]))


def not_a_set(state):
    table = [tuple(c) for c in state['table']]
    n = len(table)
    return next([table[a], table[b], table[c]] for a in range(n) for b in range(a + 1, n)
                for c in range(b + 1, n) if not is_set(table[a], table[b], table[c]))


def test_line_reader_handles_split_and_bad_messages():
    reader = LineReader()
    data = encode({'type': 'a'}) + encode({'type': 'b'})
    assert reader.feed(data[:5]) == []
    assert [m['type'] for m in reader.feed(data[5:])] == ['a', 'b']
    with pytest.raises(ProtocolError):
        LineReader().feed(b'not json\n')


def test_players_join_and_see_the_same_table(host):
    alice, bob = join(host, 'Alice'), join(host, 'Bob')
    assert (alice.client.player, bob.client.player) == (0, 1)
    host.start_game(seed=3)
    wait_until(lambda: alice.states and bob.states and alice.state['started'] and bob.state['started'])
    assert alice.state['table'] == bob.state['table'] and len(alice.state['table']) >= 12
    assert [p['name'] for p in alice.state['players']] == ['Alice', 'Bob']
    assert 'deck' not in alice.state  # the deck's order stays on the host


def test_first_claim_wins_and_second_is_too_late(host):
    alice, bob = join(host, 'Alice'), join(host, 'Bob')
    host.start_game(seed=3)
    wait_until(lambda: alice.states and alice.state['started'] and bob.states and bob.state['started'])
    cards = a_set(alice.state)
    alice.client.submit(cards)
    bob.client.submit(cards)
    # Whichever claim reaches the host first scores; the other is told it was too late.
    wait_until(lambda: any(not r['counted'] for r in alice.results + bob.results))
    late = [r for r in alice.results + bob.results if not r['counted']]
    assert len(late) == 1 and 'Too late' in late[0]['message']
    assert sorted(p.score for p in host.game.players) == [0, SET_POINTS]
    winner = 1 - late[0]['player']
    wait_until(lambda: any(r['valid'] and r['player'] == winner for r in alice.results))


def test_wrong_guess_costs_points_and_locks_out(host):
    alice = join(host, 'Alice')
    host.start_game(seed=3)
    wait_until(lambda: alice.states and alice.state['started'])
    alice.client.submit(not_a_set(alice.state))
    wait_until(lambda: alice.results)
    assert alice.results[-1]['counted'] and not alice.results[-1]['valid']
    assert host.game.players[0].score == -WRONG_PENALTY
    alice.client.submit(a_set(alice.state))
    wait_until(lambda: len(alice.results) == 2)
    assert not alice.results[-1]['counted'] and 'wait' in alice.results[-1]['message']


def test_dropped_player_rejoins_with_their_score(host):
    alice = join(host, 'Alice')
    host.start_game(seed=3)
    wait_until(lambda: alice.states and alice.state['started'])
    alice.client.submit(a_set(alice.state))
    wait_until(lambda: alice.results)
    alice.client.close()
    wait_until(lambda: not host.connected_players())
    again = join(host, 'Alice')
    assert again.client.player == 0
    wait_until(lambda: again.states)
    assert again.state['players'][0]['score'] == SET_POINTS


def test_same_name_while_connected_gets_a_number(host):
    first = join(host, 'Sam')  # noqa: F841 - must stay connected
    second = join(host, 'Sam')
    wait_until(lambda: second.states)
    assert [p['name'] for p in second.state['players']] == ['Sam', 'Sam 2']


def test_wrong_version_is_refused(host, monkeypatch):
    monkeypatch.setattr('gameset.net.client.PROTOCOL_VERSION', protocol.PROTOCOL_VERSION + 1)
    player = join(host, 'Old')
    wait_until(lambda: player.failures)
    assert 'version' in player.failures[0]


def test_players_hear_when_the_host_stops(host):
    alice = join(host, 'Alice')
    host.stop()
    wait_until(lambda: alice.failures)
