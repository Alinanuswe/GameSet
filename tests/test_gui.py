"""GUI behaviour tests. Run headless with QT_QPA_PLATFORM=offscreen (set below)."""

import os
import time

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
QtWidgets = pytest.importorskip('PySide6.QtWidgets', exc_type=ImportError)

from PySide6.QtCore import QSettings, Qt
from PySide6.QtNetwork import QHostAddress
from PySide6.QtTest import QTest

from gameset.game import SET_POINTS, WRONG_PENALTY, GameMode
from gameset.gui import app as app_module
from gameset.gui.dialogs import game_over
from gameset.gui.dialogs import settings as settings_module
from gameset.gui.dialogs.settings import GuiSettings
from gameset.gui.widgets.board_widget import CARD_KEYS
from gameset.set_logic import find_set, is_set


@pytest.fixture(scope='session')
def qapp():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def make_window(qapp, tmp_path, monkeypatch):
    """Opens game windows (several for LAN tests) and closes them afterwards."""
    monkeypatch.setenv('GAMESET_SCORES', str(tmp_path / 'scores.json'))
    # On Windows QSettings defaults to the registry, which setPath cannot redirect,
    # so point the settings store at a file in tmp_path instead.
    ini = str(tmp_path / 'settings.ini')
    monkeypatch.setattr(settings_module, 'open_settings_store', lambda: QSettings(ini, QSettings.IniFormat))
    shown = []
    monkeypatch.setattr(game_over.GameOverDialog, 'exec', lambda self: shown.append(self) or game_over.CLOSE)
    windows = []

    def make():
        w = app_module.SetGameGUI(GameMode.CLASSIC, seed=5)
        w.game_over_dialogs = shown
        w.sounds.enabled = False
        w.show()
        windows.append(w)
        return w

    yield make
    for w in windows:
        w.timer.stop()
        w.close()


@pytest.fixture
def window(make_window):
    return make_window()


def wait(ms):
    QTest.qWait(ms)


def non_set(table):
    n = len(table)
    for a in range(n):
        for b in range(a + 1, n):
            for c in range(b + 1, n):
                if not is_set(table[a], table[b], table[c]):
                    return [a, b, c]


def board_states(w):
    return [item.state for item in w.board_widget.card_items]


def test_starts_with_twelve_cards(window):
    assert len(window.board_widget.card_items) == 12
    assert window.score_label.text() == 'Score: 0'


def test_wrong_guess_does_not_leave_selection_stuck(window):
    """Regression: the game and the board used to disagree after a wrong guess."""
    for p in non_set(window.game.table):
        window.on_card_clicked(p)
    assert window.game.wrong_attempts == 1
    assert window.game.selected == set()
    wait(app_module.ERROR_FLASH_MS + 100)
    assert 'selected' not in board_states(window)
    # The player can immediately pick three new cards.
    window.on_card_clicked(0)
    window.on_card_clicked(1)
    assert window.game.selected == {0, 1}
    assert board_states(window).count('selected') == 2


def test_finding_a_set_updates_board_and_sidebar(window):
    while find_set(window.game.table) is None:
        window.deal_cards()
    for p in find_set(window.game.table):
        window.on_card_clicked(p)
    assert window._busy
    wait(app_module.SUCCESS_FLASH_MS + 100)
    assert not window._busy
    assert window.game.sets_found == 1
    assert len(window.sidebar.found_sets) == 1
    assert len(window.board_widget.card_items) == len(window.game.table)


def test_keyboard_selects_cards(window):
    window.activateWindow()
    QTest.qWaitForWindowActive(window)
    QTest.keyClick(window, CARD_KEYS[0])
    QTest.keyClick(window, CARD_KEYS[4])
    assert window.game.selected == {0, 4}
    QTest.keyClick(window, Qt.Key_Escape)
    assert window.game.selected == set()


def test_submit_mode_waits_for_enter(window):
    window.apply_settings(GuiSettings(set_button_enabled=True))
    while find_set(window.game.table) is None:
        window.deal_cards()
    for p in find_set(window.game.table):
        window.on_card_clicked(p)
    assert window.game.sets_found == 0 and window.set_button.isEnabled()
    window.on_card_clicked(next(p for p in range(12) if p not in window.game.selected))
    assert len(window.game.selected) == 3  # 4th card refused
    window.submit_set()
    wait(app_module.SUCCESS_FLASH_MS + 100)
    assert window.game.sets_found == 1


def test_hint_highlights_and_costs_points(window):
    while find_set(window.game.table) is None:
        window.deal_cards()
    window.show_hint()
    assert board_states(window).count('hint') == 3
    assert window.game.score < 0


