"""Owns the cv2 window, mouse input, and the frame-by-frame tick that
drives GameEngine.advance_clock() and Renderer.render().

Neither Controller nor GameEngine.request_move()/request_jump() expose
their MoveResult to this driver (Controller swallows it, only using
.accepted internally to clear selection) -- so animation state changes
are detected reactively, by diffing GameState.selected_position and
GameEngine.is_locked() immediately before/after each click, rather than
predicted from a returned arrival_time_ms. See kfchess.gui.animation
for how MOVE settlement (on_settled()) is likewise detected by polling
is_locked() on the piece's origin cell each frame, instead of being
timed against a predicted arrival.
"""

import time

import cv2

from kfchess.gui.animation import PieceAnimationState
from kfchess.input.board_mapper import pixel_to_cell

WINDOW_NAME = "Kung Fu Chess"
QUIT_KEYS = (ord("q"), 27)  # 'q' or Esc


class GameLoop:
    def __init__(self, game_engine, game_state, controller, renderer, sprite_set_cache):
        self._game_engine = game_engine
        self._game_state = game_state
        self._controller = controller
        self._renderer = renderer
        self._sprite_set_cache = sprite_set_cache
        self._animations_by_piece_id = {}
        # piece_id -> origin Position, while its MOVE animation waits for arrival
        self._in_flight_moves = {}

    def run(self):
        cv2.namedWindow(WINDOW_NAME)
        cv2.setMouseCallback(WINDOW_NAME, self._on_mouse)

        last_tick = time.perf_counter()
        try:
            while True:
                now = time.perf_counter()
                dt_ms = max(0, int((now - last_tick) * 1000))
                last_tick = now

                self._game_engine.advance_clock(dt_ms)
                board = self._game_engine.board()

                self._sync_animations(board)
                self._settle_in_flight_moves()
                for animation in self._animations_by_piece_id.values():
                    animation.advance(dt_ms)

                frame = self._renderer.render(board, self._animations_by_piece_id, dt_ms)
                cv2.imshow(WINDOW_NAME, frame.img)

                key = cv2.waitKey(1) & 0xFF
                if key in QUIT_KEYS or self._game_engine.is_game_over():
                    break
                if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                    break
        finally:
            cv2.destroyAllWindows()

    def _sync_animations(self, board):
        """Create a PieceAnimationState (idle) for any newly-seen piece,
        and drop entries for pieces no longer on the board (captured)."""
        current_ids = set()
        for position in board.all_positions():
            piece = board.get(position)
            if piece is None:
                continue
            current_ids.add(piece.id)
            if piece.id not in self._animations_by_piece_id:
                sprite_set = self._sprite_set_cache.get(piece.kind, piece.color)
                self._animations_by_piece_id[piece.id] = PieceAnimationState(sprite_set)

        stale_ids = set(self._animations_by_piece_id) - current_ids
        for piece_id in stale_ids:
            del self._animations_by_piece_id[piece_id]
            self._in_flight_moves.pop(piece_id, None)

    def _settle_in_flight_moves(self):
        """A MOVE animation loops forever on its own -- it only ends once
        GameEngine reports the piece's origin cell is no longer locked
        (arrived, or captured mid-path)."""
        settled_ids = [
            piece_id
            for piece_id, origin in self._in_flight_moves.items()
            if not self._game_engine.is_locked(origin)
        ]
        for piece_id in settled_ids:
            self._in_flight_moves.pop(piece_id)
            animation = self._animations_by_piece_id.get(piece_id)
            if animation is not None:
                animation.on_settled()

    def _on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self._handle_move_click(x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self._handle_jump_click(x, y)

    def _handle_move_click(self, x, y):
        prior_selection = self._game_state.selected_position
        self._controller.handle_click_at_pixel(x, y)

        move_was_accepted = prior_selection is not None and self._game_state.selected_position is None
        if not move_was_accepted:
            return
        piece = self._game_engine.board().get(prior_selection)
        animation = self._animations_by_piece_id.get(piece.id) if piece else None
        if animation is not None:
            animation.start_move()
            self._in_flight_moves[piece.id] = prior_selection

    def _handle_jump_click(self, x, y):
        position = pixel_to_cell(x, y)
        was_locked = self._game_engine.is_locked(position)
        self._controller.handle_jump_at_pixel(x, y)

        jump_was_accepted = not was_locked and self._game_engine.is_locked(position)
        if not jump_was_accepted:
            return
        piece = self._game_engine.board().get(position)
        animation = self._animations_by_piece_id.get(piece.id) if piece else None
        if animation is not None:
            animation.start_jump()
