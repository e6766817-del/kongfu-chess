"""BoardMapper: converts pixel coordinates into board cells.

Ported from the old flat commands.py's pixel_to_cell/CELL_SIZE_PX,
which used to sit alongside command-dispatch/script-runner concerns.
"""

from kfchess.model.position import Position

CELL_SIZE_PX = 100


def pixel_to_cell(x, y, cell_size_px=CELL_SIZE_PX, x_offset=0):
    """`x_offset` is the pixel column the board itself starts at (e.g.
    past a side panel drawn to its left) -- a click left of it maps to
    a negative column, which callers reject via Board.is_inside()."""
    return Position(y // cell_size_px, (x - x_offset) // cell_size_px)
