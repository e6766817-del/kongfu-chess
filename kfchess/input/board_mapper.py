"""BoardMapper: converts pixel coordinates into board cells.

Ported from the old flat commands.py's pixel_to_cell/CELL_SIZE_PX,
which used to sit alongside command-dispatch/script-runner concerns.
"""

from kfchess.model.position import Position

CELL_SIZE_PX = 100


def pixel_to_cell(x, y, cell_size_px=CELL_SIZE_PX, x_offset=0, y_offset=0):
    """`x_offset`/`y_offset` are the pixel column/row the board itself
    starts at (e.g. past a side panel to its left, or a coordinate
    margin above it) -- a click outside them maps to a negative row/
    column, which callers reject via Board.is_inside()."""
    return Position((y - y_offset) // cell_size_px, (x - x_offset) // cell_size_px)
