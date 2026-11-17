import pytest

from gameset.card import Card
from gameset.deck import create_deck
from gameset.game import (Game, GameMode, SET_POINTS, HINT_PENALTY, WRONG_PENALTY,
                          TIMED_LIMIT_SECONDS, daily_seed)
from gameset.set_logic import is_set, find_set, find_all_sets


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def make_game(**kwargs) -> Game:
    game = Game(**kwargs)
    game.new_game(seed=1)
    return game


def first_non_set(table: list[Card]) -> list[int]:
    for a in range(len(table)):
        for b in range(a + 1, len(table)):
            for c in range(b + 1, len(table)):
                if not is_set(table[a], table[b], table[c]):
                    return [a, b, c]
    raise AssertionError('no non-set found')


def test_new_game_deals_twelve():
    game = make_game()
    assert len(game.table) == 12
    assert len(game.deck) == 69
    assert game.game_active


def test_same_seed_same_shuffle():
    a, b = Game(), Game()
    a.new_game(seed=42)
    b.new_game(seed=42)
    assert a.table == b.table and a.deck == b.deck


def test_daily_mode_uses_date_seed():
    game = Game()
    game.new_game(mode=GameMode.DAILY)
    assert game.seed == daily_seed()


def test_valid_set_scores_and_refills_in_place():
    game = make_game()
    while find_set(game.table) is None:
        game.deal_more()
    before = list(game.table)
    hint = list(find_set(game.table))
    game.select_cards(hint)
    result = game.submit_set()
    assert result.valid
    assert game.score == SET_POINTS
    assert game.sets_found == 1
    assert len(game.table) == max(12, len(before) - 3)
    if len(before) == 12:
        untouched = [i for i in range(12) if i not in hint]
        assert all(game.table[i] == before[i] for i in untouched)
    assert game.found_sets[0] == tuple(before[i] for i in hint)


def test_invalid_set_counts_wrong_attempt_and_explains():
    game = make_game()
    game.select_cards(first_non_set(game.table))
    result = game.submit_set()
    assert not result.valid
    assert result.message.startswith('Not a SET')
    assert game.wrong_attempts == 1
    assert game.score == -WRONG_PENALTY
    assert game.selected == set()


def test_select_cards_rejects_bad_input():
    game = make_game()
    with pytest.raises(ValueError):
        game.select_cards([0, 1, 99])
    with pytest.raises(ValueError):
        game.select_cards([0, 0, 1])


def test_toggle_selection_limits_to_three():
    game = make_game()
    assert all(game.toggle_selection(i) for i in range(3))
    assert not game.toggle_selection(3)
    assert game.toggle_selection(0)  # deselect
    assert game.toggle_selection(3)
    assert game.selected == {1, 2, 3}


def test_hint_costs_points_and_respects_mode():
    game = make_game()
    while find_set(game.table) is None:
        game.deal_more()
    game.set_hint_mode(2)
    assert len(game.get_hint_cards()) == 2
    assert game.hints_used == 1
    assert game.score == -HINT_PENALTY
    game.set_options(hint_enabled=False)
    assert game.get_hint_cards() == []


def test_accuracy():
    game = make_game()
    assert game.accuracy() == 0.0
    game.select_cards(first_non_set(game.table))
    game.submit_set()
    while find_set(game.table) is None:
        game.deal_more()
    game.select_cards(list(find_set(game.table)))
    game.submit_set()
    assert game.accuracy() == 50.0


def test_autodeal_guarantees_a_set_while_deck_lasts():
    game = Game()
    game.set_options(autodeal=True)
    for seed in range(20):
        game.new_game(seed=seed)
        assert find_set(game.table) is not None or not game.deck


def test_full_game_ends_with_empty_deck():
    game = Game()
    game.set_options(autodeal=True)
    game.new_game(seed=7)
    while game.game_active:
        game.select_cards(list(find_set(game.table)))
        assert game.submit_set().valid
    assert not game.deck
    assert game.is_game_over()
    assert find_all_sets(game.table) == []
    assert game.sets_found * 3 + len(game.table) == 81


def test_twenty_cards_always_contain_a_set():
    # Max cap set size in SET is 20, so the GUI's 21-card limit is always enough.
    import random
    rng = random.Random(0)
    deck = create_deck()
    for _ in range(200):
        assert find_set(rng.sample(deck, 21)) is not None


def test_timed_mode_ends_when_time_runs_out():
    clock = FakeClock()
    game = Game(clock=clock)
    game.new_game(mode=GameMode.TIMED, seed=3)
    assert game.get_formatted_time() == '03:00'
    clock.now += TIMED_LIMIT_SECONDS - 1
    assert not game.check_time()
    clock.now += 5
    assert game.check_time()
    assert not game.game_active
    assert game.is_game_over()
    assert game.get_elapsed_time() == TIMED_LIMIT_SECONDS
    assert not game.submit_set().valid


def test_elapsed_time_freezes_when_game_ends():
    clock = FakeClock()
    game = Game(clock=clock)
    game.set_options(autodeal=True)
    game.new_game(seed=7)
    clock.now += 65
    while game.game_active:
        game.select_cards(list(find_set(game.table)))
        game.submit_set()
    clock.now += 100
    assert game.get_formatted_time() == '01:05'


def test_export_csv(tmp_path):
    game = make_game()
    path = tmp_path / 'board.csv'
    game.export_table_csv(str(path))
    lines = path.read_text().splitlines()
    assert lines[0].startswith('ID,Shape')
    assert len([l for l in lines[1:13] if l]) == 12
