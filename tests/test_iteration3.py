"""Iteration 3 tests: movement-shape legality for K, Q, R, B, N.

Run: pytest --cov -q
Each parametrized list below is a table of test cases; every row is one
test, with a trailing comment explaining what that row checks.
"""
import io

import pytest

from board import Board
from game_state import GameState
from main_iteration1 import main
from movement_rules import is_legal_shape
from pieces_config import piece_type_of


@pytest.mark.parametrize("piece_type, delta_row, delta_col, expected", [
    ("K", 0, 1, True),    # king: one step sideways is legal
    ("K", 1, 1, True),    # king: one step diagonally is legal
    ("K", 0, 2, False),   # king: two cells is illegal
    ("R", 0, 5, True),    # rook: any distance in a straight horizontal line is legal
    ("R", 3, 0, True),    # rook: any distance in a straight vertical line is legal
    ("R", 2, 2, False),   # rook: diagonal is illegal
    ("B", 3, 3, True),    # bishop: any distance diagonally is legal
    ("B", 0, 4, False),   # bishop: a straight line is illegal
    ("Q", 0, 4, True),    # queen: straight line is legal
    ("Q", 4, 4, True),    # queen: diagonal is legal
    ("Q", 2, 1, False),   # queen: neither straight nor diagonal is illegal
    ("N", 1, 2, True),    # knight: L-shape is legal
    ("N", 2, 1, True),    # knight: L-shape (rotated) is legal
    ("N", 1, 1, False),   # knight: one diagonal step is not an L-shape
    ("N", 0, 1, False),   # knight: one straight step is not an L-shape
])
def test_is_legal_shape(piece_type, delta_row, delta_col, expected):
    assert is_legal_shape(piece_type, delta_row, delta_col) == expected


def test_unregistered_piece_type_is_unrestricted():
    assert is_legal_shape("S", 5, 0) is True  # a piece type with no registered rule stays unrestricted


def test_piece_type_of_reads_the_letter_after_color():
    assert piece_type_of("wK") == "K"  # first char is color, the rest is the type
    assert piece_type_of(".") is None  # empty cells have no piece type


@pytest.mark.parametrize("grid, from_cell, to_cell, expected_token_at_to", [
    ([["wK", ".", "."]], (0, 0), (0, 1), "wK"),           # king one step sideways: legal, moves
    ([["wR", ".", ".", "."]], (0, 0), (0, 3), "wR"),      # rook straight line: legal, moves
    ([["wB", ".", "."], [".", ".", "."], [".", ".", "."]], (0, 0), (2, 2), "wB"),  # bishop diagonal: legal, moves
    ([["wN", ".", "."], [".", ".", "."], [".", ".", "."]], (0, 0), (1, 2), "wN"),  # knight L-shape: legal, moves
    ([["wQ", ".", ".", "."]], (0, 0), (0, 3), "wQ"),      # queen straight line: legal, moves
])
def test_legal_move_relocates_the_piece(grid, from_cell, to_cell, expected_token_at_to):
    state = GameState(Board(grid))
    state.handle_click(*from_cell)
    state.handle_click(*to_cell)
    assert state.board().get(*to_cell) == expected_token_at_to
    assert state.board().get(*from_cell) == "."  # source cell cleared


@pytest.mark.parametrize("piece, illegal_to, legal_to", [
    ("wK", (0, 2), (0, 1)),  # king: two cells is illegal, one step is legal
    ("wR", (2, 2), (0, 2)),  # rook: diagonal is illegal, straight line is legal
    ("wB", (0, 2), (2, 2)),  # bishop: straight line is illegal, diagonal is legal
    ("wN", (0, 1), (1, 2)),  # knight: one straight step is illegal, an L-shape is legal
])
def test_illegal_move_is_ignored_and_selection_survives_for_a_later_legal_move(piece, illegal_to, legal_to):
    grid = [[".", ".", "."], [".", ".", "."], [".", ".", "."]]
    grid[0][0] = piece
    state = GameState(Board(grid))
    state.handle_click(0, 0)
    state.handle_click(*illegal_to)
    assert state.board().get(0, 0) == piece  # illegal move ignored, piece never left its cell

    state.handle_click(*legal_to)
    assert state.board().get(*legal_to) == piece  # selection survived the ignored click, so this move succeeds
    assert state.board().get(0, 0) == "."


@pytest.mark.parametrize("stdin_text, expected_stdout", [
    (
        "Board:\nwK . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 250 50\nprint board\n",
        "wK . .\n. . .\n. . .\n",
    ),  # end-to-end: king can't jump two cells, board is unchanged
    (
        "Board:\nwR . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 250 50\nprint board\n",
        ". . wR\n. . .\n. . .\n",
    ),  # end-to-end: rook moves in a straight line across the row
])
def test_main(stdin_text, expected_stdout, capsys):
    main(io.StringIO(stdin_text))
    assert capsys.readouterr().out == expected_stdout
