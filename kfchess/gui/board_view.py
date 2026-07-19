"""Board background + Position<->pixel conversion, drawn through Img."""

import cv2
import numpy as np

from kfchess.gui import assets
from kfchess.gui.config import (
    BOARD_MARGIN_PX,
    BOARD_SIZE_CELLS,
    BOARD_SIZE_PX,
    BOARD_X_OFFSET_PX,
    BOARD_Y_OFFSET_PX,
    CANVAS_SIZE_PX,
    CELL_SIZE_PX,
    DEFAULT_SKIN,
    HUD_TOP_PX,
    SIDE_PANEL_WIDTH_PX,
)
from kfchess.gui.img import Img

HUD_BACKGROUND_COLOR = (32, 32, 32, 255)  # BGRA, dark gray

# The board frame -- the BOARD_MARGIN_PX ring around the 8x8 grid,
# outside the side panels -- holds the file letters (a-h, bottom edge)
# and rank numbers (1-8, left edge), like a physical/professional
# chess board, rather than stamping labels inside the corner of each
# edge square.
FRAME_COLOR = (40, 36, 34, 255)  # BGRA, warm dark taupe (echoes SidePanel's theme)
FRAME_BORDER_COLOR = (0, 179, 255, 255)  # BGRA, gold -- same accent as SidePanel
FRAME_BORDER_THICKNESS = 2
COORDINATE_FONT_SCALE = 0.5
COORDINATE_FONT_THICKNESS = 1
COORDINATE_TEXT_COLOR = (0, 179, 255, 255)  # BGRA, gold


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
        SidePanel and the board's coordinate margin."""
        return position.col * CELL_SIZE_PX + BOARD_X_OFFSET_PX, position.row * CELL_SIZE_PX + BOARD_Y_OFFSET_PX

    def new_canvas(self):
        """A fresh Img sized for the two side panels plus the board
        (with its coordinate-label margin) and the HUD strip below it
        (see kfchess.gui.config.SIDE_PANEL_WIDTH_PX / HUD_HEIGHT_PX),
        safe to draw pieces and HUD/panel text onto without mutating
        the cached board image."""
        self._ensure_loaded()
        canvas_w, canvas_h = CANVAS_SIZE_PX
        board_pixels = self._board_img.img
        channels = board_pixels.shape[2]

        canvas_pixels = np.empty((canvas_h, canvas_w, channels), dtype=board_pixels.dtype)
        canvas_pixels[:, :] = HUD_BACKGROUND_COLOR[:channels]

        frame_x0 = BOARD_X_OFFSET_PX - BOARD_MARGIN_PX
        frame_x1 = BOARD_X_OFFSET_PX + BOARD_SIZE_PX[0] + BOARD_MARGIN_PX
        canvas_pixels[0:HUD_TOP_PX, frame_x0:frame_x1] = FRAME_COLOR[:channels]

        board_h, board_w = board_pixels.shape[:2]
        canvas_pixels[BOARD_Y_OFFSET_PX:BOARD_Y_OFFSET_PX + board_h, BOARD_X_OFFSET_PX:BOARD_X_OFFSET_PX + board_w] = (
            board_pixels
        )

        canvas = Img()
        canvas.img = canvas_pixels
        self._draw_frame_border(canvas)
        self._draw_coordinates(canvas)
        return canvas

    def _draw_frame_border(self, canvas):
        """A thin gold outline right at the board's edge, like a picture
        frame separating the grid from its coordinate margin."""
        x0, y0 = BOARD_X_OFFSET_PX - 1, BOARD_Y_OFFSET_PX - 1
        x1, y1 = BOARD_X_OFFSET_PX + BOARD_SIZE_PX[0], BOARD_Y_OFFSET_PX + BOARD_SIZE_PX[1]
        cv2.rectangle(canvas.img, (x0, y0), (x1, y1), FRAME_BORDER_COLOR, FRAME_BORDER_THICKNESS)

    def _draw_coordinates(self, canvas):
        """File letters (a-h) centered under each column, rank numbers
        (8-1, top to bottom) centered left of each row -- both drawn in
        the margin outside the grid, not overlapping any square."""
        for col in range(BOARD_SIZE_CELLS):
            label = chr(ord("a") + col)
            (text_w, text_h), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, COORDINATE_FONT_SCALE, COORDINATE_FONT_THICKNESS
            )
            x = BOARD_X_OFFSET_PX + col * CELL_SIZE_PX + CELL_SIZE_PX // 2 - text_w // 2
            y = HUD_TOP_PX - BOARD_MARGIN_PX // 2 + text_h // 2
            canvas.put_text(label, x, y, COORDINATE_FONT_SCALE, color=COORDINATE_TEXT_COLOR)

        for row in range(BOARD_SIZE_CELLS):
            label = str(BOARD_SIZE_CELLS - row)
            (text_w, text_h), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, COORDINATE_FONT_SCALE, COORDINATE_FONT_THICKNESS
            )
            x = SIDE_PANEL_WIDTH_PX + (BOARD_MARGIN_PX - text_w) // 2
            y = BOARD_Y_OFFSET_PX + row * CELL_SIZE_PX + CELL_SIZE_PX // 2 + text_h // 2
            canvas.put_text(label, x, y, COORDINATE_FONT_SCALE, color=COORDINATE_TEXT_COLOR)
