# Repo: https://github.com/<your-username>/<your-repo>
import sys

from commands import execute_commands, parse_commands_section
from errors import BoardFixtureError
from game_state import GameState
from parser import parse_board_section
from stream_reader import read_lines
from validator import validate_board


def main(stream=sys.stdin):
    lines = read_lines(stream)
    grid = parse_board_section(lines)
    try:
        board = validate_board(grid)
    except BoardFixtureError as error:
        print(error.code)
        return

    game_state = GameState(board)
    commands = parse_commands_section(lines)
    execute_commands(commands, game_state, print)


if __name__ == "__main__":
    main()
