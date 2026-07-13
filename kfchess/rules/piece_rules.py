"""Per-piece rules: shape (does this piece's geometry allow the move)
and path clearance (is anything in the way). All piece-type-specific
logic lives here so rule_engine.py can stay generic orchestration.

Piece type -> rule is a lookup (not an if/elif chain) so a new piece
type can be registered without touching existing ones. A piece type
with no registered rule is unrestricted.
"""

from kfchess.model.piece import PAWN_TYPE


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
        return board_height - 2
    if color == "b":
        return 1
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


def _path_cells(from_position, delta_row, delta_col):
    step_count = steps(delta_row, delta_col)
    if step_count <= 1:
        return []
    step_row = (delta_row > 0) - (delta_row < 0)
    step_col = (delta_col > 0) - (delta_col < 0)
    return [from_position.translated(step_row * i, step_col * i) for i in range(1, step_count)]


def line_path_cells(from_position, to_position):
    """Interior cells strictly between from_position and to_position, in
    travel order, for moves that travel a single straight or diagonal
    line one cell per step. Returns None for moves with no such line
    (e.g. a knight's jump) -- those have no meaningful intermediate
    cells to collide on.
    """
    delta_row, delta_col = from_position.delta_to(to_position)
    if not (_is_straight_line(delta_row, delta_col) or _is_diagonal_line(delta_row, delta_col)):
        return None
    return _path_cells(from_position, delta_row, delta_col)


def _requires_clear_path(piece_type, delta_row):
    if piece_type in SLIDING_PIECE_TYPES:
        return True
    return piece_type == PAWN_TYPE and abs(delta_row) == 2


def is_path_clear(board, piece_type, from_position, delta_row, delta_col):
    if not _requires_clear_path(piece_type, delta_row):
        return True
    return all(board.get(cell) is None for cell in _path_cells(from_position, delta_row, delta_col))
