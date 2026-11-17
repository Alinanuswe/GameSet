from itertools import combinations

from .card import FEATURE_NAMES, Card


def is_set(c1: Card, c2: Card, c3: Card) -> bool:
    """Return True when three cards form a valid SET."""
    return all((c1[i] + c2[i] + c3[i]) % 3 == 0 for i in range(4))


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


def broken_features(c1: Card, c2: Card, c3: Card) -> list[str]:
    """Names of the features that are neither all the same nor all different."""
    return [FEATURE_NAMES[i] for i in range(4) if (c1[i] + c2[i] + c3[i]) % 3 != 0]


def explain_not_set(c1: Card, c2: Card, c3: Card) -> str:
    """One-line explanation of why three cards are not a SET."""
    broken = broken_features(c1, c2, c3)
    if not broken:
        return "That is a SET."
    names = ', '.join(name.lower() for name in broken)
    verb = 'is' if len(broken) == 1 else 'are'
    return f"Not a SET: {names} {verb} two-and-one (must be all same or all different)."
