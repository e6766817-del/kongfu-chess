"""Entry point: builds a standard starting Board, wires it through
GameState/GameEngine/Controller (all from kfchess), and launches the
GameLoop.

Run with: python -m kfchess.gui.main [--skin pieces1|pieces2]
"""

import argparse
import functools
from types import SimpleNamespace

from kfchess.engine.game_engine import GameEngine
from kfchess.input import board_mapper
from kfchess.input.controller import Controller
from kfchess.io.validator import build_board
from kfchess.model.game_state import GameState

from kfchess.gui.board_view import BoardView
from kfchess.gui.clock import Clock
from kfchess.gui.config import (
    AVAILABLE_SKINS,
    BOARD_SIZE_CELLS,
    BOARD_X_OFFSET_PX,
    BOARD_Y_OFFSET_PX,
    DEFAULT_SKIN,
    LEFT_PANEL_X,
    RIGHT_PANEL_X,
)
from kfchess.gui.game_loop import GameLoop
from kfchess.gui.hud_message import HudMessage
from kfchess.gui.piece_sprites import SpriteSetCache
from kfchess.gui.renderer import Renderer
from kfchess.gui.side_panel import SidePanel

# Standard chess starting position, in the "<color><kind>" token format
# kfchess.io.validator.build_board expects (see kfchess.io.pieces_config).
STARTING_GRID = [
    "bR bN bB bQ bK bB bN bR".split(),
    ["bP"] * 8,
    ["."] * 8,
    ["."] * 8,
    ["."] * 8,
    ["."] * 8,
    ["wP"] * 8,
    "wR wN wB wQ wK wB wN wR".split(),
]


def build_game():
    board = build_board(STARTING_GRID)
    game_engine = GameEngine(board)
    game_state = GameState(board)
    # The board is drawn past the left SidePanel and its own coordinate
    # margin (see BoardView.cell_to_pixel), so raw mouse clicks need the
    # same x/y offsets to land on the right cell.
    gui_board_mapper = SimpleNamespace(
        pixel_to_cell=functools.partial(
            board_mapper.pixel_to_cell, x_offset=BOARD_X_OFFSET_PX, y_offset=BOARD_Y_OFFSET_PX
        )
    )
    controller = Controller(game_engine, game_state, board_mapper=gui_board_mapper)
    return game_engine, game_state, controller


def build_game_loop(game_engine, game_state, controller, skin=DEFAULT_SKIN):
    board_view = BoardView(skin)
    clock = Clock()
    white_panel = SidePanel("w", LEFT_PANEL_X, BOARD_SIZE_CELLS, skin=skin)
    black_panel = SidePanel("b", RIGHT_PANEL_X, BOARD_SIZE_CELLS, skin=skin)
    game_engine.add_observer(white_panel)
    game_engine.add_observer(black_panel)
    hud_message = HudMessage()
    renderer = Renderer(board_view, clock, (white_panel, black_panel), hud_message)
    sprite_set_cache = SpriteSetCache(skin)
    return GameLoop(game_engine, game_state, controller, renderer, board_view, sprite_set_cache, hud_message)


def parse_args():
    parser = argparse.ArgumentParser(description="Kung-fu chess GUI.")
    parser.add_argument("--skin", choices=AVAILABLE_SKINS, default=DEFAULT_SKIN)
    return parser.parse_args()


def main():
    args = parse_args()
    game_engine, game_state, controller = build_game()
    game_loop = build_game_loop(game_engine, game_state, controller, skin=args.skin)
    game_loop.run()


if __name__ == "__main__":
    main()
