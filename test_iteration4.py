"""Iteration 4 tests: path blocking for sliding pieces, and captures.

Run: pytest --cov -q
Each parametrized list below is a table of test cases; every row is one
test, with a trailing comment explaining what that row checks.
"""
import io

import pytest

from board import Board
from game_state import GameState
from main_iteration1 import main
from movement_rules import is_legal_move, is_path_clear


@pytest.mark.parametrize("delta_row, delta_col, blocker_offset, expected", [
    (0, 3, None, True),        # straight horizontal, nothing in the way
    (0, 3, (0, 1), False),     # straight horizontal, blocker on the first in-between cell
    (0, 3, (0, 2), False),     # straight horizontal, blocker on the second in-between cell
    (3, 0, (1, 0), False),     # straight vertical, blocker in the way
    (3, 3, (1, 1), False),     # diagonal, blocker in the way
    (0, 1, None, True),        # adjacent cell, nothing can be "in between"
])
def test_is_path_clear(delta_row, delta_col, blocker_offset, expected):
    board = Board([["." for _ in range(4)] for _ in range(4)])
    if blocker_offset:
        board.set(*blocker_offset, "wP")
    assert is_path_clear(board, 0, 0, delta_row, delta_col, ".") == expected


@pytest.mark.parametrize("piece_type, to_cell, expected", [
    ("R", (0, 2), False),  # rook: blocker at (0, 1) sits directly in its path
    ("Q", (0, 2), False),  # queen sliding straight: same blocker still stops it
    ("B", (0, 2), False),  # bishop: that same delta isn't diagonal, so shape rejects it first (blocker irrelevant)
    ("N", (1, 2), True),   # knight: legal L-shape, never path-checked so the blocker at (0, 1) doesn't matter
])
def test_is_legal_move_blocking_depends_on_being_a_sliding_piece(piece_type, to_cell, expected):
    board = Board([[".", "wP", "."], [".", ".", "."]])
    assert is_legal_move(piece_type, board, 0, 0, *to_cell, ".") == expected


def test_is_legal_move_true_on_a_clear_path():
    board = Board([[".", ".", "."]])
    assert is_legal_move("R", board, 0, 0, 0, 2, ".") is True  # nothing in the way


def test_rook_cannot_slide_through_a_blocker():
    state = GameState(Board([["wR", "bP", "."]]))
    state.handle_click(0, 0)
    state.handle_click(0, 2)  # trying to slide past the blocker at (0, 1)
    assert state.board().get(0, 0) == "wR"  # rook never moved
    assert state.board().get(0, 2) == "."   # destination untouched


def test_bishop_cannot_slide_through_a_blocker():
    state = GameState(Board([["wB", ".", "."], [".", "wP", "."], [".", ".", "."]]))
    state.handle_click(0, 0)
    state.handle_click(2, 2)  # diagonal path passes through the blocker at (1, 1)
    assert state.board().get(0, 0) == "wB"
    assert state.board().get(2, 2) == "."


def test_knight_jumps_over_blockers_on_every_side():
    state = GameState(Board([["wN", "bP", "."], ["bP", "bP", "."], [".", ".", "."]]))
    state.handle_click(0, 0)
    state.handle_click(1, 2)  # L-shaped jump straight over the surrounding blockers
    assert state.board().get(1, 2) == "wN"
    assert state.board().get(0, 0) == "."


def test_cannot_capture_own_color_piece_just_reselects():
    state = GameState(Board([["wR", "wQ", "."]]))
    state.handle_click(0, 0)  # select rook
    state.handle_click(0, 1)  # friendly queen: reselects instead of moving/capturing
    assert state.board().get(0, 0) == "wR"  # rook untouched
    assert state.board().get(0, 1) == "wQ"  # queen untouched


def test_can_capture_enemy_piece_at_destination():
    state = GameState(Board([["wR", ".", "bQ"]]))
    state.handle_click(0, 0)  # select rook
    state.handle_click(0, 2)  # clear path, enemy queen sits at the destination
    assert state.board().get(0, 2) == "wR"  # rook captured the enemy queen
    assert state.board().get(0, 0) == "."


@pytest.mark.parametrize("stdin_text, expected_stdout", [
    (
        "Board:\nwR bP .\nCommands:\nclick 50 50\nclick 250 50\nprint board\n",
        "wR bP .\n",
    ),  # end-to-end: enemy pawn blocks the rook's slide, board unchanged
    (
        "Board:\nwR . bQ\nCommands:\nclick 50 50\nclick 250 50\nprint board\n",
        ". . wR\n",
    ),  # end-to-end: clear path lets the rook capture the enemy queen
])
def test_main(stdin_text, expected_stdout, capsys):
    main(io.StringIO(stdin_text))
    assert capsys.readouterr().out == expected_stdout
