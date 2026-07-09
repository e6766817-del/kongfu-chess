"""BoardMapper: converts pixel coordinates into board cells.

Ported from the old flat commands.py's pixel_to_cell/CELL_SIZE_PX,
which used to sit alongside command-dispatch/script-runner concerns.
"""

from kfchess.model.position import Position

CELL_SIZE_PX = 100


def pixel_to_cell(x, y, cell_size_px=CELL_SIZE_PX):
    return Position(y // cell_size_px, x // cell_size_px)
