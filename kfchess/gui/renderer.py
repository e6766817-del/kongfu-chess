"""Composes BoardView + per-piece animation frames + Clock + the two
SidePanels into one frame (an Img), each frame, for GameLoop to display.
"""

import cv2

from kfchess.input.board_mapper import CELL_SIZE_PX

SELECTION_OUTLINE_COLOR = (0, 255, 255, 255)  # BGRA, yellow
SELECTION_OUTLINE_THICKNESS = 4

GAME_OVER_TEXT = "GAME OVER"
GAME_OVER_DIM_COLOR = (0, 0, 0, 255)  # BGRA, black
GAME_OVER_DIM_ALPHA = 0.55
GAME_OVER_TEXT_COLOR = (255, 255, 255, 255)  # BGRA, white
GAME_OVER_FONT_SCALE = 2.2
GAME_OVER_THICKNESS = 4


class Renderer:
    def __init__(self, board_view, clock, side_panels, hud_message):
        self._board_view = board_view
        self._clock = clock
        self._side_panels = side_panels
        self._hud_message = hud_message

    def render(self, board, animations_by_piece_id, dt_ms, selected_position=None, game_over=False):
        """Return one composed Img for this frame."""
        self._clock.tick(dt_ms)
        self._hud_message.tick(dt_ms)

        canvas = self._board_view.new_canvas()

        if selected_position is not None:
            x, y = self._board_view.cell_to_pixel(selected_position)
            cv2.rectangle(
                canvas.img,
                (x, y),
                (x + CELL_SIZE_PX - 1, y + CELL_SIZE_PX - 1),
                SELECTION_OUTLINE_COLOR,
                SELECTION_OUTLINE_THICKNESS,
            )

        for position in board.all_positions():
            piece = board.get(position)
            if piece is None:
                continue
            animation = animations_by_piece_id.get(piece.id)
            if animation is None:
                continue
            pixel = animation.current_pixel()
            x, y = pixel if pixel is not None else self._board_view.cell_to_pixel(position)
            animation.current_frame().draw_on(canvas, int(x), int(y))

        self._clock.draw(canvas)
        for side_panel in self._side_panels:
            side_panel.draw(canvas)
        self._hud_message.draw(canvas)

        if game_over:
            self._draw_game_over_banner(canvas)

        return canvas

    def _draw_game_over_banner(self, canvas):
        """Dim the whole frame and stamp a big centered GAME OVER label,
        shown for GameLoop's post-game display window before it closes
        the window."""
        height, width = canvas.img.shape[:2]
        dim_layer = canvas.img.copy()
        dim_layer[:, :] = GAME_OVER_DIM_COLOR[: canvas.img.shape[2]]
        cv2.addWeighted(dim_layer, GAME_OVER_DIM_ALPHA, canvas.img, 1 - GAME_OVER_DIM_ALPHA, 0, canvas.img)

        (text_w, text_h), _baseline = cv2.getTextSize(
            GAME_OVER_TEXT, cv2.FONT_HERSHEY_SIMPLEX, GAME_OVER_FONT_SCALE, GAME_OVER_THICKNESS
        )
        x = (width - text_w) // 2
        y = (height + text_h) // 2
        cv2.putText(
            canvas.img, GAME_OVER_TEXT, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
            GAME_OVER_FONT_SCALE, GAME_OVER_TEXT_COLOR, GAME_OVER_THICKNESS, cv2.LINE_AA,
        )