def test_timed_game_over_records_score(window):
    window.new_game(GameMode.TIMED)
    window.game.start_time -= 10_000
    window.tick()
    assert not window.game.game_active
    assert len(window.game_over_dialogs) == 1
    assert len(window.leaderboard.top('timed')) == 1
    window.tick()
    assert len(window.game_over_dialogs) == 1  # shown once only


def test_settings_round_trip_and_dark_theme(window):
    settings = GuiSettings(theme='dark', show_available=True, hints_enabled=False, hint_mode=2)
    settings.save()
    assert GuiSettings.load() == settings
    window.apply_settings(settings)
    assert window.available_sets_label.isVisibleTo(window)
    assert not window.hint_button.isVisibleTo(window)


def test_board_scales_with_window(window):
    window.resize(800, 500)
    wait(50)
    small = window.board_widget.transform().m11()
    window.resize(1600, 1000)
    wait(50)
    assert window.board_widget.transform().m11() > small


def test_redraw_during_fade_in_stops_animations(window):
    """Regression: redrawing while new cards faded in touched deleted card items."""
    window.new_game()
    assert window.board_widget._animations
    window.refresh_board()
    assert not window.board_widget._animations


def test_deal_button_only_enabled_without_a_set(window):
    while find_set(window.game.table) is None:
        assert window.deal_button.isEnabled()
        window.deal_cards()
    size = len(window.game.table)
    assert not window.deal_button.isEnabled()
    window.deal_cards()
    assert len(window.game.table) == size


def test_available_set_count_shown_by_default_and_can_be_hidden(window):
    window.apply_settings(GuiSettings())
    assert window.available_sets_label.isVisibleTo(window)
    expected = window.game.available_set_count()
    assert window.available_sets_label.text() == f'SETs on table: {expected}'
    window.apply_settings(GuiSettings(show_available=False))
    assert not window.available_sets_label.isVisibleTo(window)


def wait_until(condition, timeout=3.0):
    end = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > end:
            raise AssertionError('timed out waiting')
        wait(10)


def test_local_multiplayer_claim_by_name(window):
    window.start_local_multiplayer(['Ann', 'Ben'])
    assert window.player_bar.isVisibleTo(window) and not window.hint_button.isVisibleTo(window)
    while find_set(window.game.table) is None:
        window.deal_cards()
    for p in find_set(window.game.table):
        window.on_card_clicked(p)
    assert window.game.sets_found == 0  # nobody has claimed it yet
    assert all(b.isEnabled() for b in window.player_bar.buttons)
    window.player_bar.buttons[1].click()
    wait(app_module.SUCCESS_FLASH_MS + 100)
    assert [p.score for p in window.game.players] == [0, SET_POINTS]
    assert window.sidebar.found_sets


def test_local_multiplayer_wrong_claim_locks_player(window):
    window.start_local_multiplayer(['Ann', 'Ben'])
    for p in non_set(window.game.table):
        window.on_card_clicked(p)
    window.claim(0)
    assert window.game.players[0].score == -WRONG_PENALTY
    for p in non_set(window.game.table):
        window.on_card_clicked(p)
    window.refresh_states()
    ann, ben = window.player_bar.buttons
    assert not ann.isEnabled() and ben.isEnabled()
    assert 'wait' in ann.text()


def test_back_to_single_player(window):
    window.start_local_multiplayer(['Ann', 'Ben'])
    window.play_single()
    assert not window.game.is_multiplayer and not window.player_bar.isVisibleTo(window)
    assert window.hint_button.isVisibleTo(window)


def test_lan_game_between_two_windows(make_window):
    host, guest = make_window(), make_window()
    assert host.host_lan('Ann', address=QHostAddress(QHostAddress.LocalHost), announce=False)
    wait_until(lambda: host.is_lan)
    guest.join_lan('127.0.0.1', host.lan_host.port, 'Ben')
    wait_until(lambda: guest.is_lan and len(host.game.players) == 2)
    assert not guest.new_game_button.isVisibleTo(guest)  # only the host starts games

    host.new_game()
    wait_until(lambda: guest.game.table and guest.game.game_active and host.game.game_active)
    assert guest.game.table == host.game.table == host.lan_host.game.table

    for p in find_set(guest.game.table):
        guest.on_card_clicked(p)  # auto-confirm is on by default
    wait_until(lambda: host.sidebar.found_sets and guest.sidebar.found_sets)
    wait_until(lambda: [p.score for p in host.game.players] == [0, SET_POINTS])
    assert guest.game.table == host.lan_host.game.table

    host.leave_lan()  # the guest is told the game ended and goes back to playing alone
    wait_until(lambda: not guest.is_lan)
    assert not guest.game.is_multiplayer and guest.game.game_active
