"""Value objects for moves/jumps in flight -- there's no model/move.py
on the shared path (per the target design), since a move request is
just a from/to Position pair at the public API boundary. These live
here instead, as realtime-only bookkeeping the RealTimeArbiter owns.
"""

from dataclasses import dataclass

from kfchess.model.position import Position

JUMP_DURATION_MS = 1000

# A jump doesn't travel to a different cell (schedule_jump only takes one
# position -- it's an in-place dodge), so short_rest has no distance to
# scale by; it stays a flat per-action cost. Baseline mirrors
# assets/pieces1/*/states/short_rest/config.json's 5 frames @ 8fps, but
# actual per-kind sprite packs don't all agree on frame count (e.g. the
# rook's rest states only have 4 frames) -- the GUI no longer times
# itself off this number, it polls GameEngine.is_locked() instead (see
# kfchess.gui.game_loop.GameLoop._settle_resting_pieces), so this is
# only a real gameplay duration now, not an animation-sync number.
SHORT_REST_DURATION_MS = 625

# A move does travel across cells, so its rest scales with how far the
# piece actually went (same steps() distance move_duration_ms uses) --
# a piece that crossed the whole board pays more cooldown than one that
# shuffled one square. LONG_REST_MS_PER_CELL is the per-cell rate;
# total long rest = steps(delta_row, delta_col) * LONG_REST_MS_PER_CELL,
# see real_time_arbiter.long_rest_duration_ms().
LONG_REST_MS_PER_CELL = 833


@dataclass(frozen=True)
class PendingMove:
    from_position: Position
    to_position: Position
    arrival_time_ms: int
    color: str
    piece_type: str


@dataclass(frozen=True)
class AirborneJump:
    position: Position
    color: str
    end_time_ms: int


@dataclass(frozen=True)
class RestingPiece:
    """A piece that just arrived (long_rest) or just landed a jump
    (short_rest) and can't move/jump again until end_time_ms."""

    position: Position
    color: str
    end_time_ms: int


@dataclass(frozen=True)
class MidPathCapture:
    """A same-cell, opposite-color near-collision detected mid-path (not
    at either move's final destination). `move` is destroyed in transit
    -- removed from the board -- once the clock reaches resolve_time_ms.
    """

    move: PendingMove
    resolve_time_ms: int
