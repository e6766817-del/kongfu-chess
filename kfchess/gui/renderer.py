"""Composes BoardView + per-piece animation frames + ScoreBoard into one
frame (an Img), each frame, for GameLoop to display.
"""


class Renderer:
    def __init__(self, board_view, scoreboard):
        self._board_view = board_view
        self._scoreboard = scoreboard

    def render(self, board, animations_by_piece_id, dt_ms):
        """Return one composed Img for this frame."""
        self._scoreboard.tick(dt_ms)
        self._scoreboard.note_captures(board)

        canvas = self._board_view.new_canvas()

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

        self._scoreboard.draw(canvas)
        return canvas
