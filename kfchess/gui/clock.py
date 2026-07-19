"""Elapsed-time HUD, drawn centered in the strip below the board (see
kfchess.gui.config.HUD_HEIGHT_PX). Score, captures, and move history
are per-color concerns and live in SidePanel instead -- the clock is
the one piece of HUD state that belongs to neither side.
"""

from kfchess.gui.config import BOARD_SIZE_PX, BOARD_X_OFFSET_PX, HUD_TOP_PX

CLOCK_COLOR = (255, 255, 255, 255)  # BGRA, white


class Clock:
    def __init__(self):
        self._elapsed_ms = 0

    def tick(self, dt_ms):
        self._elapsed_ms += dt_ms

    def draw(self, canvas):
        board_width, _board_height = BOARD_SIZE_PX
        seconds = self._elapsed_ms // 1000
        text = f"{seconds // 60:02d}:{seconds % 60:02d}"
        x = BOARD_X_OFFSET_PX + board_width // 2 - 30
        canvas.put_text(text, x, HUD_TOP_PX + 30, 0.8, color=CLOCK_COLOR)
