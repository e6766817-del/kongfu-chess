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


def _is_straight_line(delta_row, delta_col):
    return (delta_row == 0) != (delta_col == 0)


def _is_diagonal_line(delta_row, delta_col):
    return delta_row != 0 and abs(delta_row) == abs(delta_col)


def _king_shape(delta_row, delta_col, color=None, is_capture=False):
    return max(abs(delta_row), abs(delta_col)) == 1


def _rook_shape(delta_row, delta_col, color=None, is_capture=False):
    return _is_straight_line(delta_row, delta_col)


def _bishop_shape(delta_row, delta_col, color=None, is_capture=False):
    return _is_diagonal_line(delta_row, delta_col)


def _queen_shape(delta_row, delta_col, color=None, is_capture=False):
    return _is_straight_line(delta_row, delta_col) or _is_diagonal_line(delta_row, delta_col)


def _knight_shape(delta_row, delta_col, color=None, is_capture=False):
    return sorted((abs(delta_row), abs(delta_col))) == [1, 2]


# iteration5
# Row direction each color's pawns advance toward: white moves to a
# lower row index ("upward" in the printed board), black to a higher
# one ("downward"). Config, not a literal buried in _pawn_shape.
PAWN_FORWARD_ROW_DELTA = {"w": -1, "b": 1}


# iteration5
def _pawn_shape(delta_row, delta_col, color=None, is_capture=False):
    forward = PAWN_FORWARD_ROW_DELTA.get(color)
    if forward is None or delta_row != forward:
        return False
    if delta_col == 0:
        return not is_capture  # straight ahead only onto an empty cell
    if abs(delta_col) == 1:
        return is_capture  # diagonal only when actually capturing
    return False


MOVEMENT_SHAPES = {
    "K": _king_shape,
    "Q": _queen_shape,
    "R": _rook_shape,
    "B": _bishop_shape,
    "N": _knight_shape,
    "P": _pawn_shape,  # iteration5
}


def is_legal_shape(piece_type, delta_row, delta_col, color=None, is_capture=False):
    shape = MOVEMENT_SHAPES.get(piece_type)
    if shape is None:
        return True
    return shape(delta_row, delta_col, color, is_capture)


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
    if not is_legal_shape(piece_type, delta_row, delta_col, color, is_capture):
        return False
    if piece_type in SLIDING_PIECE_TYPES:
        return is_path_clear(board, from_row, from_col, delta_row, delta_col, empty_token)
    return True


# iteration6
# How long a move takes to complete: milliseconds per cell of Chebyshev
# distance travelled (a 3-cell diagonal costs the same as a 3-cell
# straight line, matching how _steps already measures distance above).
MS_PER_CELL = 1000


def move_duration_ms(delta_row, delta_col):
    return _steps(delta_row, delta_col) * MS_PER_CELL
