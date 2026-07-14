"""Composes BoardView + per-piece animation frames + ScoreBoard into one
frame (an Img), each frame, for GameLoop to display.
"""


class Renderer:
    def __init__(self, board_view, sprite_set_cache, scoreboard):
        self._board_view = board_view
        self._sprite_set_cache = sprite_set_cache
        self._scoreboard = scoreboard

    def render(self, board, animations_by_piece_id):
        """Return one composed Img for this frame.

        TODO:
          1. canvas = fresh Img copy of the board background (board_view.draw)
          2. for each piece on `board`, look up its PieceAnimationState from
             animations_by_piece_id, get current_frame(), and
             frame.draw_on(canvas, *board_view.cell_to_pixel(piece.cell))
          3. self._scoreboard.draw(canvas)
          4. return canvas
        """
        raise NotImplementedError
