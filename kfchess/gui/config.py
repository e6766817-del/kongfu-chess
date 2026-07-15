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

# The HUD message strip below the board, for the transient move-rejection
# banner and the game clock -- everything color-specific (score, captures,
# move history) lives in the side panels instead, see SidePanel.
HUD_HEIGHT_PX = 70

# A SidePanel flanks each side of the board -- white's on the left,
# black's on the right -- each spanning the full canvas height, so a
# player's own score/captures/move-history all live together on their
# own side rather than sharing a strip under the board.
SIDE_PANEL_WIDTH_PX = 240
BOARD_X_OFFSET_PX = SIDE_PANEL_WIDTH_PX
LEFT_PANEL_X = 0
RIGHT_PANEL_X = BOARD_X_OFFSET_PX + BOARD_SIZE_PX[0]

CANVAS_SIZE_PX = (SIDE_PANEL_WIDTH_PX * 2 + BOARD_SIZE_PX[0], BOARD_SIZE_PX[1] + HUD_HEIGHT_PX)

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
    "SIDE_PANEL_WIDTH_PX",
    "BOARD_X_OFFSET_PX",
    "LEFT_PANEL_X",
    "RIGHT_PANEL_X",
    "CANVAS_SIZE_PX",
]
