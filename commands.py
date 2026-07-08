"""Everything about the "Commands:" section: parsing lines into tokens and
dispatching them against a GameState.

Command keywords are constants (not scattered string literals), and
dispatch is a keyword -> handler lookup rather than an if/elif chain, so
a future iteration can register a new command without touching existing
handlers.
"""

from parser import COMMANDS_MARKER
from renderer import render
from stream_reader import read_section

CLICK = "click"
WAIT = "wait"
PRINT = "print"
PRINT_BOARD_TARGET = "board"
JUMP = "jump"  # iteration11

CELL_SIZE_PX = 100


def parse_commands_section(lines):
    command_lines = read_section(lines, COMMANDS_MARKER, None)
    return [line.split() for line in command_lines]


def pixel_to_cell(x, y, cell_size_px=CELL_SIZE_PX):
    return y // cell_size_px, x // cell_size_px


def execute_commands(command_token_lists, game_state, output):
    handlers = {
        CLICK: lambda args: _handle_click(args, game_state),
        WAIT: lambda args: game_state.handle_wait(int(args[0])),
        PRINT: lambda args: _handle_print(args, game_state, output),
        JUMP: lambda args: _handle_jump(args, game_state),  # iteration11
    }
    for tokens in command_token_lists:
        if not tokens:
            continue
        handler = handlers.get(tokens[0])
        if handler:
            handler(tokens[1:])


def _handle_click(args, game_state):
    x, y = int(args[0]), int(args[1])
    row, col = pixel_to_cell(x, y)
    game_state.handle_click(row, col)


def _handle_print(args, game_state, output):
    if args and args[0] == PRINT_BOARD_TARGET:
        output(render(game_state.board()))


def _handle_jump(args, game_state):  # iteration11
    x, y = int(args[0]), int(args[1])
    row, col = pixel_to_cell(x, y)
    game_state.handle_jump(row, col)
