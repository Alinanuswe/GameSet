from typing import Tuple

Card = Tuple[int, int, int, int]

SHAPE_SYMBOLS = ['O', '0', 'D']
COLOR_SYMBOLS = ['R', 'G', 'P']
SHADING_SYMBOLS = ['E', 'S', 'F']

FEATURE_NAMES = ['Shape', 'Color', 'Number', 'Shading']


def format_card(card: Card) -> str:
    shape, color, number, shading = card
    shape_symbol = SHAPE_SYMBOLS[shape]
    color_symbol = COLOR_SYMBOLS[color]
    shading_symbol = SHADING_SYMBOLS[shading]
    display_number = number + 1
    return f"{shape_symbol} {color_symbol} {display_number} {shading_symbol}"
