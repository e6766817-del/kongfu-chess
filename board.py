"""Board: encapsulates board storage behind a small public API.

Internal storage is a list-of-lists of token strings today. If a future
iteration switches to a binary/bitboard representation, only this file
changes -- callers only ever use dimensions()/get()/rows(), never the
internal structure directly.
"""


class Board:
    def __init__(self, grid):
        self._grid = grid

    def dimensions(self):
        height = len(self._grid)
        width = len(self._grid[0]) if height else 0
        return height, width

    def get(self, row, col):
        return self._grid[row][col]

    def set(self, row, col, token):
        self._grid[row][col] = token

    def move(self, from_row, from_col, to_row, to_col, empty_token):
        token = self.get(from_row, from_col)
        self.set(from_row, from_col, empty_token)
        self.set(to_row, to_col, token)

    def rows(self):
        return iter(self._grid)
