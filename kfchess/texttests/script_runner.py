"""The composition root: wires BoardParser -> GameState/GameEngine/
Controller -> BoardPrinter for the stdin/stdout fixture format. This is
what main.py calls into.
"""

from kfchess.engine.game_engine import GameEngine
from kfchess.input.controller import Controller
from kfchess.io.board_printer import render
from kfchess.io.errors import BoardFixtureError
from kfchess.io.parser import parse_board_section
from kfchess.io.stream_reader import read_lines
from kfchess.io.validator import build_board
from kfchess.model.game_state import GameState
from kfchess.texttests.script_parser import (
    CLICK,
    JUMP,
    PRINT,
    PRINT_BOARD_TARGET,
    WAIT,
    parse_commands_section,
)


def run(stream, output):
    lines = read_lines(stream)
    grid = parse_board_section(lines)
    try:
        board = build_board(grid)
    except BoardFixtureError as error:
        output(error.code)
        return

    game_engine = GameEngine(board)
    game_state = GameState(board)
    controller = Controller(game_engine, game_state)

    handlers = {
        CLICK: lambda args: controller.handle_click_at_pixel(int(args[0]), int(args[1])),
        WAIT: lambda args: game_engine.advance_clock(int(args[0])),
        PRINT: lambda args: _handle_print(args, game_engine, output),
        JUMP: lambda args: controller.handle_jump_at_pixel(int(args[0]), int(args[1])),
    }

    for tokens in parse_commands_section(lines):
        if not tokens:
            continue
        handler = handlers.get(tokens[0])
        if handler:
            handler(tokens[1:])


def _handle_print(args, game_engine, output):
    if args and args[0] == PRINT_BOARD_TARGET:
        output(render(game_engine.board()))
