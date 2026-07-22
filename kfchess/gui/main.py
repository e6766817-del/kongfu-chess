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
from kfchess.gui.home_screen import HomeScreen
from kfchess.gui.hud_message import HudMessage
from kfchess.gui.login_screen import LoginScreen
from kfchess.gui.logging_config import setup_logging
from kfchess.gui.matchmaking_screen import MatchmakingScreen
from kfchess.gui.network_client import NetworkClient
from kfchess.gui.piece_sprites import SpriteSetCache
from kfchess.gui.renderer import Renderer
from kfchess.gui.room_dialog import RoomDialog
from kfchess.gui.side_panel import SidePanel
from kfchess.gui.skin_menu import SkinMenu
from kfchess.gui.sound import SoundPlayer

DEFAULT_SERVER_URI = "ws://localhost:8765"

# Sentinel my_color passed to Controller for spectators -- never equals "w"
# or "b", so Controller._is_own_piece is always False and clicks are a
# no-op, without needing any spectator-specific branching in Controller or
# GameLoop (see kfchess.input.controller).
VIEWER_COLOR = "v"

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


def _gui_board_mapper():
    # The board is drawn past the left SidePanel and its own coordinate
    # margin (see BoardView.cell_to_pixel), so raw mouse clicks need the
    # same x/y offsets to land on the right cell.
    return SimpleNamespace(
        pixel_to_cell=functools.partial(
            board_mapper.pixel_to_cell, x_offset=BOARD_X_OFFSET_PX, y_offset=BOARD_Y_OFFSET_PX
        )
    )


def build_game():
    board = build_board(STARTING_GRID)
    game_engine = GameEngine(board)
    game_state = GameState(board)
    controller = Controller(game_engine, game_state, board_mapper=_gui_board_mapper())
    return game_engine, game_state, controller


def build_online_game(server_uri):
    """Connects to kfchess.server, blocks in the login screen until the
    player logs in (or quits), then blocks in the Home screen until the
    player picks Play (anonymous rating-based matchmaking) or Room
    (create/join a specific room, possibly as a read-only viewer -- see
    kfchess.gui.room_dialog), then builds the same GameEngine/GameState/
    Controller trio either way -- Controller is given my_color so it only
    ever acts on this client's own pieces (or, for a viewer, never acts at
    all -- see VIEWER_COLOR), and GameLoop is given the NetworkClient so it
    can send this player's moves and replay the opponent's.

    Returns (game_engine, game_state, controller, network_client,
    usernames_by_color, ratings_by_color), or None if the player quits at
    any step."""
    network_client = NetworkClient(server_uri)
    login_result = LoginScreen(network_client).run()
    if login_result is None:
        return None
    username, _password, rating = login_result

    action = HomeScreen(username, rating).run()
    if action is None:
        return None

    if action == "room":
        matched = RoomDialog(network_client).run()
    else:
        network_client.join_queue()
        result = MatchmakingScreen(network_client).run()
        matched = None if result is None else ("player",) + result

    if matched is None:
        return None
    return _build_from_match(matched, network_client)


def _build_from_match(matched, network_client):
    """Builds the GameEngine/GameState/Controller trio from either a
    ("player", ...) result (MatchmakingScreen or RoomDialog, when this
    client is White or Black) or a ("viewer", ...) result (RoomDialog,
    the 3rd+ joiner of a room)."""
    kind = matched[0]
    if kind == "player":
        _, color, board_rows, username, opponent_username, rating, opponent_rating = matched
        opponent_color = "b" if color == "w" else "w"
        usernames_by_color = {color: username, opponent_color: opponent_username}
        ratings_by_color = {color: rating, opponent_color: opponent_rating}
        my_color = color
    else:
        _, board_rows, white_username, black_username, white_rating, black_rating = matched
        usernames_by_color = {"w": white_username, "b": black_username}
        ratings_by_color = {"w": white_rating, "b": black_rating}
        my_color = VIEWER_COLOR

    board = build_board([row.split() for row in board_rows])
    game_engine = GameEngine(board)
    game_state = GameState(board)
    controller = Controller(game_engine, game_state, board_mapper=_gui_board_mapper(), my_color=my_color)
    return game_engine, game_state, controller, network_client, usernames_by_color, ratings_by_color


def build_game_loop(
    game_engine, game_state, controller, skin=DEFAULT_SKIN, network_client=None,
    usernames_by_color=None, ratings_by_color=None,
):
    usernames_by_color = usernames_by_color or {}
    ratings_by_color = ratings_by_color or {}
    board_view = BoardView(skin)
    clock = Clock()
    white_panel = SidePanel(
        "w", LEFT_PANEL_X, BOARD_SIZE_CELLS, skin=skin,
        username=usernames_by_color.get("w"), rating=ratings_by_color.get("w"),
    )
    black_panel = SidePanel(
        "b", RIGHT_PANEL_X, BOARD_SIZE_CELLS, skin=skin,
        username=usernames_by_color.get("b"), rating=ratings_by_color.get("b"),
    )
    game_engine.add_observer(white_panel)
    game_engine.add_observer(black_panel)
    sound_player = SoundPlayer()
    game_engine.add_observer(sound_player)
    hud_message = HudMessage()
    renderer = Renderer(board_view, clock, (white_panel, black_panel), hud_message)
    sprite_set_cache = SpriteSetCache(skin)
    return GameLoop(
        game_engine, game_state, controller, renderer, board_view, sprite_set_cache, hud_message,
        network_client=network_client, sound_player=sound_player,
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Kung-fu chess GUI.")
    parser.add_argument(
        "--skin", choices=AVAILABLE_SKINS, default=None,
        help="Skip the in-app skin picker and start directly with this skin.",
    )
    parser.add_argument(
        "--server", nargs="?", const=DEFAULT_SERVER_URI, default=None,
        help=(
            "Play online instead of local single-window play: connect to a "
            f"kfchess.server (default {DEFAULT_SERVER_URI} if no URI given), "
            "wait for matchmaking, and control only your assigned color."
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.server is not None:
        setup_logging()
    skin = args.skin
    if skin is None:
        skin = SkinMenu().run()
        if skin is None:
            return

    if args.server is not None:
        built = build_online_game(args.server)
        if built is None:
            return
        game_engine, game_state, controller, network_client, usernames_by_color, ratings_by_color = built
    else:
        game_engine, game_state, controller = build_game()
        network_client = None
        usernames_by_color = None
        ratings_by_color = None

    game_loop = build_game_loop(
        game_engine, game_state, controller, skin=skin, network_client=network_client,
        usernames_by_color=usernames_by_color, ratings_by_color=ratings_by_color,
    )
    game_loop.run()


if __name__ == "__main__":
    main()
