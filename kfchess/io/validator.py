"""Validates a raw token grid and builds a Board from it.

The legal-token set is accepted as a parameter (defaulting to the
configured set) rather than imported and used implicitly, so a future
user-defined-game feature can validate against a custom piece set
without changing this function.
"""

from kfchess.io.errors import RowWidthMismatchError, UnknownTokenError
from kfchess.io.pieces_config import EMPTY_TOKEN, LEGAL_TOKENS
from kfchess.model.board import Board
from kfchess.model.piece import Piece
from kfchess.model.position import Position


def build_board(grid, legal_tokens=LEGAL_TOKENS):
    if not grid:
        return Board(0, 0)

    width = len(grid[0])
    for row in grid:
        if len(row) != width:
            raise RowWidthMismatchError()
        for cell in row:
            if cell not in legal_tokens:
                raise UnknownTokenError()

    height = len(grid)
    board = Board(height, width)
    for row_index, row in enumerate(grid):
        for col_index, token in enumerate(row):
            if token != EMPTY_TOKEN:
                board.set(Position(row_index, col_index), Piece(token[0], token[1:]))
    return board
