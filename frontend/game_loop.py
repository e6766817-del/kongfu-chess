"""Owns the cv2 window, mouse input, and the frame-by-frame tick that
drives GameEngine.advance_clock() and Renderer.render().
"""

WINDOW_NAME = "Kung Fu Chess"
TARGET_FRAME_MS = 16  # ~60 fps


class GameLoop:
    def __init__(self, game_engine, game_state, controller, renderer):
        self._game_engine = game_engine
        self._game_state = game_state
        self._controller = controller
        self._renderer = renderer
        self._animations_by_piece_id = {}

    def run(self):
        """Open the window and run until the user closes it / quits.

        TODO:
          - cv2.namedWindow(WINDOW_NAME)
          - cv2.setMouseCallback(WINDOW_NAME, self._on_mouse) wired to
            controller.handle_click_at_pixel / handle_jump_at_pixel
            (left click = move, right click or a modifier = jump)
          - loop: track dt via time.perf_counter(), call
            game_engine.advance_clock(dt_ms), advance each tracked
            PieceAnimationState, render a frame via self._renderer.render(...),
            display it (cv2.imshow(WINDOW_NAME, frame.img)), cv2.waitKey(1),
            break on a quit key or window close, or game_engine.is_game_over()
          - cv2.destroyAllWindows() on exit
        """
        raise NotImplementedError

    def _on_mouse(self, event, x, y, flags, param):
        """cv2 mouse callback: routes clicks to Controller, and starts a
        PieceAnimationState.start_move/start_jump() when a request is
        accepted (checking MoveResult.accepted from GameEngine)."""
        raise NotImplementedError
