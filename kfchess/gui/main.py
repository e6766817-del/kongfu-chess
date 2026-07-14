"""Entry point: builds a standard starting Board, wires it through
GameState/GameEngine/Controller (all from kfchess), and launches the
GameLoop.

Run with: python -m kfchess.gui.main [--skin pieces1|pieces2]
"""

import argparse

from kfchess.engine.game_engine import GameEngine
from kfchess.input.controller import Controller
from kfchess.io.validator import build_board
from kfchess.model.game_state import GameState

from kfchess.gui.board_view import BoardView
from kfchess.gui.config import AVAILABLE_SKINS, DEFAULT_SKIN
from kfchess.gui.game_loop import GameLoop
from kfchess.gui.piece_sprites import SpriteSetCache
from kfchess.gui.renderer import Renderer
from kfchess.gui.scoreboard import ScoreBoard

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
    controller = Controller(game_engine, game_state)
    return game_engine, game_state, controller


def build_game_loop(game_engine, game_state, controller, skin=DEFAULT_SKIN):
    board_view = BoardView(skin)
    scoreboard = ScoreBoard()
    renderer = Renderer(board_view, scoreboard)
    sprite_set_cache = SpriteSetCache(skin)
    return GameLoop(game_engine, game_state, controller, renderer, sprite_set_cache)


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
