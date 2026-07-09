"""Iteration 10 tests: pawn 2-cell start move (with a clear-path
requirement) and promotion to queen on the last row.

A pawn's "start row" is its own home edge -- the fixture places pawns
directly there, there's no separate back rank the way a standard chess
set has one. White's home edge is the last row, black's is row 0.

Run: pytest --cov -q
Each parametrized list below is a table of test cases; every row is one
test, with a trailing comment explaining what that row checks.

Note: as with iteration6/7/8/9, this file does not modify
test_iteration2/3/4/5/6/7/8/9.py.
"""
import io

import pytest

from board import Board
from game_state import GameState
from main_iteration1 import main
from movement_rules import is_legal_shape, pawn_promotion_row, pawn_start_row


@pytest.mark.parametrize("color, board_height, expected", [
    ("w", 5, 4),  # white starts on the last row (its own home edge)
    ("b", 5, 0),  # black starts on row 0 (its own home edge)
])
def test_pawn_start_row(color, board_height, expected):
    assert pawn_start_row(color, board_height) == expected


@pytest.mark.parametrize("color, board_height, expected", [
    ("w", 5, 0),  # white promotes on the opposite edge, row 0
    ("b", 5, 4),  # black promotes on the opposite edge, the last row
])
def test_pawn_promotion_row(color, board_height, expected):
    assert pawn_promotion_row(color, board_height) == expected


@pytest.mark.parametrize("delta_row, from_row, board_height, expected", [
    (-2, 4, 5, True),      # white: two cells forward, from row 4 -- its start row on a 5-row board
    (-2, 3, 5, False),     # white: two cells forward, but not from the start row -- illegal
    (-2, 4, None, False),  # without board_height context (e.g. old call sites), the 2-cell case is conservatively illegal
])
def test_pawn_shape_two_cell_start_move(delta_row, from_row, board_height, expected):
    assert is_legal_shape("P", delta_row, 0, "w", False, from_row, board_height) == expected


def test_two_cell_move_from_start_row_is_legal():
    state = GameState(Board([
        [".", ".", "."],
        [".", ".", "."],
        [".", ".", "."],
        [".", ".", "."],
        [".", "wP", "."],
    ]))
    state.handle_click(4, 1)
    state.handle_click(2, 1)  # 2 cells forward from row 4, white's start row on this 5-row board
    state.handle_wait(2000)
    assert state.board().get(2, 1) == "wP"
    assert state.board().get(4, 1) == "."


def test_two_cell_move_blocked_by_a_piece_in_between_is_illegal():
    state = GameState(Board([
        [".", ".", "."],
        [".", ".", "."],
        [".", ".", "."],
        [".", "bP", "."],
        [".", "wP", "."],
    ]))
    state.handle_click(4, 1)
    state.handle_click(2, 1)  # blocked by the black pawn sitting at (3, 1), the square in between
    state.handle_wait(2000)
    assert state.board().get(4, 1) == "wP"  # never moved
    assert state.board().get(3, 1) == "bP"  # blocker untouched


def test_two_cell_move_is_only_allowed_once_from_the_true_start_row():
    state = GameState(Board([
        [".", ".", "."],
        [".", ".", "."],
        [".", ".", "."],
        [".", ".", "."],
        [".", "wP", "."],
    ]))
    state.handle_click(4, 1)
    state.handle_click(3, 1)  # normal single-cell move first
    state.handle_wait(1000)
    assert state.board().get(3, 1) == "wP"

    state.handle_click(3, 1)
    state.handle_click(1, 1)  # now attempt a 2-cell move from the new position -- not the start row anymore
    state.handle_wait(2000)
    assert state.board().get(3, 1) == "wP"  # still there, the 2-cell attempt was ignored
    assert state.board().get(1, 1) == "."


def test_white_pawn_reaching_the_last_row_becomes_a_queen():
    state = GameState(Board([
        [".", ".", "."],
        [".", "wP", "."],
        [".", ".", "."],
    ]))
    state.handle_click(1, 1)
    state.handle_click(0, 1)  # one cell forward onto the last row
    state.handle_wait(1000)
    assert state.board().get(0, 1) == "wQ"


def test_black_pawn_reaching_the_last_row_becomes_a_queen():
    state = GameState(Board([
        [".", ".", "."],
        [".", "bP", "."],
        [".", ".", "."],
    ]))
    state.handle_click(1, 1)
    state.handle_click(2, 1)  # one cell forward (downward) onto the last row
    state.handle_wait(1000)
    assert state.board().get(2, 1) == "bQ"


def test_promotion_also_applies_when_the_last_row_is_reached_by_a_capture():
    state = GameState(Board([
        [".", "bR", "."],
        [".", ".", "wP"],
        [".", ".", "."],
    ]))
    state.handle_click(1, 2)
    state.handle_click(0, 1)  # diagonal capture of the rook, landing on the last row
    state.handle_wait(1000)
    assert state.board().get(0, 1) == "wQ"  # captured and promoted in the same move
    assert state.board().get(1, 2) == "."


@pytest.mark.parametrize("stdin_text, expected_stdout", [
    (
        "Board:\n. . .\n. . .\n. . .\n. . .\n. wP .\nCommands:\nclick 150 450\nclick 150 250\nwait 2000\nprint board\n",
        ". . .\n. . .\n. wP .\n. . .\n. . .\n",
    ),  # end-to-end: 2-cell start move from white's home edge (row 4 of 5)
    (
        "Board:\n. . .\n. wP .\n. . .\nCommands:\nclick 150 150\nclick 150 50\nwait 1000\nprint board\n",
        ". wQ .\n. . .\n. . .\n",
    ),  # end-to-end: promotion to queen on arrival at the last row
])
def test_main(stdin_text, expected_stdout, capsys):
    main(io.StringIO(stdin_text))
    assert capsys.readouterr().out == expected_stdout
