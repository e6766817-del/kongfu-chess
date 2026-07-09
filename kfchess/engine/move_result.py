"""The result of a move/jump request made through GameEngine.

No separate model/move.py object is needed at the public API boundary
-- a move request is just a from/to Position pair -- but the answer to
"did it get accepted, and when will it happen, or why not" is worth a
small named result type instead of a bare tuple.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MoveResult:
    accepted: bool
    reason: str = None
    arrival_time_ms: int = None
