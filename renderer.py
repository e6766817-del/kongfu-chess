"""Formats a Board back into its canonical text form."""


def render(board):
    return "\n".join(" ".join(row) for row in board.rows())
