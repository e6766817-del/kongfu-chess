"""Parses the "Commands:" section of a fixture into token lists.

Ported from the old flat commands.py's parse_commands_section and
command keyword constants.
"""

from kfchess.io.parser import COMMANDS_MARKER
from kfchess.io.stream_reader import read_section

CLICK = "click"
WAIT = "wait"
PRINT = "print"
PRINT_BOARD_TARGET = "board"
JUMP = "jump"


def parse_commands_section(lines):
    command_lines = read_section(lines, COMMANDS_MARKER, None)
    return [line.split() for line in command_lines]
