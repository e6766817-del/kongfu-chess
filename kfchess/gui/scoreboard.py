"""Captured-piece tally and game clock HUD, drawn via Img.put_text."""


class ScoreBoard:
    def __init__(self):
        self._captured_by_color = {"w": [], "b": []}
        self._elapsed_ms = 0

    def note_captures(self, board):
        """Diff `board` against the last-seen piece set to detect captures.

        TODO: compare current Board contents (via board.all_positions()/
        board.get()) against piece ids seen last frame; anything missing
        that wasn't a move destination is a capture -- append its kind to
        self._captured_by_color[color].
        """
        raise NotImplementedError

    def tick(self, dt_ms):
        self._elapsed_ms += dt_ms

    def draw(self, canvas):
        """Render captured-piece tallies + elapsed clock onto `canvas` (an Img)."""
        # TODO: canvas.put_text(...) for each side's captures and the clock.
        raise NotImplementedError
