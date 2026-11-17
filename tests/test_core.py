from itertools import combinations

import pytest

from gameset.card import card_to_index, index_to_card, format_card, describe_card
from gameset.deck import create_deck, deal
from gameset.set_logic import is_set, find_set, find_all_sets, broken_features, explain_not_set


def test_deck_has_81_unique_cards():
    deck = create_deck()
    assert len(deck) == 81
    assert len(set(deck)) == 81


def test_card_index_round_trip():
    for index, card in enumerate(create_deck()):
        assert card_to_index(card) == index
        assert index_to_card(index) == card
    with pytest.raises(ValueError):
        index_to_card(81)


def test_deal_never_overdraws():
    deck = create_deck()
    assert len(deal(deck, 80)) == 80
    assert len(deal(deck, 3)) == 1
    assert deal(deck, 3) == []


def test_is_set_examples():
    assert is_set((0, 0, 0, 0), (1, 1, 1, 1), (2, 2, 2, 2))   # all different
    assert is_set((0, 1, 2, 0), (0, 1, 2, 1), (0, 1, 2, 2))   # all same but shading
    assert not is_set((0, 0, 0, 0), (0, 0, 0, 1), (0, 0, 0, 0))


def test_is_set_matches_rule_definition():
    def rule(*cards):
        return all(len({c[i] for c in cards}) in (1, 3) for i in range(4))

    deck = create_deck()
    for a, b, c in combinations(deck[:30], 3):
        assert is_set(a, b, c) == rule(a, b, c)


def test_every_pair_has_exactly_one_completing_card():
    deck = create_deck()
    for a, b in combinations(deck[:20], 2):
        third = [c for c in deck if c not in (a, b) and is_set(a, b, c)]
        assert len(third) == 1


def test_find_set_and_find_all_sets_agree():
    table = create_deck()[:12]
    sets = find_all_sets(table)
    assert find_set(table) == (sets[0] if sets else None)
    assert find_set(table[:2]) is None


def test_explain_not_set_names_broken_features():
    a, b, c = (0, 0, 0, 0), (0, 1, 0, 1), (0, 2, 0, 1)
    assert broken_features(a, b, c) == ['Shading']
    assert 'shading is two-and-one' in explain_not_set(a, b, c)


def test_card_text():
    assert format_card((0, 0, 0, 0)) == 'O R 1 E'
    assert describe_card((1, 2, 1, 1)) == 'two purple striped diamonds'
