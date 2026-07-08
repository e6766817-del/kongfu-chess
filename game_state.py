"""GameState: the mutable board, the current click selection, and (as of
iteration6) moves in flight.

handle_click/handle_wait work in board-cell coordinates and game
semantics only -- pixel geometry and command-line parsing are handled
by their own modules before reaching here.
"""

from collections import namedtuple  # iteration6

from pieces_config import EMPTY_TOKEN, KING_TYPE, PAWN_TYPE, QUEEN_TYPE, color_of, is_piece, piece_type_of  # iteration3, iteration9, iteration10
from movement_rules import is_legal_move, move_duration_ms, pawn_promotion_row  # iteration4, iteration6, iteration10

# iteration6: a move accepted by handle_click doesn't touch the board
# right away -- it's recorded here and only applied once the game
# clock reaches arrival_time. color is tracked (iteration7) so an
# opposite-colored piece can be refused a move while this one is still
# in flight.
PendingMove = namedtuple("PendingMove", ["from_row", "from_col", "to_row", "to_col", "arrival_time", "color"])

# iteration11: a piece that jumped stays on its own cell but is immune
# to a normal capture for the duration of the jump -- if an enemy move
# arrives at end_time, it's the enemy that's captured instead.
AirborneJump = namedtuple("AirborneJump", ["row", "col", "color", "end_time"])
JUMP_DURATION_MS = 1000


