"""GUI-wide constants: cell size, default skin, assets root."""

import pathlib

from kfchess.input.board_mapper import CELL_SIZE_PX

ASSETS_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent / "assets"
DEFAULT_SKIN = "pieces1"
PIECE_STATES = ("idle", "move", "jump", "short_rest", "long_rest")
FRAMES_PER_STATE = 5

__all__ = ["CELL_SIZE_PX", "ASSETS_ROOT", "DEFAULT_SKIN", "PIECE_STATES", "FRAMES_PER_STATE"]
