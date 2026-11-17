from ..card import COLOR_SYMBOLS, SHADING_SYMBOLS, SHAPE_SYMBOLS
from ..game import HINT_PENALTY, SET_POINTS, WRONG_PENALTY, Game, GameMode
from ..scores import Leaderboard

SEPARATOR = '-' * 60


def parse_selection(text: str, table_size: int) -> tuple[list[int], str | None]:
    """Parse '1 5 9' into zero-based positions. Returns (positions, error message or None)."""
    parts = text.replace(',', ' ').split()
    if len(parts) != 3:
        return [], 'Please enter exactly 3 card numbers separated by spaces.'
    positions = []
    for part in parts:
        if not part.isdigit():
            return [], f"'{part}' is not a card number."
        value = int(part)
        if not 1 <= value <= table_size:
            return [], f'There is no card {value}. Cards are numbered 1-{table_size}.'
        positions.append(value - 1)
    if len(set(positions)) != 3:
        return [], 'Each card can only be chosen once.'
    return positions, None


def show_header(game: Game) -> None:
    print(f'SET Game - CLI Version ({game.mode.label})')
    print('Commands: 3 card numbers to select a SET | d deal 3 more | h hint | o options | '
          'x export csv | s scores | n new game | q quit')
    print(f"Cards: shape {'/'.join(SHAPE_SYMBOLS)} = oval/diamond/squiggle, "
          f"colour {'/'.join(COLOR_SYMBOLS)}, number 1-3, "
          f"shading {'/'.join(SHADING_SYMBOLS)} = empty/striped/filled")
    print(f'Scoring: +{SET_POINTS} per SET, -{WRONG_PENALTY} per wrong guess, -{HINT_PENALTY} per hint')
    print(SEPARATOR)


def show_status(game: Game) -> None:
    print(game.get_board_display())
    clock = 'Time left' if game.mode is GameMode.TIMED else 'Time'
    print(f'Score: {game.score} | SETs found: {game.sets_found} | '
          f'SETs on table: {game.available_set_count()} | Cards in deck: {len(game.deck)} | '
          f'{clock}: {game.get_formatted_time()}')
    print(f"Auto-deal: {'ON' if game.autodeal else 'OFF'} | Hints: {'ON' if game.hint_enabled else 'OFF'}")
    if game.game_active and game.deck and game.get_hint() is None and not game.autodeal:
        print('No SETs on the table. Press d to deal 3 more cards.')
    print(SEPARATOR)


def show_options(game: Game) -> None:
    while True:
        print('\nOptions')
        print(f"1: Toggle Auto-deal (now {'ON' if game.autodeal else 'OFF'})")
        print(f"2: Toggle Hints (now {'ON' if game.hint_enabled else 'OFF'})")
        print(f'3: Hint reveals {game.hint_mode} card(s) - change')
        print('b: Back to game')
        choice = input('Choice: ').strip().lower()
        if choice == 'b':
            return
        if choice == '1':
            game.set_options(autodeal=not game.autodeal)
        elif choice == '2':
            game.set_options(hint_enabled=not game.hint_enabled)
        elif choice == '3':
            game.set_hint_mode(game.hint_mode % 3 + 1)
        else:
            print('Invalid option. Enter 1, 2, 3 or b.')


def show_scores(leaderboard: Leaderboard, mode: GameMode) -> None:
    import datetime
    day = datetime.date.today().isoformat() if mode is GameMode.DAILY else None
    entries = leaderboard.top(mode.value, day)
    print(f'\nBest scores - {mode.label}' + (' (today)' if day else ''))
    if not entries:
        print('  No games recorded yet.')
    for rank, e in enumerate(entries, start=1):
        print(f'  {rank:2d}. {e.score:4d} pts  {e.sets_found:2d} SETs  '
              f'{int(e.seconds) // 60:02d}:{int(e.seconds) % 60:02d}  {e.date}')
    print()


def report_game_over(game: Game, leaderboard: Leaderboard) -> None:
    stats = game.get_game_statistics()
    print('\nGame over!')
    print(f"Time: {stats['time_elapsed']} | SETs: {stats['sets_found']} | Score: {stats['final_score']} | "
          f"Accuracy: {stats['accuracy_rate']:.0f}% | Hints: {stats['hints_used']}")
    rank = leaderboard.add(game.mode.value, game.score, game.sets_found, game.elapsed_time)
    if rank:
        print(f'New entry on the leaderboard at #{rank}!')
    print('Press n to start a new game, s for scores or q to quit.')


def run(mode: GameMode = GameMode.CLASSIC, seed: int | None = None) -> None:
    game = Game()
    leaderboard = Leaderboard()
    game.new_game(mode, seed)
    reported = False

    while True:
        game.check_time()
        if not game.game_active and not reported:
            show_status(game)
            report_game_over(game, leaderboard)
            reported = True
        elif game.game_active:
            show_header(game)
            show_status(game)

        try:
            command = input('Enter 3 card numbers or a command: ').strip().lower()
        except EOFError:
            print()
            return
        if not command:
            continue

        if command == 'q':
            print('Goodbye!')
            return
        if command == 'n':
            game.new_game(game.mode)
            reported = False
            continue
        if command == 'o':
            show_options(game)
            continue
        if command == 's':
            show_scores(leaderboard, game.mode)
            continue
        if command == 'x':
            filename = input('Enter CSV filename to write (default board.csv): ').strip() or 'board.csv'
            try:
                game.export_table_csv(filename)
                print(f'Exported current board to {filename}.')
            except OSError as exc:
                print(f'Could not write {filename}: {exc}')
            continue

        if game.check_time() or not game.game_active:
            print('The game is over. Press n for a new game.')
            continue
        if command == 'd':
            if game.deal_more():
                print('Dealt 3 more cards.')
            elif not game.deck:
                print('Deck is empty. Cannot deal more cards.')
            else:
                print('There is a SET on the table. Find it before dealing more cards.')
            continue
        if command == 'h':
            if not game.hint_enabled:
                print('Hints are disabled. Enable them from the options menu (o).')
                continue
            hint = game.get_hint_cards()
            if hint:
                print(f"Hint (-{HINT_PENALTY} points): try card(s) {', '.join(str(i + 1) for i in hint)}")
            else:
                print('No valid SET on the table.')
            continue

        positions, error = parse_selection(command, len(game.table))
        if error:
            print(error)
            continue
        game.select_cards(positions)
        result = game.submit_set()
        print('Nice! That is a valid SET.' if result.valid else result.message)
