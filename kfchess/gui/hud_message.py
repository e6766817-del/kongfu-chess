"""Transient HUD banner explaining why a move/jump request was rejected,
drawn via Img.put_text below the ScoreBoard row (see kfchess.gui.config.
HUD_HEIGHT_PX / kfchess.gui.board_view.BoardView.new_canvas).
"""

from kfchess.gui.config import BOARD_SIZE_PX

DISPLAY_DURATION_MS = 2500

REASON_MESSAGES = {
    "outside_board": "That square is outside the board.",
    "no_piece_at_source": "There's no piece there to move.",
    "destination_occupied_by_own_color": "You already have a piece there.",
    "illegal_shape": "That piece can't move like that.",
    "path_blocked": "Something is blocking that path.",
    "piece_already_locked": "That piece is still moving.",
}


class HudMessage:
    def __init__(self):
        self._text = None
        self._remaining_ms = 0

    def show(self, reason):
        """Display the human-readable message for a rejected MoveResult's
        `reason` string, or the raw reason itself if unrecognized."""
        self._text = REASON_MESSAGES.get(reason, reason)
        self._remaining_ms = DISPLAY_DURATION_MS

    def tick(self, dt_ms):
        if self._remaining_ms <= 0:
            return
        self._remaining_ms -= dt_ms
        if self._remaining_ms <= 0:
            self._text = None

    def draw(self, canvas):
        if self._text is None:
            return
        _board_width, board_height = BOARD_SIZE_PX
        baseline_y = board_height + 72
        canvas.put_text(self._text, 10, baseline_y, 0.55, color=(80, 80, 255, 255))
