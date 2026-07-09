"""GameEngine: the application-service front door. Coordinates Board,
RuleEngine, and RealTimeArbiter -- it contains no piece-specific
movement logic, no rendering, no input parsing, and no pixel mapping,
matching the target design's boundary for this layer exactly.

Ported from the old flat game_state.py's handle_click validation shell
(the parts that aren't selection state or settlement, which moved to
input.Controller and realtime.RealTimeArbiter respectively).
"""

from kfchess.engine.move_result import MoveResult
from kfchess.realtime.real_time_arbiter import RealTimeArbiter
from kfchess.rules.rule_engine import REASON_NO_PIECE, RuleEngine

REASON_OPPONENT_MOVING = "opponent_piece_moving"
REASON_ALREADY_LOCKED = "piece_already_locked"


class GameEngine:
    def __init__(self, board):
        self._board = board
        self._rule_engine = RuleEngine()
        self._arbiter = RealTimeArbiter(board, self._rule_engine)

    def board(self):
        self._arbiter.settle()
        return self._board

    def is_game_over(self):
        self._arbiter.settle()
        return self._arbiter.is_game_over()

    def is_locked(self, position):
        self._arbiter.settle()
        return self._arbiter.is_locked(position)

    def request_move(self, from_position, to_position):
        self._arbiter.settle()
        if self._arbiter.is_game_over():
            return MoveResult(False, reason=REASON_NO_PIECE)

        piece = self._board.get(from_position)
        if piece is None:
            return MoveResult(False, reason=REASON_NO_PIECE)
        if self._arbiter.is_opposite_color_moving(piece.color):
            return MoveResult(False, reason=REASON_OPPONENT_MOVING)

        legality = self._rule_engine.evaluate(self._board, from_position, to_position, piece.color)
        if not legality.is_legal:
            return MoveResult(False, reason=legality.reason)

        arrival_time_ms = self._arbiter.schedule_move(from_position, to_position, piece.color, piece.piece_type)
        return MoveResult(True, arrival_time_ms=arrival_time_ms)

    def request_jump(self, position):
        self._arbiter.settle()
        if self._arbiter.is_game_over():
            return MoveResult(False, reason=REASON_NO_PIECE)

        piece = self._board.get(position)
        if piece is None:
            return MoveResult(False, reason=REASON_NO_PIECE)
        if self._arbiter.is_locked(position):
            return MoveResult(False, reason=REASON_ALREADY_LOCKED)

        self._arbiter.schedule_jump(position, piece.color)
        return MoveResult(True)

    def advance_clock(self, milliseconds):
        self._arbiter.advance_clock(milliseconds)
