"""Controller: turns raw clicks (pixels or cells) into selection state
and move/jump requests against GameEngine. Depends only on BoardMapper
and GameEngine -- never on RuleEngine or RealTimeArbiter directly.

Ported from the old flat game_state.py's handle_click selection state
machine (select / same-color reselect-or-ignore-if-locked / attempt
move), which used to live inside the same class as settlement logic.
"""

from kfchess.input import board_mapper as default_board_mapper


class Controller:
    def __init__(self, game_engine, game_state, board_mapper=default_board_mapper):
        self._game_engine = game_engine
        self._game_state = game_state
        self._board_mapper = board_mapper

    def handle_click_at_pixel(self, x, y):
        self.handle_click_at_cell(self._board_mapper.pixel_to_cell(x, y))

    def handle_click_at_cell(self, position):
        if self._game_engine.is_game_over():
            return

        board = self._game_engine.board()
        if not board.is_inside(position):
            return

        clicked_piece = board.get(position)
        selected_position = self._game_state.selected_position

        if selected_position is None:
            if clicked_piece is not None and not self._game_engine.is_locked(position):
                self._game_state.select(position)
            return

        selected_piece = board.get(selected_position)

        if clicked_piece is not None and clicked_piece.color == selected_piece.color:
            if not self._game_engine.is_locked(position):
                self._game_state.select(position)
            return

        result = self._game_engine.request_move(selected_position, position)
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
        self._game_engine.request_jump(position)
