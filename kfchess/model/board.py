"""Board: encapsulates board storage behind a small public API, same
role as the old flat board.py, but keyed by Position/Piece value
objects instead of a list-of-lists of token strings.

Storage is a dict of Position -> Piece; an absent key means the cell
is empty. Dimensions are stored explicitly since a sparse dict can't
infer a rectangular extent from its occupied cells alone.
"""

from kfchess.model.position import Position


class Board:
    def __init__(self, height, width, cells=None):
        self._height = height
        self._width = width
        self._cells = dict(cells) if cells else {}

    def dimensions(self):
        return self._height, self._width

    def get(self, position):
        return self._cells.get(position)

    def set(self, position, piece):
        if piece is None:
            self._cells.pop(position, None)
        else:
            self._cells[position] = piece

    def move(self, from_position, to_position):
        piece = self.get(from_position)
        self.set(from_position, None)
        self.set(to_position, piece)

    def is_inside(self, position):
        return 0 <= position.row < self._height and 0 <= position.col < self._width

    def all_positions(self):
        for row in range(self._height):
            for col in range(self._width):
                yield Position(row, col)
