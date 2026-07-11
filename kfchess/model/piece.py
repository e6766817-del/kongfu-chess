"""Piece as a real value type, replacing the old flat modules' bare
2-char token strings ("wK", "bP", ...) at the new model boundary.

Config constants mirror kfchess.io.pieces_config deliberately rather
than importing it -- the model layer must not depend on the io layer's
text-token representation (a raw token string is not a Piece).
"""

import itertools
from dataclasses import dataclass, field
from typing import Optional

from kfchess.model.position import Position

COLORS = ("w", "b")
PIECE_TYPES = ("K", "Q", "R", "B", "N", "P")
KING_TYPE = "K"
PAWN_TYPE = "P"
QUEEN_TYPE = "Q"

IDLE_STATE = "idle"
MOVING_STATE = "moving"
CAPTURED_STATE = "captured"
PIECE_STATES = (IDLE_STATE, MOVING_STATE, CAPTURED_STATE)

_id_counter = itertools.count(1)


@dataclass(frozen=True)
class Piece:
    color: str
    kind: str
    id: int = field(default_factory=lambda: next(_id_counter))
    cell: Optional[Position] = None
    state: str = IDLE_STATE