class GameState:
    def __init__(self, board):
        self._board = board
        self._selected_cell = None
        self._clock_ms = 0  # iteration6
        self._pending_moves = []  # iteration6
        self._game_over = False  # iteration9
        self._airborne = []  # iteration11

    def board(self):
        self._settle()  # iteration6, iteration11
        return self._board

    def is_game_over(self):  # iteration9
        self._settle()
        return self._game_over

    def handle_click(self, row, col):
        self._settle()  # iteration6, iteration11

        if self._game_over:  # iteration9: no further move commands once a king is captured
            return

        if not self._is_inside_board(row, col):
            return

        token = self._board.get(row, col)

        if self._selected_cell is None:
            if is_piece(token) and not self._is_locked(row, col):  # iteration7, iteration11
                self._selected_cell = (row, col)
            return

        selected_row, selected_col = self._selected_cell
        selected_token = self._board.get(selected_row, selected_col)

        # A same-color piece at the destination always reselects instead
        # of moving, so a piece can never "capture" its own color. #iteration4
        if is_piece(token) and color_of(token) == color_of(selected_token):
            # iteration7: a piece already in flight can't be (re)selected
            # -- it can't be redirected mid-route. iteration11: same for
            # an airborne piece. It's still a friendly piece occupying
            # that cell though, so the click is simply ignored rather
            # than falling through to a move attempt.
            if not self._is_locked(row, col):
                self._selected_cell = (row, col)
            return

        # iteration3: a move request only executes if it matches the
        # selected piece's movement shape; iteration4: sliding pieces
        # must also have a clear path (destination itself isn't checked,
        # so capturing the enemy piece sitting there is still allowed).
        # An illegal move is ignored, same as any other ignored click
        # (selection stays as-is).
        selected_color = color_of(selected_token)
        # iteration7: opposite-colored pieces can't be in flight at the
        # same time -- if the other color already has a move pending,
        # this move request is ignored (selection stays as-is, so it
        # can be retried once that move settles).
        if self._is_opposite_color_moving(selected_color):
            return

        if is_legal_move(piece_type_of(selected_token), self._board, selected_row, selected_col, row, col, EMPTY_TOKEN, selected_color):  # iteration5: color needed for pawn direction
            # iteration6: schedule the move instead of applying it now.
            # The board keeps showing the piece at its original cell
            # (get()/print board included) until the clock reaches
            # arrival_time.
            delta_row, delta_col = row - selected_row, col - selected_col
            arrival_time = self._clock_ms + move_duration_ms(delta_row, delta_col)
            self._pending_moves.append(PendingMove(selected_row, selected_col, row, col, arrival_time, selected_color))
            self._selected_cell = None

    def handle_jump(self, row, col):
        # iteration11: jump x y -- names the piece directly, no
        # selection step involved.
        self._settle()

        if self._game_over:
            return
        if not self._is_inside_board(row, col):
            return

        token = self._board.get(row, col)
        if not is_piece(token):
            return
        # A moving piece cannot jump, and a piece already airborne can't
        # be sent to jump again until it lands.
        if self._is_locked(row, col):
            return

        self._airborne.append(AirborneJump(row, col, color_of(token), self._clock_ms + JUMP_DURATION_MS))

    def handle_wait(self, milliseconds):
        self._clock_ms += milliseconds  # iteration6
        self._settle()  # iteration6, iteration11

    def _settle(self):
        # iteration11: moves are settled (and can trigger an airborne
        # ambush) before expired jumps are cleared, so a jump ending at
        # the exact same instant an enemy arrives still intercepts it.
        self._settle_due_moves()
        self._settle_due_jumps()

    def _settle_due_moves(self):
        # iteration6: apply every pending move whose arrival time has
        # passed, earliest first (so an earlier arrival is already on
        # the board by the time a later one is checked -- this is what
        # lets two same-color races resolve deterministically below).
        still_pending = []
        for move in sorted(self._pending_moves, key=lambda m: m.arrival_time):
            if move.arrival_time > self._clock_ms:
                still_pending.append(move)
                continue
            # iteration8: re-validate against the board as it is right
            # now, not as it was when the move was requested. Another
            # same-color piece may have settled onto this move's
            # destination or into its path in the meantime. If so, the
            # move is cancelled -- the piece simply stays where it is,
            # same as any other ignored move -- rather than teleporting
            # through/onto whatever is there now.
            if not self._is_move_still_valid(move):
                continue
            # iteration11: compare against the jump's own end_time, not
            # just "is it still in the airborne list right now" -- a
            # single wait() can jump the clock past both a jump's
            # expiry and a later move's arrival in one step, and a jump
            # that had already ended before this move arrived must not
            # intercept it, even though it hasn't been pruned yet.
            airborne_jump = self._find_airborne(move.to_row, move.to_col)
            if airborne_jump is not None and airborne_jump.end_time >= move.arrival_time:
                # The destination is only ever airborne AND non-friendly
                # here (a friendly landing was already cancelled above),
                # so this is always an enemy ambush -- the arriving
                # piece is destroyed, the airborne piece never leaves
                # its cell, and the jump ends immediately.
                arriving_type = piece_type_of(self._board.get(move.from_row, move.from_col))
                self._board.set(move.from_row, move.from_col, EMPTY_TOKEN)
                self._end_airborne(move.to_row, move.to_col)
                if arriving_type == KING_TYPE:
                    self._game_over = True
                continue
            # iteration9: capturing a king ends the game -- checked
            # against whatever is actually being captured here, not
            # at request time, since iteration8 may have changed it.
            captured_type = piece_type_of(self._board.get(move.to_row, move.to_col))
            self._board.move(move.from_row, move.from_col, move.to_row, move.to_col, EMPTY_TOKEN)
            # iteration11: defensive -- clears a stale (already expired
            # but not yet pruned) airborne record on the cell that just
            # changed occupant via an ordinary capture.
            self._end_airborne(move.to_row, move.to_col)
            if captured_type == KING_TYPE:
                self._game_over = True
            self._maybe_promote(move)  # iteration10
        self._pending_moves = still_pending

    def _settle_due_jumps(self):
        # iteration11: a jump that reaches end_time without being
        # ambushed just lands -- the piece never moved, so there's
        # nothing to apply, just drop its airborne status.
        self._airborne = [jump for jump in self._airborne if jump.end_time > self._clock_ms]

    def _maybe_promote(self, move):
        # iteration10: a pawn that reaches the last row becomes a queen.
        moved_token = self._board.get(move.to_row, move.to_col)
        if piece_type_of(moved_token) != PAWN_TYPE:
            return
        board_height, _ = self._board.dimensions()
        if move.to_row == pawn_promotion_row(move.color, board_height):
            self._board.set(move.to_row, move.to_col, move.color + QUEEN_TYPE)

    def _is_move_still_valid(self, move):
        # iteration8
        destination_token = self._board.get(move.to_row, move.to_col)
        if is_piece(destination_token) and color_of(destination_token) == move.color:
            return False
        piece_type = piece_type_of(self._board.get(move.from_row, move.from_col))
        return is_legal_move(piece_type, self._board, move.from_row, move.from_col, move.to_row, move.to_col, EMPTY_TOKEN, move.color)

    def _is_inside_board(self, row, col):
        height, width = self._board.dimensions()
        return 0 <= row < height and 0 <= col < width

    def _is_moving(self, row, col):
        # iteration7: true while some pending move still has this cell
        # as its source. Once a move settles it's removed from
        # _pending_moves, so the piece becomes selectable again with no
        # extra cooldown.
        return any(move.from_row == row and move.from_col == col for move in self._pending_moves)

    def _is_opposite_color_moving(self, color):
        # iteration7: true while any pending move belongs to the other
        # color. Same-color pieces may still move concurrently with
        # each other.
        return any(move.color != color for move in self._pending_moves)

    def _is_airborne(self, row, col):
        # iteration11: true while this cell has a piece mid-jump.
        return self._find_airborne(row, col) is not None

    def _find_airborne(self, row, col):
        # iteration11
        for jump in self._airborne:
            if jump.row == row and jump.col == col:
                return jump
        return None

    def _end_airborne(self, row, col):
        # iteration11: called when an ambush resolves a jump early.
        self._airborne = [jump for jump in self._airborne if not (jump.row == row and jump.col == col)]

    def _is_locked(self, row, col):
        # iteration11: a piece that is moving or airborne can't be
        # selected, moved, or jumped again until it settles/lands.
        return self._is_moving(row, col) or self._is_airborne(row, col)
