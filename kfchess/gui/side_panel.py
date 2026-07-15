"""One player's own column of HUD state -- score, captured pieces, and
move history -- drawn in the strip beside the board (white's on the
left, black's on the right; see kfchess.gui.config.LEFT_PANEL_X /
RIGHT_PANEL_X).

Wired as an ArbiterObserver (kfchess.realtime.observers) via
GameEngine.add_observer(): each SidePanel only reacts to the events
that belong to its own color, so nothing needs to poll or diff the
board to keep these lists in sync -- a move/capture updates only the
piece involved, not the whole panel.
"""

from kfchess.gui.config import BOARD_SIZE_PX, HUD_HEIGHT_PX
from kfchess.gui.notation import algebraic
from kfchess.model.piece import PIECE_VALUES

PANEL_TEXT_COLOR = (255, 255, 255, 255)  # BGRA, white
HEADER_COLOR = (0, 255, 255, 255)  # BGRA, yellow
PIECE_NAMES = {"K": "K", "Q": "Q", "R": "R", "B": "B", "N": "N", "P": "P"}

HEADER_Y = 30
SCORE_Y = 58
CAPTURES_Y = 80
MOVES_LABEL_Y = 108
MOVES_START_Y = 132
MOVE_LINE_HEIGHT = 22
PANEL_TEXT_X_PAD = 16


class SidePanel:
    def __init__(self, color, panel_x, board_height):
        self._color = color
        self._panel_x = panel_x
        self._board_height = board_height
        self._score = 0
        self._captured = []
        self._moves = []

    # -- ArbiterObserver interface --

    def on_move_settled(self, color, piece_type, from_position, to_position):
        if color != self._color:
            return
        move_number = len(self._moves) + 1
        origin = algebraic(from_position, self._board_height)
        destination = algebraic(to_position, self._board_height)
        self._moves.append(f"{move_number}. {PIECE_NAMES[piece_type]} {origin}-{destination}")

    def on_piece_captured(self, color, piece_type):
        if color == self._color:
            self._captured.append(piece_type)
        else:
            self._score += PIECE_VALUES[piece_type]

    # -- HUD --

    def draw(self, canvas):
        x = self._panel_x + PANEL_TEXT_X_PAD
        canvas.put_text(self._color_label(), x, HEADER_Y, 0.7, color=HEADER_COLOR)
        canvas.put_text(f"Score: {self._score}", x, SCORE_Y, 0.5, color=PANEL_TEXT_COLOR)
        captured_text = " ".join(self._captured) if self._captured else "-"
        canvas.put_text(f"Captured: {captured_text}", x, CAPTURES_Y, 0.5, color=PANEL_TEXT_COLOR)
        canvas.put_text("Moves:", x, MOVES_LABEL_Y, 0.5, color=PANEL_TEXT_COLOR)

        panel_height = BOARD_SIZE_PX[1] + HUD_HEIGHT_PX
        visible_count = max(0, (panel_height - MOVES_START_Y) // MOVE_LINE_HEIGHT)
        for row, line in enumerate(self._moves[-visible_count:]):
            y = MOVES_START_Y + row * MOVE_LINE_HEIGHT
            canvas.put_text(line, x, y, 0.5, color=PANEL_TEXT_COLOR)

    def _color_label(self):
        return "WHITE" if self._color == "w" else "BLACK"
