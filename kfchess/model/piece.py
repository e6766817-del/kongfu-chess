"""Piece as a real value type, replacing the old flat modules' bare
2-char token strings ("wK", "bP", ...) at the new model boundary.

Config constants mirror kfchess.io.pieces_config deliberately rather
than importing it -- the model layer must not depend on the io layer's
text-token representation (a raw token string is not a Piece).
"""

from dataclasses import dataclass

COLORS = ("w", "b")
PIECE_TYPES = ("K", "Q", "R", "B", "N", "P")
KING_TYPE = "K"
PAWN_TYPE = "P"
QUEEN_TYPE = "Q"


@dataclass(frozen=True)
class Piece:
    color: str
    piece_type: str
