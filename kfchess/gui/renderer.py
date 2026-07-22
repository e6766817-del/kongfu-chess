"""Composes BoardView + per-piece animation frames + Clock + the two
SidePanels into one frame (an Img), each frame, for GameLoop to display.
"""

import cv2

from kfchess.input.board_mapper import CELL_SIZE_PX

SELECTION_OUTLINE_COLOR = (0, 255, 255, 255)  # BGRA, yellow
SELECTION_OUTLINE_THICKNESS = 4

MOVE_HIGHLIGHT_COLOR = (0, 200, 0, 255)  # BGRA, green -- empty legal destination
CAPTURE_HIGHLIGHT_COLOR = (0, 0, 220, 255)  # BGRA, red -- legal capture destination
MOVE_HIGHLIGHT_ALPHA = 0.4

GAME_OVER_TEXT = "GAME OVER"
GAME_OVER_DIM_COLOR = (0, 0, 0, 255)  # BGRA, black
GAME_OVER_DIM_ALPHA = 0.55
GAME_OVER_TEXT_COLOR = (255, 255, 255, 255)  # BGRA, white
GAME_OVER_FONT_SCALE = 2.2
GAME_OVER_THICKNESS = 4

COOLDOWN_DIM_COLOR = (0, 0, 0, 255)  # BGRA, black
COOLDOWN_DIM_ALPHA = 0.45
COOLDOWN_TEXT_COLOR = (255, 255, 255, 255)  # BGRA, white
COOLDOWN_FONT_SCALE = 0.9
COOLDOWN_THICKNESS = 2

DISCONNECT_DIM_COLOR = (0, 0, 0, 255)  # BGRA, black
DISCONNECT_DIM_ALPHA = 0.4
DISCONNECT_TEXT_COLOR = (255, 255, 255, 255)  # BGRA, white
DISCONNECT_FONT_SCALE = 0.9
DISCONNECT_THICKNESS = 2


class Renderer:
    def __init__(self, board_view, clock, side_panels, hud_message):
        self._board_view = board_view
        self._clock = clock
        self._side_panels = side_panels
        self._hud_message = hud_message

    def render(
        self, board, animations_by_piece_id, dt_ms, selected_position=None, game_over=False,
        cooldown_remaining_ms_by_position=None, move_destinations=None, capture_destinations=None,
    ):
        """Return one composed Img for this frame."""
        self._clock.tick(dt_ms)
        self._hud_message.tick(dt_ms)

        canvas = self._board_view.new_canvas()

        for position in move_destinations or ():
            self._draw_highlight(canvas, position, MOVE_HIGHLIGHT_COLOR)
        for position in capture_destinations or ():
            self._draw_highlight(canvas, position, CAPTURE_HIGHLIGHT_COLOR)

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

        for position, remaining_ms in (cooldown_remaining_ms_by_position or {}).items():
            self._draw_cooldown_overlay(canvas, position, remaining_ms)

        self._clock.draw(canvas)
        for side_panel in self._side_panels:
            side_panel.draw(canvas)
        self._hud_message.draw(canvas)

        if game_over:
            self.draw_banner(canvas, GAME_OVER_TEXT)

        return canvas

    def _draw_highlight(self, canvas, position, color):
        """Tint `position`'s cell with `color` at MOVE_HIGHLIGHT_ALPHA, so
        a selected piece's reachable cells read at a glance -- green for
        an empty destination, red for a capture."""
        x, y = self._board_view.cell_to_pixel(position)
        overlay_region = canvas.img[y : y + CELL_SIZE_PX, x : x + CELL_SIZE_PX]
        tint_layer = overlay_region.copy()
        tint_layer[:, :] = color[: canvas.img.shape[2]]
        cv2.addWeighted(tint_layer, MOVE_HIGHLIGHT_ALPHA, overlay_region, 1 - MOVE_HIGHLIGHT_ALPHA, 0, overlay_region)

    def _draw_cooldown_overlay(self, canvas, position, remaining_ms):
        """Dim a resting piece's own cell and stamp the seconds left on
        its cooldown, so it reads at a glance as "can't be reselected
        yet" rather than just holding on its last rest-animation frame."""
        if remaining_ms <= 0:
            return
        x, y = self._board_view.cell_to_pixel(position)
        overlay_region = canvas.img[y : y + CELL_SIZE_PX, x : x + CELL_SIZE_PX]
        dim_layer = overlay_region.copy()
        dim_layer[:, :] = COOLDOWN_DIM_COLOR[: canvas.img.shape[2]]
        cv2.addWeighted(dim_layer, COOLDOWN_DIM_ALPHA, overlay_region, 1 - COOLDOWN_DIM_ALPHA, 0, overlay_region)

        seconds_left = (remaining_ms + 99) // 100 / 10  # round up to nearest 0.1s
        text = f"{seconds_left:.1f}"
        (text_w, text_h), _baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, COOLDOWN_FONT_SCALE, COOLDOWN_THICKNESS
        )
        text_x = x + (CELL_SIZE_PX - text_w) // 2
        text_y = y + (CELL_SIZE_PX + text_h) // 2
        cv2.putText(
            canvas.img, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX,
            COOLDOWN_FONT_SCALE, COOLDOWN_TEXT_COLOR, COOLDOWN_THICKNESS, cv2.LINE_AA,
        )

    def draw_banner(self, canvas, text):
        """Dim the whole frame and stamp a big centered label -- used for
        the GAME OVER banner, and callable directly by GameLoop for a
        networked opponent-disconnect message (drawn on the last frame
        once the game loop stops updating)."""
        height, width = canvas.img.shape[:2]
        dim_layer = canvas.img.copy()
        dim_layer[:, :] = GAME_OVER_DIM_COLOR[: canvas.img.shape[2]]
        cv2.addWeighted(dim_layer, GAME_OVER_DIM_ALPHA, canvas.img, 1 - GAME_OVER_DIM_ALPHA, 0, canvas.img)

        (text_w, text_h), _baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, GAME_OVER_FONT_SCALE, GAME_OVER_THICKNESS
        )
        x = (width - text_w) // 2
        y = (height + text_h) // 2
        cv2.putText(
            canvas.img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
            GAME_OVER_FONT_SCALE, GAME_OVER_TEXT_COLOR, GAME_OVER_THICKNESS, cv2.LINE_AA,
        )

    def draw_countdown_banner(self, canvas, seconds_left):
        """Dim the whole frame (lighter than draw_banner's GAME OVER dim,
        since the board is frozen but not over yet) and stamp a centered
        auto-resign countdown -- called every frame while GameLoop is
        frozen waiting out the opponent's disconnect grace period."""
        height, width = canvas.img.shape[:2]
        dim_layer = canvas.img.copy()
        dim_layer[:, :] = DISCONNECT_DIM_COLOR[: canvas.img.shape[2]]
        cv2.addWeighted(dim_layer, DISCONNECT_DIM_ALPHA, canvas.img, 1 - DISCONNECT_DIM_ALPHA, 0, canvas.img)

        text = f"Opponent disconnected. Auto-resigning in {seconds_left:.0f}s..."
        (text_w, text_h), _baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, DISCONNECT_FONT_SCALE, DISCONNECT_THICKNESS
        )
        x = (width - text_w) // 2
        y = (height + text_h) // 2
        cv2.putText(
            canvas.img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
            DISCONNECT_FONT_SCALE, DISCONNECT_TEXT_COLOR, DISCONNECT_THICKNESS, cv2.LINE_AA,
        )
