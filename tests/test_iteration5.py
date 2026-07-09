"""Iteration 5 tests: pawn movement and diagonal captures.

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


@pytest.mark.parametrize("color, delta_row, delta_col, is_capture, expected", [
    ("w", -1, 0, False, True),   # white: one step upward onto an empty cell is legal
    ("w", -1, 0, True, False),   # white: cannot capture straight ahead
    ("w", -2, 0, False, False),  # white: cannot move two cells
    ("w", -1, 1, True, True),    # white: diagonal capture is legal
    ("w", -1, 1, False, False),  # white: diagonal move without a capture is illegal
    ("w", 1, 0, False, False),   # white: cannot move backward (downward)
    ("b", 1, 0, False, True),    # black: one step downward onto an empty cell is legal
    ("b", 1, 0, True, False),    # black: cannot capture straight ahead
    ("b", 2, 0, False, False),   # black: cannot move two cells
    ("b", 1, -1, True, True),    # black: diagonal capture is legal
    ("b", 1, -1, False, False),  # black: diagonal move without a capture is illegal
    ("b", -1, 0, False, False),  # black: cannot move backward (upward)
])
def test_pawn_shape(color, delta_row, delta_col, is_capture, expected):
    assert is_legal_shape("P", delta_row, delta_col, color, is_capture) == expected


def test_white_pawn_moves_upward_into_empty_cell():
    state = GameState(Board([[".", ".", "."], [".", ".", "."], [".", "wP", "."]]))
    state.handle_click(2, 1)  # select the white pawn
    state.handle_click(1, 1)  # one cell upward
    assert state.board().get(1, 1) == "wP"
    assert state.board().get(2, 1) == "."


def test_white_pawn_cannot_move_two_cells():
    state = GameState(Board([[".", ".", "."], [".", ".", "."], [".", "wP", "."]]))
    state.handle_click(2, 1)
    state.handle_click(0, 1)  # two cells upward
    assert state.board().get(2, 1) == "wP"  # never moved


def test_white_pawn_captures_diagonally():
    state = GameState(Board([[".", ".", "."], ["bQ", ".", "."], [".", "wP", "."]]))
    state.handle_click(2, 1)  # select white pawn
    state.handle_click(1, 0)  # diagonal capture of the black queen
    assert state.board().get(1, 0) == "wP"
    assert state.board().get(2, 1) == "."


def test_white_pawn_cannot_capture_straight_ahead():
    state = GameState(Board([[".", ".", "."], [".", "bQ", "."], [".", "wP", "."]]))
    state.handle_click(2, 1)
    state.handle_click(1, 1)  # enemy directly in front
    assert state.board().get(2, 1) == "wP"  # never moved
    assert state.board().get(1, 1) == "bQ"  # enemy still there


def test_white_pawn_cannot_move_diagonally_onto_empty_cell():
    state = GameState(Board([[".", ".", "."], [".", ".", "."], [".", "wP", "."]]))
    state.handle_click(2, 1)
    state.handle_click(1, 0)  # diagonal, but nothing to capture
    assert state.board().get(2, 1) == "wP"  # never moved


def test_black_pawn_moves_downward_into_empty_cell():
    state = GameState(Board([[".", "bP", "."], [".", ".", "."], [".", ".", "."]]))
    state.handle_click(0, 1)  # select the black pawn
    state.handle_click(1, 1)  # one cell downward
    assert state.board().get(1, 1) == "bP"
    assert state.board().get(0, 1) == "."


def test_black_pawn_captures_diagonally():
    state = GameState(Board([["bP", ".", "."], [".", "wQ", "."], [".", ".", "."]]))
    state.handle_click(0, 0)  # select black pawn
    state.handle_click(1, 1)  # diagonal capture of the white queen
    assert state.board().get(1, 1) == "bP"
    assert state.board().get(0, 0) == "."


@pytest.mark.parametrize("stdin_text, expected_stdout", [
    (
        "Board:\n. . .\n. . .\n. wP .\nCommands:\nclick 150 250\nclick 150 150\nprint board\n",
        ". . .\n. wP .\n. . .\n",
    ),  # end-to-end: white pawn advances one cell upward
    (
        "Board:\n. . .\nbQ . .\n. wP .\nCommands:\nclick 150 250\nclick 50 150\nprint board\n",
        ". . .\nwP . .\n. . .\n",
    ),  # end-to-end: white pawn captures the black queen diagonally
])
def test_main(stdin_text, expected_stdout, capsys):
    main(io.StringIO(stdin_text))
    assert capsys.readouterr().out == expected_stdout
