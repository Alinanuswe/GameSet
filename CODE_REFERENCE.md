# Code Reference

This document explains every line of executable source code in the project. It is intended as a handoff reference for new maintainers.

---

## `run.bat`

1. `py src/main.py`
   - Runs the Python interpreter to execute the CLI entry point at `src/main.py`.
2. `pause`
   - Pauses the command window after the script exits so the user can read any final output.

---

## `src/__init__.py`

1. `# SET Game CLI package`
   - Package marker file for the `src` directory. It contains a short comment and no executable code.

---

## `src/card.py`

1. `from typing import Tuple`
   - Imports the `Tuple` type alias from Python's `typing` module for static type annotations.

2. `Card = Tuple[int, int, int, int]`
   - Defines a `Card` type alias representing a SET card as a 4-tuple of integers.
   - Each integer is one feature dimension: shape, color, number, and shading.

3. `SHAPE_SYMBOLS = ['O', '0', 'D']`
   - Maps the internal shape values `0`, `1`, and `2` to display symbols: circle, oval, diamond.

4. `COLOR_SYMBOLS = ['R', 'G', 'P']`
   - Maps the internal color values `0`, `1`, and `2` to display letters for red, green, and purple.

5. `SHADING_SYMBOLS = ['E', 'S', 'F']`
   - Maps the internal shading values `0`, `1`, and `2` to letters for empty, striped, and filled.

6. `FEATURE_NAMES = ['Shape', 'Color', 'Number', 'Shading']`
   - Defines human-readable names for the four card features.
   - This constant is available for any UI or debugging output that needs feature labels.

7. `
   def format_card(card: Card) -> str:`
   - Declares the `format_card` function that accepts a `Card` tuple and returns a formatted string.

8. `    shape, color, number, shading = card`
   - Unpacks the four feature values from the card tuple into local variables.

9. `    shape_symbol = SHAPE_SYMBOLS[shape]`
   - Converts the numeric shape value to its display symbol.

10. `    color_symbol = COLOR_SYMBOLS[color]`
   - Converts the numeric color value to its display symbol.

11. `    shading_symbol = SHADING_SYMBOLS[shading]`
   - Converts the numeric shading value to its display symbol.

12. `    display_number = number + 1`
   - Converts the zero-based internal number into a human-friendly 1-based value.

13. `    return f"{shape_symbol} {color_symbol} {display_number} {shading_symbol}"`
   - Returns a single string representing the card, such as `O R 1 E`.

---

## `src/deck.py`

1. `import random`
   - Imports Python's standard library random module for shuffling.

2. `from card import Card`
   - Imports the `Card` type alias from `src/card.py` for type annotations.

3. `
   def create_deck() -> list[Card]:`
   - Declares `create_deck`, which returns a full list of 81 unique cards.

4. `    """Generate the 81 unique cards for the SET deck."""
   - Docstring describing the purpose of the function.

5. `    return [(shape, color, number, shading)
            for shape in range(3)
            for color in range(3)
            for number in range(3)
            for shading in range(3)]`
   - Builds the full deck using nested list comprehensions over the 3 possible values for each feature.
   - The returned deck contains every combination of shape, color, number, and shading.

6. `
   def shuffle(deck: list[Card]) -> None:`
   - Declares `shuffle`, which randomizes the card order in place.

7. `    """Shuffle the deck in place."""
   - Docstring describing the function.

8. `    random.shuffle(deck)`
   - Uses `random.shuffle` to permute the list contents.

9. `
   def deal(deck: list[Card], count: int) -> list[Card]:`
   - Declares `deal`, which removes up to `count` cards from the top of the deck.

10. `    """Deal up to `count` cards from the deck."""
   - Docstring describing the deal behavior.

11. `    dealt = []`
   - Initializes an empty list to collect the dealt cards.

12. `    for _ in range(min(count, len(deck))):`
   - Iterates the smaller of `count` and the current deck size so it never overdraws.

13. `        dealt.append(deck.pop())`
   - Removes and returns the last card from the deck, adding it to the dealt list.

14. `    return dealt`
   - Returns the cards that were dealt.

---

## `src/set_logic.py`

1. `from itertools import combinations`
   - Imports `combinations` from the standard library to generate all possible 3-card triplets.

2. `from card import Card`
   - Imports the `Card` type alias for function type annotations.

3. `
   def is_set(c1: Card, c2: Card, c3: Card) -> bool:`
   - Declares `is_set`, which checks whether three cards form a valid SET.

4. `    """Return True when three cards form a valid SET."""
   - Docstring explaining the function.

