"""Owns the cv2 window, mouse input, and the frame-by-frame tick that
drives GameEngine.advance_clock() and Renderer.render().

GameEngine.request_move() returns arrival_time_ms, and Controller now
surfaces that MoveResult via .last_move_result (see kfchess.input.
controller) -- this driver uses it to compute exactly how long the
slide from origin to destination should take (arrival_time_ms minus
the engine clock at accept time), so the sprite lands on the
destination cell the same moment GameEngine actually unlocks it. See
kfchess.gui.animation.PieceAnimationState.start_move()/current_pixel().

MOVE settlement (on_settled(), which advances the sprite state past
MOVE once the slide's real-world duration is done) is still detected
reactively by polling GameEngine.is_locked() on the piece's origin cell
each frame, since a move can end early (mid-path capture) or its
target cell can get truncated by a path collision -- see
RealTimeArbiter._resolve_path_collisions -- cases GameEngine exposes no
advance notice of.

SHORT_REST/LONG_REST settlement (on_rest_settled(), see
_settle_resting_pieces()) is polled the same way, on the piece's own
(destination) cell -- these are the real enforced cooldown
(RealTimeArbiter.RESTING), and each piece kind's sprite pack doesn't
necessarily have the same frame count, so the animation can't just
time itself out locally the way JUMP's purely-cosmetic air-time does.
"""

import time

import cv2

from kfchess.gui.animation import LONG_REST, SHORT_REST, PieceAnimationState
from kfchess.gui.config import BOARD_X_OFFSET_PX
from kfchess.input.board_mapper import pixel_to_cell

WINDOW_NAME = "Kung Fu Chess"
QUIT_KEYS = (ord("q"), 27)  # 'q' or Esc
GAME_OVER_DISPLAY_SECONDS = 3.0


class GameLoop:
    def __init__(self, game_engine, game_state, controller, renderer, board_view, sprite_set_cache, hud_message):
        self._game_engine = game_engine
        self._game_state = game_state
        self._controller = controller
        self._renderer = renderer
        self._board_view = board_view
        self._sprite_set_cache = sprite_set_cache
        self._hud_message = hud_message
        self._animations_by_piece_id = {}
        # piece_id -> origin Position, while its MOVE animation waits for arrival
        self._in_flight_moves = {}
        # Mirrors the total milliseconds fed to GameEngine.advance_clock()
        # so far -- the same time base request_move()'s arrival_time_ms is
        # measured against, letting us compute a slide's real duration.
        self._engine_clock_ms = 0

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
                self._engine_clock_ms += dt_ms
                board = self._game_engine.board()

                self._sync_animations(board)
                self._settle_in_flight_moves()
                self._settle_resting_pieces(board)
                for animation in self._animations_by_piece_id.values():
                    animation.advance(dt_ms)

                game_over = self._game_engine.is_game_over()
                cooldown_remaining_ms_by_position = self._cooldown_remaining_ms_by_position(board)
                move_destinations, capture_destinations = self._legal_destinations_by_kind(board)
                frame = self._renderer.render(
                    board, self._animations_by_piece_id, dt_ms, self._game_state.selected_position,
                    game_over=game_over,
                    cooldown_remaining_ms_by_position=cooldown_remaining_ms_by_position,
                    move_destinations=move_destinations,
                    capture_destinations=capture_destinations,
                )
                cv2.imshow(WINDOW_NAME, frame.img)

                key = cv2.waitKey(1) & 0xFF
                if key in QUIT_KEYS:
                    break
                if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                    break
                if game_over:
                    self._hold_game_over_screen()
                    break
        finally:
            cv2.destroyAllWindows()

    def _hold_game_over_screen(self):
        """Keep the last-rendered GAME OVER frame on screen (pumping cv2's
        event loop so the window stays responsive) for
        GAME_OVER_DISPLAY_SECONDS, then let run() close the window."""
        end_time = time.perf_counter() + GAME_OVER_DISPLAY_SECONDS
        while time.perf_counter() < end_time:
            cv2.waitKey(50)
            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                break

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

    def _settle_resting_pieces(self, board):
        """A SHORT_REST/LONG_REST animation holds on its last frame once
        its own frames finish (see PieceAnimationState.advance()) -- it
        only actually advances to idle once GameEngine reports the
        piece's own cell unlocked, i.e. RealTimeArbiter's real cooldown
        elapsed, not just this state's own (per-kind-inconsistent) frame
        count."""
        for position in board.all_positions():
            piece = board.get(position)
            if piece is None:
                continue
            animation = self._animations_by_piece_id.get(piece.id)
            if animation is None or animation.state_name not in (SHORT_REST, LONG_REST):
                continue
            if not self._game_engine.is_locked(position):
                animation.on_rest_settled()

    def _cooldown_remaining_ms_by_position(self, board):
        """Positions of pieces currently in their SHORT_REST/LONG_REST
        animation, mapped to milliseconds left on RealTimeArbiter's real
        cooldown lock -- what Renderer overlays on the cell so a resting
        piece visibly can't be reselected yet."""
        remaining_by_position = {}
        for position in board.all_positions():
            piece = board.get(position)
            if piece is None:
                continue
            animation = self._animations_by_piece_id.get(piece.id)
            if animation is None or animation.state_name not in (SHORT_REST, LONG_REST):
                continue
            remaining_by_position[position] = self._game_engine.locked_remaining_ms(position)
        return remaining_by_position

    def _legal_destinations_by_kind(self, board):
        """(empty_destinations, capture_destinations) for the currently
        selected piece, for Renderer to paint green/red move highlights
        -- empty if nothing is selected."""
        selected_position = self._game_state.selected_position
        if selected_position is None:
            return [], []
        destinations = self._game_engine.legal_destinations(selected_position)
        empty_destinations = [pos for pos in destinations if board.get(pos) is None]
        capture_destinations = [pos for pos in destinations if board.get(pos) is not None]
        return empty_destinations, capture_destinations

    def _on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self._handle_move_click(x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self._handle_jump_click(x, y)

    def _handle_move_click(self, x, y):
        prior_selection = self._game_state.selected_position
        self._controller.handle_click_at_pixel(x, y)

        result = self._controller.last_move_result
        if prior_selection is None or result is None:
            return
        if not result.accepted:
            self._hud_message.show(result.reason)
            return
        piece = self._game_engine.board().get(prior_selection)
        animation = self._animations_by_piece_id.get(piece.id) if piece else None
        if animation is not None:
            origin_px = self._board_view.cell_to_pixel(prior_selection)
            destination_px = self._board_view.cell_to_pixel(pixel_to_cell(x, y, x_offset=BOARD_X_OFFSET_PX))
            duration_ms = result.arrival_time_ms - self._engine_clock_ms
            animation.start_move(origin_px, destination_px, duration_ms)
            self._in_flight_moves[piece.id] = prior_selection

    def _handle_jump_click(self, x, y):
        position = pixel_to_cell(x, y, x_offset=BOARD_X_OFFSET_PX)
        was_locked = self._game_engine.is_locked(position)
        self._controller.handle_jump_at_pixel(x, y)

        jump_was_accepted = not was_locked and self._game_engine.is_locked(position)
        if not jump_was_accepted:
            return
        piece = self._game_engine.board().get(position)
        animation = self._animations_by_piece_id.get(piece.id) if piece else None
        if animation is not None:
            animation.start_jump()
