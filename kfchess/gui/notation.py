"""Position -> human algebraic label ("e2", "a8", ...) for move-history
HUD text -- files run a.. left-to-right by column, ranks are counted
from the bottom row up (row 0 is the far rank, so rank number is
board_height - row), matching how a chessboard is conventionally read.
"""


def algebraic(position, board_height):
    file_letter = chr(ord("a") + position.col)
    rank_number = board_height - position.row
    return f"{file_letter}{rank_number}"
