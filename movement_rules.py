# iteration3
"""Movement-shape rules: whether a piece type's geometry allows moving
from one cell to another. Shape only -- no blocking-piece or capture
checks yet.

Piece type -> rule is a lookup (not an if/elif chain), so a future
user-defined game can register a new piece type's movement rule
without touching existing ones. A piece type with no registered rule
is treated as unrestricted, so piece types not covered by this
iteration (e.g. pawns) keep behaving as they did before this iteration.
"""

from pieces_config import PAWN_TYPE  # iteration10


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


# iteration5
# Row direction each color's pawns advance toward: white moves to a
# lower row index ("upward" in the printed board), black to a higher
# one ("downward"). Config, not a literal buried in _pawn_shape.
PAWN_FORWARD_ROW_DELTA = {"w": -1, "b": 1}


# iteration10: the row each color's pawns start on / promote on, given
# the board's height. Config-driven the same way PAWN_FORWARD_ROW_DELTA
# is, rather than a number buried in _pawn_shape. Pawns start on their
# own home edge (the fixture places them there directly, there's no
# separate back rank the way a standard chess set has one) and promote
# on the opposite edge.
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


# iteration5, iteration10
def _pawn_shape(delta_row, delta_col, color=None, is_capture=False, from_row=None, board_height=None, **_context):
    forward = PAWN_FORWARD_ROW_DELTA.get(color)
    if forward is None:
        return False
    if delta_col == 0:
        if is_capture:
            return False  # can't capture moving straight ahead
        if delta_row == forward:
            return True
        # iteration10: two cells forward, only from the pawn's start row
        return delta_row == forward * 2 and _is_at_pawn_start_row(color, from_row, board_height)
    if abs(delta_col) == 1:
        return is_capture and delta_row == forward  # diagonal only when actually capturing
    return False


MOVEMENT_SHAPES = {
    "K": _king_shape,
    "Q": _queen_shape,
    "R": _rook_shape,
    "B": _bishop_shape,
    "N": _knight_shape,
    "P": _pawn_shape,  # iteration5
}


def is_legal_shape(piece_type, delta_row, delta_col, color=None, is_capture=False, from_row=None, board_height=None):
    shape = MOVEMENT_SHAPES.get(piece_type)
    if shape is None:
        return True
    return shape(delta_row, delta_col, color=color, is_capture=is_capture, from_row=from_row, board_height=board_height)


# iteration4
# Pieces that slide across multiple cells in one move and so can be
# blocked by whatever occupies the cells in between. Piece types not
# listed here (king, knight) never have their path checked.
SLIDING_PIECE_TYPES = {"R", "B", "Q"}


def _steps(delta_row, delta_col):
    return max(abs(delta_row), abs(delta_col))


def _path_cells(delta_row, delta_col):
    steps = _steps(delta_row, delta_col)
    if steps <= 1:
        return []
    step_row = (delta_row > 0) - (delta_row < 0)
    step_col = (delta_col > 0) - (delta_col < 0)
    return [(step_row * i, step_col * i) for i in range(1, steps)]


def is_path_clear(board, from_row, from_col, delta_row, delta_col, empty_token):
    for offset_row, offset_col in _path_cells(delta_row, delta_col):
        if board.get(from_row + offset_row, from_col + offset_col) != empty_token:
            return False
    return True


def is_legal_move(piece_type, board, from_row, from_col, to_row, to_col, empty_token, color=None):
    delta_row, delta_col = to_row - from_row, to_col - from_col
    is_capture = board.get(to_row, to_col) != empty_token  # iteration5
    board_height, _ = board.dimensions()  # iteration10: pawn start-row needs this
    if not is_legal_shape(piece_type, delta_row, delta_col, color, is_capture, from_row, board_height):
        return False
    if piece_type in SLIDING_PIECE_TYPES:
        return is_path_clear(board, from_row, from_col, delta_row, delta_col, empty_token)
    if piece_type == PAWN_TYPE and abs(delta_row) == 2:
        # iteration10: the pawn's 2-cell start move must also have a
        # clear path -- reuses the same path-cell logic sliding pieces
        # use, since it already handles a single square in between.
        return is_path_clear(board, from_row, from_col, delta_row, delta_col, empty_token)
    return True


# iteration6
# How long a move takes to complete: milliseconds per cell of Chebyshev
# distance travelled (a 3-cell diagonal costs the same as a 3-cell
# straight line, matching how _steps already measures distance above).
MS_PER_CELL = 1000


def move_duration_ms(delta_row, delta_col):
    return _steps(delta_row, delta_col) * MS_PER_CELL
