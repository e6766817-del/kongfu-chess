"""GameState: the mutable board plus the current click selection --
nothing else. Unlike the old flat game_state.py, this class owns no
clock, no pending moves, no airborne jumps, and no game-over flag --
those all moved up to realtime.RealTimeArbiter and engine.GameEngine,
which is exactly the separation this restructuring is for.
"""


class GameState:
    def __init__(self, board):
        self._board = board
        self._selected_position = None

    @property
    def board(self):
        return self._board

    @property
    def selected_position(self):
        return self._selected_position

    def select(self, position):
        self._selected_position = position

    def clear_selection(self):
        self._selected_position = None
