"""Validates a raw token grid and builds a Board from it.

The legal-token set is accepted as a parameter (defaulting to the
configured set) rather than imported and used implicitly, so a future
user-defined-game feature can validate against a custom piece set
without changing this function.
"""

from board import Board
from errors import RowWidthMismatchError, UnknownTokenError
from pieces_config import LEGAL_TOKENS


def validate_board(grid, legal_tokens=LEGAL_TOKENS):
    if not grid:
        return Board(grid)

    width = len(grid[0])
    for row in grid:
        if len(row) != width:
            raise RowWidthMismatchError()
        for cell in row:
            if cell not in legal_tokens:
                raise UnknownTokenError()

    return Board(grid)
