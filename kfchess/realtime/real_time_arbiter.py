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

from dataclasses import replace

from kfchess.model.piece import KING_TYPE, PAWN_TYPE, QUEEN_TYPE, Piece
from kfchess.realtime.motion import JUMP_DURATION_MS, AirborneJump, MidPathCapture, PendingMove
from kfchess.rules.piece_rules import line_path_cells, pawn_promotion_row, steps

MS_PER_CELL = 1000


def move_duration_ms(delta_row, delta_col):
    return steps(delta_row, delta_col) * MS_PER_CELL


class RealTimeArbiter:
    def __init__(self, board, rule_engine):
        self._board = board
        self._rule_engine = rule_engine
        self._clock_ms = 0
        self._pending_moves = []
        self._airborne = []
        self._mid_path_captures = []
        self._game_over = False

    def schedule_move(self, from_position, to_position, color, piece_type):
        delta_row, delta_col = from_position.delta_to(to_position)
        arrival_time_ms = self._clock_ms + move_duration_ms(delta_row, delta_col)
        move = PendingMove(from_position, to_position, arrival_time_ms, color, piece_type)
        move = self._resolve_path_collisions(move)
        self._pending_moves.append(move)
        return move.arrival_time_ms

    def schedule_jump(self, position, color):
        self._airborne.append(AirborneJump(position, color, self._clock_ms + JUMP_DURATION_MS))

    def advance_clock(self, milliseconds):
        self._clock_ms += milliseconds
        self.settle()

    def settle(self):
        self._settle_due_mid_path_captures()
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

    def _settle_due_mid_path_captures(self):
        still_pending = []
        for capture in self._mid_path_captures:
            if capture.resolve_time_ms > self._clock_ms:
                still_pending.append(capture)
                continue
            if capture.move in self._pending_moves:
                self._pending_moves.remove(capture.move)
                self._board.set(capture.move.from_position, None)
                if capture.move.piece_type == KING_TYPE:
                    self._game_over = True
        self._mid_path_captures = still_pending

    def _interior_path_times(self, move):
        """(cell, entry_time_ms) for each interior cell of move's path, in
        travel order. A piece occupies a cell for the MS_PER_CELL window
        starting at its entry time, matching its constant travel speed.
        """
        cells = line_path_cells(move.from_position, move.to_position)
        if not cells:
            return []
        step_count = len(cells) + 1  # + the final destination step
        start_time_ms = move.arrival_time_ms - step_count * MS_PER_CELL
        return [(cell, start_time_ms + (index + 1) * MS_PER_CELL) for index, cell in enumerate(cells)]

    def _earliest_shared_cell(self, move_a, move_b):
        """The earliest cell + both moves' entry times where move_a and
        move_b would pass through the same cell within one step (MS_PER_CELL)
        of each other -- close enough in time to be a real or "almost"
        collision -- or None if their paths never come that close.
        """
        matches = []
        for cell_a, start_a in self._interior_path_times(move_a):
            for cell_b, start_b in self._interior_path_times(move_b):
                if cell_a != cell_b:
                    continue
                if abs(start_a - start_b) <= MS_PER_CELL:
                    matches.append((min(start_a, start_b), cell_a, start_a, start_b))
        if not matches:
            return None
        matches.sort(key=lambda match: match[0])
        _, cell, start_a, start_b = matches[0]
        return cell, start_a, start_b

    def _resolve_path_collisions(self, new_move):
        for other in list(self._pending_moves):
            shared = self._earliest_shared_cell(new_move, other)
            if shared is None:
                continue
            cell, new_entry_time, other_entry_time = shared
            if new_move.color == other.color:
                if new_entry_time >= other_entry_time:
                    new_move = self._truncate_before(new_move, cell, new_entry_time)
                else:
                    self._replace_pending(other, self._truncate_before(other, cell, other_entry_time))
            else:
                if new_entry_time == other_entry_time:
                    self._mid_path_captures.append(MidPathCapture(other, other_entry_time))
                    self._mid_path_captures.append(MidPathCapture(new_move, new_entry_time))
                elif new_entry_time > other_entry_time:
                    self._mid_path_captures.append(MidPathCapture(other, other_entry_time))
                else:
                    self._mid_path_captures.append(MidPathCapture(new_move, new_entry_time))
        return new_move

    def _truncate_before(self, move, collision_cell, collision_time_ms):
        cells = line_path_cells(move.from_position, move.to_position)
        collision_index = cells.index(collision_cell)
        stop_cell = cells[collision_index - 1] if collision_index > 0 else move.from_position
        stop_time_ms = collision_time_ms - MS_PER_CELL
        if stop_time_ms <= self._clock_ms:
            stop_cell, stop_time_ms = move.from_position, self._clock_ms
        return replace(move, to_position=stop_cell, arrival_time_ms=stop_time_ms)

    def _replace_pending(self, old_move, new_move):
        self._pending_moves = [new_move if move is old_move else move for move in self._pending_moves]

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
