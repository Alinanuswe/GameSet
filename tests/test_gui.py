"""GUI behaviour tests. Run headless with QT_QPA_PLATFORM=offscreen (set below)."""

import os

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
QtWidgets = pytest.importorskip('PySide6.QtWidgets', exc_type=ImportError)

from PySide6.QtCore import QSettings, Qt
from PySide6.QtTest import QTest

from gameset.game import GameMode
from gameset.set_logic import find_set, is_set
from gameset.gui import app as app_module
from gameset.gui.dialogs import game_over
from gameset.gui.dialogs.settings import GuiSettings
from gameset.gui.widgets.board_widget import CARD_KEYS


@pytest.fixture(scope='session')
def qapp():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def window(qapp, tmp_path, monkeypatch):
    monkeypatch.setenv('GAMESET_SCORES', str(tmp_path / 'scores.json'))
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(tmp_path))
    QSettings.setPath(QSettings.NativeFormat, QSettings.UserScope, str(tmp_path))
    shown = []
    monkeypatch.setattr(game_over.GameOverDialog, 'exec', lambda self: shown.append(self) or game_over.CLOSE)
    w = app_module.SetGameGUI(GameMode.CLASSIC, seed=5)
    w.game_over_dialogs = shown
    w.sounds.enabled = False
    w.show()
    yield w
    w.timer.stop()
    w.close()


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
    window.deal_cards()
    assert window.board_widget._animations
    window.refresh_board()
    assert not window.board_widget._animations
