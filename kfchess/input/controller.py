"""Controller: turns raw clicks (pixels or cells) into selection state
and move/jump requests against GameEngine. Depends only on BoardMapper
and GameEngine -- never on RuleEngine or RealTimeArbiter directly.

Ported from the old flat game_state.py's handle_click selection state
machine (select / same-color reselect-or-ignore-if-locked / attempt
move), which used to live inside the same class as settlement logic.
"""

from kfchess.input import board_mapper as default_board_mapper


class Controller:
    def __init__(self, game_engine, game_state, board_mapper=default_board_mapper, my_color=None):
        self._game_engine = game_engine
        self._game_state = game_state
        self._board_mapper = board_mapper
        # Restricts selection/jump to pieces of this color -- unset for the
        # single-process local drivers (texttests, single-window GUI) where
        # one operator legitimately controls both colors; set to "w"/"b" by
        # the networked GUI so a client can only ever act on its own side.
        self._my_color = my_color
        # MoveResult (accepted + arrival_time_ms) from the most recent
        # handle_click_at_cell/pixel call, or None if that click wasn't a
        # move attempt. Exists so drivers that need exact arrival timing
        # (the GUI driver, to sync a sliding sprite so it lands exactly
        # when GameEngine actually unlocks the cell) don't have to
        # re-derive it -- texttests ignores this and is unaffected.
        self.last_move_result = None

    def handle_click_at_pixel(self, x, y):
        self.handle_click_at_cell(self._board_mapper.pixel_to_cell(x, y))

    def handle_click_at_cell(self, position):
        self.last_move_result = None
        if self._game_engine.is_game_over():
            return

        board = self._game_engine.board()
        if not board.is_inside(position):
            return

        clicked_piece = board.get(position)
        selected_position = self._game_state.selected_position

        if selected_position is None:
            if (
                clicked_piece is not None
                and not self._game_engine.is_locked(position)
                and self._is_own_piece(clicked_piece)
            ):
                self._game_state.select(position)
            return

        if position == selected_position:
            self._game_state.clear_selection()
            return

        selected_piece = board.get(selected_position)

        if clicked_piece is not None and clicked_piece.color == selected_piece.color:
            if not self._game_engine.is_locked(position):
                self._game_state.select(position)
            return

        result = self._game_engine.request_move(selected_position, position)
        self.last_move_result = result
        if result.accepted:
            self._game_state.clear_selection()

    def handle_jump_at_pixel(self, x, y):
        self.handle_jump_at_cell(self._board_mapper.pixel_to_cell(x, y))

    def handle_jump_at_cell(self, position):
        if self._game_engine.is_game_over():
            return
        board = self._game_engine.board()
        if not board.is_inside(position):
            return
        piece = board.get(position)
        if piece is None or not self._is_own_piece(piece):
            return
        self._game_engine.request_jump(position)

    def _is_own_piece(self, piece):
        return self._my_color is None or piece.color == self._my_color
