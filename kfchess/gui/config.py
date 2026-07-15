"""GUI-wide constants: cell size, skins, assets root.

Every skin under assets/ has its own native sprite resolution
(pieces1 sprites are ~389x386px, pieces2 sprites are 64x64px), so
nothing downstream may assume a skin's native pixel size. All loading
code must resize to SPRITE_SIZE_PX / BOARD_SIZE_PX -- that's what
makes switching DEFAULT_SKIN (or passing --skin) a one-line change.
"""

import pathlib

from kfchess.input.board_mapper import CELL_SIZE_PX

ASSETS_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent / "assets"
AVAILABLE_SKINS = ("pieces1", "pieces2")
DEFAULT_SKIN = "pieces1"
PIECE_STATES = ("idle", "move", "jump", "short_rest", "long_rest")
FRAMES_PER_STATE = 5

BOARD_SIZE_CELLS = 8
BOARD_SIZE_PX = (BOARD_SIZE_CELLS * CELL_SIZE_PX, BOARD_SIZE_CELLS * CELL_SIZE_PX)
SPRITE_SIZE_PX = (CELL_SIZE_PX, CELL_SIZE_PX)

# The scoreboard and HUD message get their own strip below the board
# rather than drawing over the last rank's pieces.
HUD_HEIGHT_PX = 90
CANVAS_SIZE_PX = (BOARD_SIZE_PX[0], BOARD_SIZE_PX[1] + HUD_HEIGHT_PX)

__all__ = [
    "CELL_SIZE_PX",
    "ASSETS_ROOT",
    "AVAILABLE_SKINS",
    "DEFAULT_SKIN",
    "PIECE_STATES",
    "FRAMES_PER_STATE",
    "BOARD_SIZE_CELLS",
    "BOARD_SIZE_PX",
    "SPRITE_SIZE_PX",
    "HUD_HEIGHT_PX",
    "CANVAS_SIZE_PX",
]
