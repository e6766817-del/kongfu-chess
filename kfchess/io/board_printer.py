"""Formats a Board back into its canonical text form.

Ported from the old flat renderer.py's render(), adapted to the new
Board's dict storage -- unlike the old list-of-lists Board, an empty
cell here is simply absent from the dict, so the printer must iterate
the full rectangle (via board.dimensions()) rather than enumerate
occupied cells, filling in "." for absent ones.
"""

from kfchess.io.pieces_config import EMPTY_TOKEN
from kfchess.model.position import Position


def _token(piece):
    if piece is None:
        return EMPTY_TOKEN
    return piece.color + piece.kind


def render(board):
    height, width = board.dimensions()
    rows = []
    for row in range(height):
        rows.append(" ".join(_token(board.get(Position(row, col))) for col in range(width)))
    return "\n".join(rows)
