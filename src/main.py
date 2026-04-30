from game import Game


def parse_selection(text: str) -> list[int]:
    choices = []
    for part in text.strip().split():
        if part.isdigit():
            value = int(part)
            if 1 <= value:
                choices.append(value - 1)
    return choices


def show_header() -> None:
    print('SET Game - CLI Version')
    print('Commands: enter 3 numbers separated by spaces to select cards | d deal 3 more | h hint | o options | n new game | q quit')
    print('-' * 60)


def show_status(game: Game) -> None:
    possible_sets = game.available_set_count()
    print(game.get_board_display())
    print(f'Current score: {game.score} | SETs found: {game.sets_found} | Cards in deck: {len(game.deck)}')
    print(f'Possible SETs on board: {possible_sets}')
    print(f"Auto-deal: {'ON' if game.autodeal else 'OFF'} | Hints: {'ON' if game.hint_enabled else 'OFF'}")
    if possible_sets == 0:
        if game.deck:
            print('No SETs available right now. Press d to deal 3 more cards or o to change settings.')
        else:
            print('No SETs available and the deck is empty.')
    print('-' * 60)


def show_options(game: Game) -> None:
    while True:
        print('\nOptions')
        print('1: Toggle Auto-deal')
        print('2: Toggle Hints')
        print('b: Back to game')
        print(f"   Auto-deal is {'ON' if game.autodeal else 'OFF'}")
        print(f"   Hints are {'ON' if game.hint_enabled else 'OFF'}")
        choice = input('Select option to toggle or b to go back: ').strip().lower()
        if choice == 'b':
            break
        if choice == '1':
            game.set_options(autodeal=not game.autodeal)
            print(f"Auto-deal is now {'ON' if game.autodeal else 'OFF'}.")
            continue
        if choice == '2':
            game.set_options(hint_enabled=not game.hint_enabled)
            print(f"Hints are now {'ON' if game.hint_enabled else 'OFF'}.")
            continue
        print('Invalid option. Enter 1, 2, or b.')


def run() -> None:
    game = Game()
    game.new_game()

    while True:
        show_header()
        show_status(game)

        if game.is_game_over():
            print('Game over! No more SETs available and the deck is empty.')
            print('Press n to start a new game or q to quit.')

        command = input('Enter 3 numbers separated by spaces or command: ').strip().lower()
        if not command:
            continue

        if command == 'q':
            print('Goodbye!')
            break
        if command == 'n':
            game.new_game()
            continue
        if command == 'd':
            if game.deck:
                game.deal_more()
                print('Dealt 3 more cards.')
            else:
                print('Deck is empty. Cannot deal more cards.')
            continue
        if command == 'o':
            show_options(game)
            continue
        if command == 'h':
            if not game.hint_enabled:
                print('Hints are currently disabled. Enable hints from the options menu.')
                continue
            hint = game.get_hint()
            if hint:
                print(f'Hint: try cards {hint[0] + 1}, {hint[1] + 1}, {hint[2] + 1}')
            else:
                print('No valid SET found on the current board.')
            continue

        chosen_indices = parse_selection(command)
        if len(chosen_indices) != 3:
            print('Please select exactly 3 card numbers separated by spaces to attempt a SET.')
            continue

        game.select_cards(chosen_indices)
        if game.submit_set():
            print('Nice! That is a valid SET.')
        else:
            print('Not a valid SET. Try again.')


if __name__ == '__main__':
    run()
