"""Movement-shape rules: whether a piece type's geometry allows moving
from one cell to another. Shape only -- no blocking-piece or capture
checks here, that's rule_engine.py's job.

Piece type -> rule is a lookup (not an if/elif chain) so a new piece
type can be registered without touching existing ones. A piece type
with no registered rule is unrestricted.
"""


def _is_straight_line(delta_row, delta_col):
    return (delta_row == 0) != (delta_col == 0)


def _is_diagonal_line(delta_row, delta_col):
    return delta_row != 0 and abs(delta_row) == abs(delta_col)


def _king_shape(delta_row, delta_col, color=None, is_capture=False, **_context):
    return max(abs(delta_row), abs(delta_col)) == 1


def _rook_shape(delta_row, delta_col, color=None, is_capture=False, **_context):
    return _is_straight_line(delta_row, delta_col)


def _bishop_shape(delta_row, delta_col, color=None, is_capture=False, **_context):
    return _is_diagonal_line(delta_row, delta_col)


def _queen_shape(delta_row, delta_col, color=None, is_capture=False, **_context):
    return _is_straight_line(delta_row, delta_col) or _is_diagonal_line(delta_row, delta_col)


def _knight_shape(delta_row, delta_col, color=None, is_capture=False, **_context):
    return sorted((abs(delta_row), abs(delta_col))) == [1, 2]


# Row direction each color's pawns advance toward: white moves to a
# lower row index, black to a higher one.
PAWN_FORWARD_ROW_DELTA = {"w": -1, "b": 1}


def pawn_start_row(color, board_height):
    if color == "w":
        return board_height - 1
    if color == "b":
        return 0
    return None


def pawn_promotion_row(color, board_height):
    if color == "w":
        return 0
    if color == "b":
        return board_height - 1
    return None


def _is_at_pawn_start_row(color, from_row, board_height):
    if from_row is None or board_height is None:
        return False
    return from_row == pawn_start_row(color, board_height)


def _pawn_shape(delta_row, delta_col, color=None, is_capture=False, from_row=None, board_height=None, **_context):
    forward = PAWN_FORWARD_ROW_DELTA.get(color)
    if forward is None:
        return False
    if delta_col == 0:
        if is_capture:
            return False
        if delta_row == forward:
            return True
        return delta_row == forward * 2 and _is_at_pawn_start_row(color, from_row, board_height)
    if abs(delta_col) == 1:
        return is_capture and delta_row == forward
    return False


MOVEMENT_SHAPES = {
    "K": _king_shape,
    "Q": _queen_shape,
    "R": _rook_shape,
    "B": _bishop_shape,
    "N": _knight_shape,
    "P": _pawn_shape,
}


def is_legal_shape(piece_type, delta_row, delta_col, color=None, is_capture=False, from_row=None, board_height=None):
    shape = MOVEMENT_SHAPES.get(piece_type)
    if shape is None:
        return True
    return shape(delta_row, delta_col, color=color, is_capture=is_capture, from_row=from_row, board_height=board_height)


# Pieces that slide across multiple cells in one move and so can be
# blocked by whatever occupies the cells in between.
SLIDING_PIECE_TYPES = {"R", "B", "Q"}


def steps(delta_row, delta_col):
    return max(abs(delta_row), abs(delta_col))
