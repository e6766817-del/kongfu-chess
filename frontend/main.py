"""Entry point: builds a standard starting Board, wires it through
GameState/GameEngine/Controller (all from kfchess), and launches the
GameLoop.

Run with: python -m frontend.main
"""

from kfchess.engine.game_engine import GameEngine
from kfchess.input.controller import Controller
from kfchess.io.validator import build_board
from kfchess.model.game_state import GameState

from frontend.board_view import BoardView
from frontend.config import DEFAULT_SKIN
from frontend.game_loop import GameLoop
from frontend.piece_sprites import SpriteSetCache
from frontend.renderer import Renderer
from frontend.scoreboard import ScoreBoard

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


def build_renderer(skin=DEFAULT_SKIN):
    board_view = BoardView(skin)
    sprite_set_cache = SpriteSetCache(skin)
    scoreboard = ScoreBoard()
    return Renderer(board_view, sprite_set_cache, scoreboard)


def main():
    game_engine, game_state, controller = build_game()
    renderer = build_renderer()
    game_loop = GameLoop(game_engine, game_state, controller, renderer)
    game_loop.run()


if __name__ == "__main__":
    main()
