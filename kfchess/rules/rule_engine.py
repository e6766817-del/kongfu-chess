"""RuleEngine: is a requested move legal right now, and if not, why.

Generic orchestration only -- no piece-type-specific logic here. Shape
and path-clearance checks are delegated to piece_rules.
"""

from dataclasses import dataclass

from kfchess.rules.piece_rules import is_legal_shape, is_path_clear

REASON_OUTSIDE_BOARD = "outside_board"
REASON_NO_PIECE = "no_piece_at_source"
REASON_FRIENDLY_DESTINATION = "destination_occupied_by_own_color"
REASON_WRONG_SHAPE = "illegal_shape"
REASON_PATH_BLOCKED = "path_blocked"


@dataclass(frozen=True)
class MoveLegality:
    is_legal: bool
    reason: str = None


class RuleEngine:
    def evaluate(self, board, from_position, to_position, color):
        if not board.is_inside(from_position) or not board.is_inside(to_position):
            return MoveLegality(False, REASON_OUTSIDE_BOARD)

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

        if not is_path_clear(board, piece.kind, from_position, delta_row, delta_col):
            return MoveLegality(False, REASON_PATH_BLOCKED)

        return MoveLegality(True)
