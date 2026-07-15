"""Observer interface for RealTimeArbiter's per-piece move/capture
instants -- lets HUD-side bookkeeping (score, step counts, ...) react to
the moment a piece actually settles or is captured, instead of polling
or diffing the whole board every frame.
"""

from abc import ABC, abstractmethod


class ArbiterObserver(ABC):
    @abstractmethod
    def on_move_settled(self, color, piece_type, from_position, to_position):
        """A piece of `color` finished travelling and is now resting at
        to_position (a completed "step" for that color)."""

    @abstractmethod
    def on_piece_captured(self, color, piece_type):
        """A piece of `color`/`piece_type` was just removed from the
        board (on arrival, mid-path, or ambushed while airborne)."""
