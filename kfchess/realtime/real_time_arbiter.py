"""RealTimeArbiter: the real-time heart of the engine. Advances a
simulated clock, decides when a scheduled move actually arrives, and
performs the arrival update atomically -- until arrival, the logical
board never changes; at arrival, everything happens together (piece
removed from source, placed at destination, any occupant captured,
king capture ending the game).

Ported from the old flat game_state.py's _settle*/_maybe_promote/
_is_move_still_valid/_is_locked family, which used to live inside
GameState alongside click/selection handling. Behavior (including the
jump/ambush mechanic and settlement ordering) is preserved exactly --
only the home of the code changed.
"""

from kfchess.model.piece import KING_TYPE, PAWN_TYPE, QUEEN_TYPE, Piece
from kfchess.realtime.motion import JUMP_DURATION_MS, AirborneJump, PendingMove
from kfchess.rules.piece_rules import pawn_promotion_row, steps

MS_PER_CELL = 1000


def move_duration_ms(delta_row, delta_col):
    return max(1, steps(delta_row, delta_col) - 1) * MS_PER_CELL


class RealTimeArbiter:
    def __init__(self, board, rule_engine):
        self._board = board
        self._rule_engine = rule_engine
        self._clock_ms = 0
        self._pending_moves = []
        self._airborne = []
        self._game_over = False

    def schedule_move(self, from_position, to_position, color, piece_type):
        delta_row, delta_col = from_position.delta_to(to_position)
        arrival_time_ms = self._clock_ms + move_duration_ms(delta_row, delta_col)
        self._pending_moves.append(PendingMove(from_position, to_position, arrival_time_ms, color, piece_type))
        return arrival_time_ms

    def schedule_jump(self, position, color):
        self._airborne.append(AirborneJump(position, color, self._clock_ms + JUMP_DURATION_MS))

    def advance_clock(self, milliseconds):
        self._clock_ms += milliseconds
        self.settle()

    def settle(self):
        self._settle_due_moves()
        self._settle_due_jumps()

    def is_game_over(self):
        return self._game_over

    def is_locked(self, position):
        return self._is_moving(position) or self._is_airborne(position)

    def is_opposite_color_moving(self, color):
        return any(move.color != color for move in self._pending_moves)

    def _settle_due_moves(self):
        still_pending = []
        for move in sorted(self._pending_moves, key=lambda m: m.arrival_time_ms):
            if move.arrival_time_ms > self._clock_ms:
                still_pending.append(move)
                continue
            if not self._is_move_still_valid(move):
                continue

            airborne_jump = self._find_airborne(move.to_position)
            if airborne_jump is not None and airborne_jump.end_time_ms >= move.arrival_time_ms:
                self._board.set(move.from_position, None)
                self._end_airborne(move.to_position)
                if move.piece_type == KING_TYPE:
                    self._game_over = True
                continue

            destination_piece = self._board.get(move.to_position)
            captured_type = destination_piece.kind if destination_piece is not None else None
            self._board.move(move.from_position, move.to_position)
            self._end_airborne(move.to_position)
            if captured_type == KING_TYPE:
                self._game_over = True
            self._maybe_promote(move)
        self._pending_moves = still_pending

    def _settle_due_jumps(self):
        self._airborne = [jump for jump in self._airborne if jump.end_time_ms > self._clock_ms]

    def _maybe_promote(self, move):
        if move.piece_type != PAWN_TYPE:
            return
        board_height, _ = self._board.dimensions()
        if move.to_position.row == pawn_promotion_row(move.color, board_height):
            self._board.set(move.to_position, Piece(move.color, QUEEN_TYPE))

    def _is_move_still_valid(self, move):
        return self._rule_engine.evaluate(self._board, move.from_position, move.to_position, move.color).is_legal

    def _is_moving(self, position):
        return any(move.from_position == position for move in self._pending_moves)

    def _is_airborne(self, position):
        return self._find_airborne(position) is not None

    def _find_airborne(self, position):
        for jump in self._airborne:
            if jump.position == position:
                return jump
        return None

    def _end_airborne(self, position):
        self._airborne = [jump for jump in self._airborne if jump.position != position]
