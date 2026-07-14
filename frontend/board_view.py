"""Board background + Position<->pixel conversion, drawn through Img."""

from frontend.config import CELL_SIZE_PX, DEFAULT_SKIN


class BoardView:
    def __init__(self, skin=DEFAULT_SKIN):
        self._skin = skin
        self._board_img = None  # Img, loaded lazily

    def cell_to_pixel(self, position):
        """Top-left pixel of `position`'s cell (inverse of
        kfchess.input.board_mapper.pixel_to_cell)."""
        # TODO: return position.col * CELL_SIZE_PX, position.row * CELL_SIZE_PX
        raise NotImplementedError

    def draw(self, canvas):
        """Blit the board background onto `canvas` (an Img)."""
        # TODO: load board.png via frontend.assets.board_image_path on first
        # use (Img().read(...)), then canvas is drawn on top of/starts as
        # a copy of it.
        raise NotImplementedError


assert CELL_SIZE_PX > 0
