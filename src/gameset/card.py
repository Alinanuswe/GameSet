
Card = tuple[int, int, int, int]

FEATURE_NAMES = ['Shape', 'Color', 'Number', 'Shading']

# Human-readable names for each feature value, indexed by feature then value.
FEATURE_VALUES = [
    ['oval', 'diamond', 'squiggle'],
    ['red', 'green', 'purple'],
    ['one', 'two', 'three'],
    ['empty', 'striped', 'filled'],
]

SHAPE_SYMBOLS = ['O', 'D', 'S']
COLOR_SYMBOLS = ['R', 'G', 'P']
SHADING_SYMBOLS = ['E', 'S', 'F']

DECK_SIZE = 81


def card_to_index(card: Card) -> int:
    """Map a card to its base-3 index (0-80): shape, color, number, shading."""
    shape, color, number, shading = card
    return shape * 27 + color * 9 + number * 3 + shading


def index_to_card(index: int) -> Card:
    """Inverse of card_to_index."""
    if not 0 <= index < DECK_SIZE:
        raise ValueError(f"Card index {index} out of range (0-80)")
    return (index // 27, (index // 9) % 3, (index // 3) % 3, index % 3)


def format_card(card: Card) -> str:
    shape, color, number, shading = card
    return f"{SHAPE_SYMBOLS[shape]} {COLOR_SYMBOLS[color]} {number + 1} {SHADING_SYMBOLS[shading]}"


def describe_card(card: Card) -> str:
    """Long form, e.g. 'two red striped ovals'."""
    shape, color, number, shading = card
    noun = FEATURE_VALUES[0][shape] + ('s' if number else '')
    return f"{FEATURE_VALUES[2][number]} {FEATURE_VALUES[1][color]} {FEATURE_VALUES[3][shading]} {noun}"
