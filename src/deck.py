import random
from card import Card


def create_deck() -> list[Card]:
    """Generate the 81 unique cards for the SET deck."""
    return [(shape, color, number, shading)
            for shape in range(3)
            for color in range(3)
            for number in range(3)
            for shading in range(3)]


def shuffle(deck: list[Card]) -> None:
    """Shuffle the deck in place."""
    random.shuffle(deck)


def deal(deck: list[Card], count: int) -> list[Card]:
    """Deal up to `count` cards from the deck."""
    dealt = []
    for _ in range(min(count, len(deck))):
        dealt.append(deck.pop())
    return dealt
