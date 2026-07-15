"""Board background + Position<->pixel conversion, drawn through Img."""

import numpy as np

from kfchess.gui import assets
from kfchess.gui.config import BOARD_SIZE_PX, BOARD_X_OFFSET_PX, CANVAS_SIZE_PX, CELL_SIZE_PX, DEFAULT_SKIN
from kfchess.gui.img import Img

HUD_BACKGROUND_COLOR = (32, 32, 32, 255)  # BGRA, dark gray


class BoardView:
    def __init__(self, skin=DEFAULT_SKIN):
        self._skin = skin
        self._board_img = None  # Img, loaded lazily

    def _ensure_loaded(self):
        if self._board_img is None:
            self._board_img = Img().read(assets.board_image_path(self._skin), size=BOARD_SIZE_PX)

    def cell_to_pixel(self, position):
        """Top-left pixel of `position`'s cell (inverse of
        kfchess.input.board_mapper.pixel_to_cell), offset past the left
        SidePanel so the board sits centered between the two panels."""
        return position.col * CELL_SIZE_PX + BOARD_X_OFFSET_PX, position.row * CELL_SIZE_PX

    def new_canvas(self):
        """A fresh Img sized for the two side panels plus the board and
        the HUD strip below it (see kfchess.gui.config.SIDE_PANEL_WIDTH_PX
        / HUD_HEIGHT_PX), safe to draw pieces and HUD/panel text onto
        without mutating the cached board image."""
        self._ensure_loaded()
        canvas_w, canvas_h = CANVAS_SIZE_PX
        board_pixels = self._board_img.img

        canvas_pixels = np.empty((canvas_h, canvas_w, board_pixels.shape[2]), dtype=board_pixels.dtype)
        canvas_pixels[:, :] = HUD_BACKGROUND_COLOR[: board_pixels.shape[2]]
        board_h, board_w = board_pixels.shape[:2]
        canvas_pixels[:board_h, BOARD_X_OFFSET_PX:BOARD_X_OFFSET_PX + board_w] = board_pixels

        canvas = Img()
        canvas.img = canvas_pixels
        return canvas