5. `    for i in range(4):`
   - Loops over the four feature positions.

6. `        if (c1[i] + c2[i] + c3[i]) % 3 != 0:`
   - Checks the SET rule: the sum of the three feature values must be divisible by 3.
   - This works because the possible values are `0`, `1`, and `2`.

7. `            return False`
   - If any feature fails the rule, the cards are not a SET.

8. `    return True`
   - If all features pass, the cards form a valid SET.

9. `
   def find_set(cards: list[Card]) -> tuple[int, int, int] | None:`
   - Declares `find_set`, which searches the board for one valid SET and returns the indices.

10. `    """Return the first valid set of indices on the board, or None."""
    - Docstring describing the lookup behavior.

11. `    for a, b, c in combinations(range(len(cards)), 3):`
    - Uses `combinations` to iterate over all unique 3-element triplets of indices.
    - Each iteration yields a tuple of three indices (a, b, c) in ascending order.

12. `        if is_set(cards[a], cards[b], cards[c]):`
    - Tests whether the selected triple forms a valid SET.

13. `            return a, b, c`
    - Returns the first valid triple of indices found.

14. `    return None`
    - Returns `None` when no valid SET exists.

---

## `src/board.py`

1. `from typing import Iterable`
   - Imports `Iterable` for type annotations used in the board update methods.

2. `from card import Card, format_card`
   - Imports the `Card` type and the `format_card` helper function to render cards.

3. `
   class Board:`
   - Defines the `Board` class for displaying and manipulating the current table of cards.

4. `    def __init__(self, cards: list[Card]) -> None:`
   - Board constructor that receives the current card list.

5. `        self.cards = cards`
   - Stores the card list on the board instance.

6. `
   def render(self, selected_indices: set[int]) -> str:`
   - Declares `render`, which returns a multiline string representation of the board.

7. `        card_width = 11`
   - Defines the fixed width of each card cell in characters.

8. `        top = '+' + '-' * card_width + '+'`
   - Builds the ASCII border for the top and bottom of a card cell.

9. `        rows = []`
   - Initializes the list of row strings that will be joined into the final board display.

10. `        for row in range(3):`
    - Iterates over three rows of the default 12-card layout.

11. `            row_cards = self.cards[row * 4:(row + 1) * 4]`
    - Selects up to four cards for the current row.

12. `            top_line = []`
    - Prepares the list of top border segments for this row.

13. `            value_line = []`
    - Prepares the list of value lines that show card labels and formatted values.

14. `            select_line = []`
    - Prepares the list of selection indicator lines.

15. `            bottom_line = []`
    - Prepares the list of bottom border segments.

16. `            for index, card in enumerate(row_cards, start=row * 4 + 1):`
    - Iterates through cards in the row, numbering them from 1 upward.

17. `                selected = index - 1 in selected_indices`
    - Computes whether the current card is selected using zero-based indices.

18. `                card_text = format_card(card)`
    - Formats the card content for display.

19. `                top_line.append(top)`
    - Appends the card border to the top row.

20. `                value_line.append(f"|{index:2d}: {card_text:<7}|")`
    - Builds the line containing the card number and formatted card text.
    - Uses alignment so each cell has fixed width.

21. `                select_label = '*' if selected else ''`
    - Sets a star when the card is selected; otherwise leaves the slot blank.

22. `                select_line.append(f"|{select_label:^11}|")`
    - Centers the selection marker inside the card cell.

23. `                bottom_line.append(top)`
    - Appends the bottom border segment for the card.

24. `            rows.append(' '.join(top_line))`
    - Joins the top border segments with spaces into a single string for the row.

25. `            rows.append(' '.join(value_line))`
    - Joins the value lines into the row string.

26. `            rows.append(' '.join(select_line))`
    - Joins the selection indicator lines into the row string.

27. `            rows.append(' '.join(bottom_line))`
    - Joins the bottom border segments into the row string.

28. `        return '\n'.join(rows)`
    - Concatenates all row strings into the final multiline board display.

29. `
   def get_card(self, index: int) -> Card:`
   - Declares `get_card`, which returns the card at a given zero-based index.

30. `        return self.cards[index]`
    - Returns the requested card.

31. `
   def replace_cards(self, indices: Iterable[int], new_cards: list[Card]) -> None:`
   - Declares `replace_cards`, which replaces specific card slots with new cards.

32. `        for dest, new_card in zip(sorted(indices), new_cards):`
    - Iterates through sorted target indices in parallel with the new cards.

33. `            self.cards[dest] = new_card`
    - Replaces the card at the destination index.

34. `
   def remove_cards(self, indices: Iterable[int]) -> None:`
   - Declares `remove_cards`, which deletes cards at the specified indices.

35. `        for index in sorted(indices, reverse=True):`
    - Iterates over indices in reverse order to avoid shifting problems during deletion.

36. `            del self.cards[index]`
    - Deletes the card at the current index.

---

## `src/game.py`

1. `from deck import create_deck, shuffle, deal`
   - Imports deck creation, shuffle, and deal utilities from `src/deck.py`.

2. `from card import Card`
   - Imports the `Card` type alias for annotations.

3. `from set_logic import is_set, find_set`
   - Imports the SET validation and search functions from `src/set_logic.py`.

4. `from board import Board`
   - Imports the `Board` class used to render the current table state.

5. `
   class Game:`
   - Defines the main game state manager.

6. `    def __init__(self) -> None:`
   - Game constructor initializes state and default settings.

7. `        self.deck: list[Card] = []`
   - Stores the remaining deck as a list of cards.

8. `        self.table: list[Card] = []`
   - Stores the cards currently on the table.

9. `        self.selected: set[int] = set()`
   - Stores zero-based indices of currently selected cards.

10. `        self.score = 0`
    - Tracks the player's score.

11. `        self.sets_found = 0`
    - Tracks the number of valid SETs found.

12. `        self.board: Board | None = None`
    - Holds the rendered board instance or `None` before a game starts.

13. `        self.autodeal = False`
    - Whether the game should automatically deal new cards when no SET is available.

14. `        self.hint_enabled = True`
    - Whether hint commands are enabled.

15. `
   def new_game(self) -> None:`
   - Starts a fresh game by initializing deck, board, and counters.

16. `        self.deck = create_deck()`
    - Builds a new full deck.

17. `        shuffle(self.deck)`
    - Randomizes the deck.

18. `        self.table = deal(self.deck, 12)`
    - Deals the first 12 cards to the table.

19. `        self.selected.clear()`
    - Clears any previous selections.

20. `        self.score = 0`
    - Resets the score.

21. `        self.sets_found = 0`
    - Resets the number of sets found.

22. `        self.board = Board(self.table)`
    - Creates a new board renderer for the current table.

23. `        self._auto_deal_if_needed()`
    - Handles auto-deal state immediately after starting the game.

24. `
   def set_options(self, autodeal: bool | None = None, hint_enabled: bool | None = None) -> None:`
    - Updates game options. `None` means leave the existing setting unchanged.

25. `        if autodeal is not None:`
    - Checks whether an auto-deal preference was provided.

26. `            self.autodeal = autodeal`
    - Sets the auto-deal option.

27. `        if hint_enabled is not None:`
    - Checks whether a hint preference was provided.

28. `            self.hint_enabled = hint_enabled`
    - Sets the hint option.

29. `        self._auto_deal_if_needed()`
    - Re-evaluates auto-deal after any option change.

30. `
   def _auto_deal_if_needed(self) -> None:`
    - Private helper that deals extra cards whenever auto-deal is enabled and no SET exists.

31. `        while self.autodeal and self.deck and self.available_set_count() == 0:`
    - Continues auto-dealing while conditions are met.
    - Conditions: auto-deal is enabled, there are cards left in the deck, and the current table has no SET.

32. `            self.table.extend(deal(self.deck, 3))`
    - Deals three more cards onto the table.

33. `            self.board = Board(self.table)`
    - Rebuilds the board renderer after changing the table.

34. `            self.selected.clear()`
    - Clears any selected cards because the board changed.

35. `
   def select_cards(self, indices: list[int]) -> None:`
    - Updates the current selection from user input.

36. `        self.selected.clear()`
    - Clears the old selection.

37. `        for index in indices:`
    - Iterates over the requested indices.

38. `            if 0 <= index < len(self.table):`
    - Validates that each index is within bounds.

39. `                self.selected.add(index)`
    - Adds the valid index to the selection set.

40. `
   def submit_set(self) -> bool:`
    - Attempts to validate the currently selected cards as a SET.
    - Returns `True` when a valid SET was submitted, otherwise `False`.

41. `        if len(self.selected) != 3:`
    - Requires exactly three selected cards.

42. `            return False`
    - Rejects invalid submission sizes.

43. `        chosen = sorted(self.selected)`
    - Sorts the selected indices to preserve order for removal and validation.

44. `        c1, c2, c3 = (self.table[i] for i in chosen)`
    - Retrieves the three selected card objects from the table.

45. `        if is_set(c1, c2, c3):`
    - Checks whether the selected cards form a valid SET.

46. `            self.sets_found += 1`
    - Increments the count of found SETs.

47. `            self.score += 1`
    - Awards a point for a valid SET.

48. `            self.table = [card for idx, card in enumerate(self.table) if idx not in chosen]`
    - Removes the chosen cards from the table by rebuilding the table list without those indices.

49. `            self.table.extend(deal(self.deck, 3))`
    - Deals three replacement cards from the deck.

50. `            self.board = Board(self.table)`
    - Recreates the board renderer after changing the table.

51. `            self.selected.clear()`
    - Clears the current selection.

52. `            self._auto_deal_if_needed()`
    - Triggers auto-deal in case the new table has no SET.

53. `            return True`
    - Returns success for the valid SET.

54. `        self.selected.clear()`
    - Clears selection after an invalid submission.

55. `        return False`
    - Returns failure when the cards were not a valid SET.

56. `
   def deal_more(self) -> None:`
    - Deals three more cards onto the table when the player requests it.

57. `        self.table.extend(deal(self.deck, 3))`
    - Adds up to three cards from the deck.

58. `        self.board = Board(self.table)`
    - Updates the board renderer.

59. `        self.selected.clear()`
    - Clears selection because table positions changed.

60. `        self._auto_deal_if_needed()`
    - Auto-deals again if enabled and there is still no SET.

61. `
   def get_hint(self) -> tuple[int, int, int] | None:`
    - Returns one valid SET found on the board, or `None` if none exists.

62. `        return find_set(self.table)`
    - Delegates to `find_set`.

63. `
   def is_game_over(self) -> bool:`
    - Determines whether the game has ended.

64. `        if self.board is None:`
    - If no game board exists, treat the game as over.

65. `            return True`
    - Returns `True` when the board is not initialized.

66. `        if self.deck:`
    - If there are cards remaining in the deck, the game is not over.

67. `            return False`
    - Returns `False` while cards remain.

68. `        return find_set(self.table) is None`
    - Otherwise, the game is over only when there are no SETs on the board.

69. `
   def get_board_display(self) -> str:`
    - Returns the board's rendered string for printing.

70. `        if self.board is None:`
    - If no board exists, returns an empty string.

71. `            return ''`
    - Returns empty display when uninitialized.

72. `        return self.board.render(self.selected)`
    - Renders the current board, marking selected cards.

73. `
   def available_set_count(self) -> int:`
    - Counts all valid SETs currently present on the table.

74. `        count = 0`
    - Initializes the counter.

75. `        table_len = len(self.table)`
    - Stores the current number of table cards.

76. `        for a in range(table_len - 2):`
    - Iterates the first card index.

77. `            for b in range(a + 1, table_len - 1):`
    - Iterates the second card index after `a`.

78. `                for c in range(b + 1, table_len):`
    - Iterates the third card index after `b`.

79. `                    if is_set(self.table[a], self.table[b], self.table[c]):`
    - Tests whether the current triple is a valid SET.

80. `                        count += 1`
    - Increments the count when a SET is found.

81. `        return count`
    - Returns the total number of valid SETs on the table.

---

## `src/main.py`

1. `from game import Game`
   - Imports the `Game` class from `src/game.py` for running the CLI game loop.

2. `
   def parse_selection(text: str) -> list[int]:`
   - Declares a parser that converts user input into zero-based card indices.

3. `    choices = []`
    - Initializes an empty list for parsed indices.

4. `    for part in text.strip().split():`
    - Splits the input text on whitespace and iterates each piece.

5. `        if part.isdigit():`
    - Only accepts pieces that are entirely digits.

6. `            value = int(part)`
    - Converts the digit string to an integer.

7. `            if 1 <= value:`
    - Validates that the entered card number is at least 1.

8. `                choices.append(value - 1)`
    - Converts the 1-based input into a zero-based index and adds it to the list.

9. `    return choices`
    - Returns the parsed list of indices.

10. `
    def show_header() -> None:`
    - Prints the CLI header and available command summary.

11. `    print('SET Game - CLI Version')`
    - Displays the game title.

12. `    print('Commands: enter 3 numbers separated by spaces to select cards | d deal 3 more | h hint | o options | n new game | q quit')`
    - Lists user commands and input format.

13. `    print('-' * 60)`
    - Prints a horizontal separator.

14. `
    def show_status(game: Game) -> None:`
    - Prints the current game state, board, and status messages.

15. `    possible_sets = game.available_set_count()`
    - Computes how many SETs are available on the current board.

16. `    print(game.get_board_display())`
    - Prints the rendered board.

17. `    print(f'Current score: {game.score} | SETs found: {game.sets_found} | Cards in deck: {len(game.deck)}')`
    - Prints score, total sets found, and deck size.

18. `    print(f'Possible SETs on board: {possible_sets}')`
    - Prints the number of possible SETs.

19. `    print(f"Auto-deal: {'ON' if game.autodeal else 'OFF'} | Hints: {'ON' if game.hint_enabled else 'OFF'}")`
    - Prints the current option states for auto-deal and hints.

20. `    if possible_sets == 0:`
    - When the board has no available SETs, prints additional guidance.

21. `        if game.deck:`
    - If the deck still has cards, suggests dealing more.

22. `            print('No SETs available right now. Press d to deal 3 more cards or o to change settings.')`
    - Displays guidance to the player.

23. `        else:`
    - If the deck is also empty, indicates the game is in a stalled state.

24. `            print('No SETs available and the deck is empty.')`
    - Informs the player that no more progress is possible.

25. `    print('-' * 60)`
    - Prints a separator after the status.

26. `
    def show_options(game: Game) -> None:`
    - Presents an interactive options menu for toggling settings.

27. `    while True:`
    - Loops until the player chooses to go back.

28. `        print('\nOptions')`
    - Prints the options menu header.

29. `        print('1: Toggle Auto-deal')`
    - Option description for auto-deal.

30. `        print('2: Toggle Hints')`
    - Option description for hints.

31. `        print('b: Back to game')`
    - Option to return to the main game.

32. `        print(f"   Auto-deal is {'ON' if game.autodeal else 'OFF'}")`
    - Displays the current auto-deal state.

33. `        print(f"   Hints are {'ON' if game.hint_enabled else 'OFF'}")`
    - Displays the current hint state.

34. `        choice = input('Select option to toggle or b to go back: ').strip().lower()`
    - Reads the user's menu choice and normalizes whitespace and case.

35. `        if choice == 'b':`
    - Handles the back command.

36. `            break`
    - Exits the options loop and returns to the game.

37. `        if choice == '1':`
    - Handles toggling auto-deal.

38. `            game.set_options(autodeal=not game.autodeal)`
    - Inverts the current auto-deal setting.

39. `            print(f"Auto-deal is now {'ON' if game.autodeal else 'OFF'}.")`
    - Confirms the new auto-deal state.

40. `            continue`
    - Returns to the start of the options loop.

41. `        if choice == '2':`
    - Handles toggling hints.

42. `            game.set_options(hint_enabled=not game.hint_enabled)`
    - Inverts the current hint setting.

43. `            print(f"Hints are now {'ON' if game.hint_enabled else 'OFF'}.")`
    - Confirms the new hint state.

44. `            continue`
    - Returns to the options loop.

45. `        print('Invalid option. Enter 1, 2, or b.')`
    - Prints an error message for unrecognized input.

46. `
    def run() -> None:`
    - Defines the main CLI game loop.

47. `    game = Game()`
    - Creates a new `Game` instance.

48. `    game.new_game()`
    - Starts a new game session.

49. `
    while True:`
    - Repeats the main input loop until the player quits.

50. `        show_header()`
    - Prints the header and command summary.

51. `        show_status(game)`
    - Prints the current board and game status.

52. `
        if game.is_game_over():`
    - Detects whether the current game has ended.

53. `            print('Game over! No more SETs available and the deck is empty.')`
    - Announces game over.

54. `            print('Press n to start a new game or q to quit.')`
    - Prints restart and quit options.

55. `
        command = input('Enter 3 numbers separated by spaces or command: ').strip().lower()`
    - Reads player input, normalizes whitespace and case.

56. `        if not command:`
    - Ignores empty input.

57. `            continue`
    - Restarts the loop.

58. `
        if command == 'q':`
    - Handles quit command.

59. `            print('Goodbye!')`
    - Prints a farewell.

60. `            break`
    - Exits the loop and ends the program.

61. `        if command == 'n':`
    - Handles new game command.

62. `            game.new_game()`
    - Resets the game state.

63. `            continue`
    - Continues the main loop.

64. `        if command == 'd':`
    - Handles the deal-more command.

65. `            if game.deck:`
    - Checks whether there are still cards to deal.

66. `                game.deal_more()`
    - Deals three more cards if possible.

67. `                print('Dealt 3 more cards.')`
    - Confirms the action to the player.

68. `            else:`
    - If the deck is empty.

69. `                print('Deck is empty. Cannot deal more cards.')`
    - Informs the player that no more cards can be dealt.

70. `            continue`
    - Returns to the main loop.

71. `        if command == 'o':`
    - Handles the options command.

72. `            show_options(game)`
    - Opens the options menu.

73. `            continue`
    - Returns to the main loop.

74. `        if command == 'h':`
    - Handles the hint command.

75. `            if not game.hint_enabled:`
    - Checks whether hints are enabled.

76. `                print('Hints are currently disabled. Enable hints from the options menu.')`
    - Informs the player that hints are disabled.

77. `                continue`
    - Skips the rest of the hint handling.

78. `            hint = game.get_hint()`
    - Requests a hint from the game state.

79. `            if hint:`
    - Checks whether a valid hint exists.

80. `                print(f'Hint: try cards {hint[0] + 1}, {hint[1] + 1}, {hint[2] + 1}')`
    - Prints the human-friendly 1-based indices of the hint cards.

81. `            else:`
    - Handles the case where no SET can be found.

82. `                print('No valid SET found on the current board.')`
    - Informs the player there is no available SET.

83. `            continue`
    - Returns to the main loop.

84. `
        chosen_indices = parse_selection(command)`
    - Parses the input as a card selection attempt.

85. `        if len(chosen_indices) != 3:`
    - Requires exactly three selections for a SET attempt.

86. `            print('Please select exactly 3 card numbers separated by spaces to attempt a SET.')`
    - Prompts the user to enter a valid selection.

87. `            continue`
    - Back to the main loop.

88. `
        game.select_cards(chosen_indices)`
    - Applies the parsed selection to the game state.

89. `        if game.submit_set():`
    - Attempts to submit the chosen cards as a SET.

90. `            print('Nice! That is a valid SET.')`
    - Informs the player the submission was successful.

91. `        else:`
    - Handles an invalid SET submission.

92. `            print('Not a valid SET. Try again.')`
    - Informs the player that the selection was incorrect.

93. `
   if __name__ == '__main__':`
    - Standard Python guard ensuring this script runs only when executed directly.

94. `    run()`
    - Calls the `run` function to start the game.
