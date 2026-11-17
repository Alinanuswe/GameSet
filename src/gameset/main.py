import argparse

from .game import GameMode


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(prog='gameset', description='SET Game - CLI and GUI versions')
    parser.add_argument('--mode', choices=['cli', 'gui'], default='gui',
                        help='cli for the command-line version, gui for the desktop app (default: gui)')
    parser.add_argument('--game', choices=[m.value for m in GameMode], default=GameMode.CLASSIC.value,
                        help='game mode: classic, timed (3 minutes) or daily puzzle (default: classic)')
    parser.add_argument('--seed', type=int, help='shuffle seed, to replay the same deal')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_arguments(argv)
    if args.mode == 'cli':
        from .cli.runner import run
        run(GameMode(args.game), args.seed)
    else:
        from .gui.app import run_gui
        run_gui(GameMode(args.game), args.seed)


if __name__ == '__main__':
    main()
