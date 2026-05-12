from typing import Iterable
from card import Card, format_card


class Board:
    def __init__(self, cards: list[Card]) -> None:
        self.cards = cards

    def render(self, selected_indices: set[int]) -> str:
        if not self.cards:
            return "No cards on the table."
            
        card_width = 11
        top = '+' + '-' * card_width + '+'
        rows = []
        
        # Calculate rows dynamically - 4 cards per row, but handle partial last row
        cards_per_row = 4
        total_rows = (len(self.cards) + cards_per_row - 1) // cards_per_row
        
        for row in range(total_rows):
            start_idx = row * cards_per_row
            end_idx = min(start_idx + cards_per_row, len(self.cards))
            row_cards = self.cards[start_idx:end_idx]
            
            if not row_cards:
                break
                
            top_line = []
            value_line = []
            select_line = []
            bottom_line = []
            
            for index, card in enumerate(row_cards, start=start_idx + 1):
                selected = index - 1 in selected_indices
                card_text = format_card(card)
                top_line.append(top)
                value_line.append(f"|{index:2d}: {card_text:<7}|")
                select_label = '*' if selected else ''
                select_line.append(f"|{select_label:^11}|")
                bottom_line.append(top)
            
            rows.append(' '.join(top_line))
            rows.append(' '.join(value_line))
            rows.append(' '.join(select_line))
            rows.append(' '.join(bottom_line))
            
        return '\n'.join(rows)

    def get_card(self, index: int) -> Card:
        return self.cards[index]

    def replace_cards(self, indices: Iterable[int], new_cards: list[Card]) -> None:
        for dest, new_card in zip(sorted(indices), new_cards):
            self.cards[dest] = new_card

    def remove_cards(self, indices: Iterable[int]) -> None:
        for index in sorted(indices, reverse=True):
            del self.cards[index]
