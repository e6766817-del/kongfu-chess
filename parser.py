"""Parses raw fixture text into a raw token grid.

Pure text extraction only -- no legality/width validation happens here
(see validator.py).
"""

from stream_reader import read_lines, read_section

BOARD_MARKER = "Board:"
COMMANDS_MARKER = "Commands:"


def parse_board_fixture(stream):
    return parse_board_section(read_lines(stream))


def parse_board_section(lines):
    board_lines = read_section(lines, BOARD_MARKER, COMMANDS_MARKER)
    return [line.split() for line in board_lines]
