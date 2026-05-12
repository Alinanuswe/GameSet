import argparse
import sys
from cli.runner import run as run_cli
from game import Game


def parse_arguments():
    parser = argparse.ArgumentParser(description='SET Game - CLI and GUI versions')
    parser.add_argument('--mode', choices=['cli', 'gui'], default='gui',
                       help='Choose game mode: cli for command-line interface, gui for graphical interface (default: gui)')
    return parser.parse_args()


def run_gui():
    from gui.app import run_gui as launch_gui
    launch_gui()


def main():
    args = parse_arguments()
    
    if args.mode == 'cli':
        run_cli()
    else:
        run_gui()


if __name__ == '__main__':
    main()
