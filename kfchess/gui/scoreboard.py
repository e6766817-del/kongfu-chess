"""Captured-piece tally and game clock HUD, drawn via Img.put_text."""

from kfchess.gui.config import BOARD_SIZE_PX


class ScoreBoard:
    def __init__(self):
        self._captured_by_color = {"w": [], "b": []}
        self._elapsed_ms = 0
        self._last_piece_by_id = {}

    def note_captures(self, board):
        """Diff `board` against the last-seen piece set to detect captures.

        A piece id present last frame but absent now was either captured
        (on arrival or mid-path) -- Board.move() carries a piece's id
        forward on a plain move, so a missing id always means it's gone,
        not just relocated.
        """
        current_by_id = {}
        for position in board.all_positions():
            piece = board.get(position)
            if piece is not None:
                current_by_id[piece.id] = piece

        removed_ids = set(self._last_piece_by_id) - set(current_by_id)
        for piece_id in removed_ids:
            removed_piece = self._last_piece_by_id[piece_id]
            self._captured_by_color[removed_piece.color].append(removed_piece.kind)

        self._last_piece_by_id = current_by_id

    def tick(self, dt_ms):
        self._elapsed_ms += dt_ms

    def draw(self, canvas):
        """Render captured-piece tallies + elapsed clock into the HUD
        strip below the board (see BoardView.new_canvas / HUD_HEIGHT_PX)
        -- never over the board itself."""
        _board_width, board_height = BOARD_SIZE_PX
        seconds = self._elapsed_ms // 1000
        clock_text = f"{seconds // 60:02d}:{seconds % 60:02d}"
        white_captures = " ".join(self._captured_by_color["w"]) or "-"
        black_captures = " ".join(self._captured_by_color["b"]) or "-"

        baseline_y = board_height + 38
        canvas.put_text(clock_text, 10, baseline_y, 0.7, color=(255, 255, 255, 255))
        canvas.put_text(f"W: {white_captures}", 110, baseline_y, 0.5, color=(255, 255, 255, 255))
        canvas.put_text(f"B: {black_captures}", 420, baseline_y, 0.5, color=(255, 255, 255, 255))
