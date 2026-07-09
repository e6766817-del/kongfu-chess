"""Value objects for moves/jumps in flight -- there's no model/move.py
on the shared path (per the target design), since a move request is
just a from/to Position pair at the public API boundary. These live
here instead, as realtime-only bookkeeping the RealTimeArbiter owns.
"""

from dataclasses import dataclass

from kfchess.model.position import Position

JUMP_DURATION_MS = 1000


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
