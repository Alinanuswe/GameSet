from itertools import combinations

from card import Card


def is_set(c1: Card, c2: Card, c3: Card) -> bool:
    """Return True when three cards form a valid SET."""
    for i in range(4):
        if (c1[i] + c2[i] + c3[i]) % 3 != 0:
            return False
    return True


def find_set(cards: list[Card]) -> tuple[int, int, int] | None:
    """Return the first valid set of indices on the board, or None."""
    for a, b, c in combinations(range(len(cards)), 3):
        if is_set(cards[a], cards[b], cards[c]):
            return a, b, c
    return None


def find_all_sets(cards: list[Card]) -> list[tuple[int, int, int]]:
    """Return all valid sets of indices on the board."""
    return [
        (a, b, c)
        for a, b, c in combinations(range(len(cards)), 3)
        if is_set(cards[a], cards[b], cards[c])
    ]
