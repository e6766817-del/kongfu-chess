"""Covers the Piece value type itself: id/color/kind/cell/state fields
and the defaults new call sites rely on (auto id, idle state, no cell).
"""

from kfchess.model.piece import CAPTURED_STATE, IDLE_STATE, Piece
from kfchess.model.position import Position


def test_piece_defaults():
    piece = Piece("w", "K")
    assert piece.color == "w"
    assert piece.kind == "K"
    assert piece.cell is None
    assert piece.state == IDLE_STATE
    assert isinstance(piece.id, int)


def test_piece_ids_are_unique():
    first = Piece("w", "K")
    second = Piece("b", "K")
    assert first.id != second.id


def test_piece_cell_and_state_are_settable():
    piece = Piece("w", "P", cell=Position(1, 4), state=CAPTURED_STATE)
    assert piece.cell == Position(1, 4)
    assert piece.state == CAPTURED_STATE
