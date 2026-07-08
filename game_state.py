"""GameState: the mutable board, the current click selection, and (as of
iteration6) moves in flight.

handle_click/handle_wait work in board-cell coordinates and game
semantics only -- pixel geometry and command-line parsing are handled
by their own modules before reaching here.
"""

from collections import namedtuple  # iteration6

from pieces_config import EMPTY_TOKEN, KING_TYPE, color_of, is_piece, piece_type_of  # iteration3, iteration9
from movement_rules import is_legal_move, move_duration_ms  # iteration4, iteration6

# iteration6: a move accepted by handle_click doesn't touch the board
# right away -- it's recorded here and only applied once the game
# clock reaches arrival_time. color is tracked (iteration7) so an
# opposite-colored piece can be refused a move while this one is still
# in flight.
PendingMove = namedtuple("PendingMove", ["from_row", "from_col", "to_row", "to_col", "arrival_time", "color"])


class GameState:
    def __init__(self, board):
        self._board = board
        self._selected_cell = None
        self._clock_ms = 0  # iteration6
        self._pending_moves = []  # iteration6
        self._game_over = False  # iteration9

    def board(self):
        self._settle_due_moves()  # iteration6
        return self._board

    def is_game_over(self):  # iteration9
        self._settle_due_moves()
        return self._game_over

    def handle_click(self, row, col):
        self._settle_due_moves()  # iteration6

        if self._game_over:  # iteration9: no further move commands once a king is captured
            return

        if not self._is_inside_board(row, col):
            return

        token = self._board.get(row, col)

        if self._selected_cell is None:
            if is_piece(token) and not self._is_moving(row, col):  # iteration7
                self._selected_cell = (row, col)
            return

        selected_row, selected_col = self._selected_cell
        selected_token = self._board.get(selected_row, selected_col)

        # A same-color piece at the destination always reselects instead
        # of moving, so a piece can never "capture" its own color. #iteration4
        if is_piece(token) and color_of(token) == color_of(selected_token):
            # iteration7: a piece already in flight can't be (re)selected
            # -- it can't be redirected mid-route. It's still a friendly
            # piece occupying that cell though, so the click is simply
            # ignored rather than falling through to a move attempt.
            if not self._is_moving(row, col):
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

    def handle_wait(self, milliseconds):
        self._clock_ms += milliseconds  # iteration6
        self._settle_due_moves()  # iteration6

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
            if self._is_move_still_valid(move):
                # iteration9: capturing a king ends the game -- checked
                # against whatever is actually being captured here, not
                # at request time, since iteration8 may have changed it.
                captured_type = piece_type_of(self._board.get(move.to_row, move.to_col))
                self._board.move(move.from_row, move.from_col, move.to_row, move.to_col, EMPTY_TOKEN)
                if captured_type == KING_TYPE:
                    self._game_over = True
        self._pending_moves = still_pending

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
