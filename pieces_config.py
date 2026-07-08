"""Piece/token configuration.

Kept as data (not scattered literals) so a future "user-defined game"
feature can swap or extend COLORS / PIECE_TYPES without touching any
parsing, validation, or rendering code.
"""

COLORS = ("w", "b")
PIECE_TYPES = ("K", "Q", "R", "B", "N", "P")
EMPTY_TOKEN = "."
KING_TYPE = "K"  # iteration9: which piece type ends the game when captured


def build_legal_tokens(colors=COLORS, piece_types=PIECE_TYPES, empty_token=EMPTY_TOKEN):
    tokens = {empty_token}
    tokens.update(color + piece for color in colors for piece in piece_types)
    return frozenset(tokens)


LEGAL_TOKENS = build_legal_tokens()


def is_piece(token):
    return token != EMPTY_TOKEN


def color_of(token):
    return token[0] if is_piece(token) else None


# iteration3
def piece_type_of(token):
    return token[1:] if is_piece(token) else None
