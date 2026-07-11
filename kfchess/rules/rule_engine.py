"""RuleEngine: is a requested move legal right now, and if not, why.

Combines movement_rules' shape check with path-clearance and capture
checks against a live Board, restructured to report a reason instead
of collapsing straight to True/False.
"""

from dataclasses import dataclass

from kfchess.model.piece import PAWN_TYPE
from kfchess.rules.movement_rules import SLIDING_PIECE_TYPES, is_legal_shape, steps

REASON_NO_PIECE = "no_piece_at_source"
REASON_FRIENDLY_DESTINATION = "destination_occupied_by_own_color"
REASON_WRONG_SHAPE = "illegal_shape"
REASON_PATH_BLOCKED = "path_blocked"


@dataclass(frozen=True)
class MoveLegality:
    is_legal: bool
    reason: str = None


def _path_cells(from_position, delta_row, delta_col):
    step_count = steps(delta_row, delta_col)
    if step_count <= 1:
        return []
    step_row = (delta_row > 0) - (delta_row < 0)
    step_col = (delta_col > 0) - (delta_col < 0)
    return [from_position.translated(step_row * i, step_col * i) for i in range(1, step_count)]


def is_path_clear(board, from_position, delta_row, delta_col):
    return all(board.get(cell) is None for cell in _path_cells(from_position, delta_row, delta_col))


class RuleEngine:
    def evaluate(self, board, from_position, to_position, color):
        piece = board.get(from_position)
        if piece is None:
            return MoveLegality(False, REASON_NO_PIECE)

        destination_piece = board.get(to_position)
        if destination_piece is not None and destination_piece.color == color:
            return MoveLegality(False, REASON_FRIENDLY_DESTINATION)

        delta_row, delta_col = from_position.delta_to(to_position)
        is_capture = destination_piece is not None
        board_height, _ = board.dimensions()

        if not is_legal_shape(piece.kind, delta_row, delta_col, color, is_capture, from_position.row, board_height):
            return MoveLegality(False, REASON_WRONG_SHAPE)

        if piece.kind in SLIDING_PIECE_TYPES:
            if not is_path_clear(board, from_position, delta_row, delta_col):
                return MoveLegality(False, REASON_PATH_BLOCKED)
        elif piece.kind == PAWN_TYPE and abs(delta_row) == 2:
            if not is_path_clear(board, from_position, delta_row, delta_col):
                return MoveLegality(False, REASON_PATH_BLOCKED)

        return MoveLegality(True)
