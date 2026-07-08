"""Iteration 9 tests: capturing the enemy king ends the game, and later
move commands are ignored afterward.

Run: pytest --cov -q
Each parametrized list below is a table of test cases; every row is one
test, with a trailing comment explaining what that row checks.

Note: as with iteration6/7/8, this file does not modify
test_iteration2/3/4/5/6/7/8.py.
"""
import io

import pytest

from board import Board
from game_state import GameState
from main_iteration1 import main


def test_capturing_the_enemy_king_ends_the_game():
    state = GameState(Board([["wR", ".", "bK"]]))
    assert state.is_game_over() is False
    state.handle_click(0, 0)  # select rook
    state.handle_click(0, 2)  # capture the black king
    state.handle_wait(2000)  # let the 2-cell move arrive
    assert state.board().get(0, 2) == "wR"  # capture happened
    assert state.is_game_over() is True


def test_capturing_a_non_king_piece_does_not_end_the_game():
    state = GameState(Board([["wR", ".", "bQ"]]))
    state.handle_click(0, 0)
    state.handle_click(0, 2)  # capture the black queen, not a king
    state.handle_wait(2000)
    assert state.board().get(0, 2) == "wR"
    assert state.is_game_over() is False


def test_click_commands_after_game_over_are_ignored():
    state = GameState(Board([["wR", ".", "bK"], [".", "bQ", "."]]))
    state.handle_click(0, 0)
    state.handle_click(0, 2)  # capture the king
    state.handle_wait(2000)
    assert state.is_game_over() is True

    state.handle_click(1, 1)  # try to select the black queen -- ignored, game is over
    state.handle_click(0, 2)  # try to move it -- also ignored
    assert state.board().get(1, 1) == "bQ"  # nothing moved after game over
    assert state.board().get(0, 2) == "wR"  # winning rook is undisturbed


def test_selection_active_before_game_over_cannot_be_used_to_move_after():
    state = GameState(Board([["wR", ".", ".", "bK"], [".", "wQ", ".", "."]]))
    state.handle_click(1, 1)  # select the queen before the game ends
    state.handle_click(0, 0)  # select the rook instead (same color, reselects)
    state.handle_click(0, 3)  # capture the king with the rook (queen is off this row, doesn't block)
    state.handle_wait(3000)  # 3-cell move
    assert state.is_game_over() is True

    state.handle_click(1, 1)  # attempt to select the queen now -- ignored
    state.handle_click(1, 2)  # attempt to move it -- ignored
    assert state.board().get(1, 1) == "wQ"  # queen never moved


@pytest.mark.parametrize("stdin_text, expected_stdout", [
    (
        "Board:\nwR . bK\nCommands:\nclick 50 50\nclick 250 50\nwait 2000\nprint board\nclick 250 50\nclick 50 50\nprint board\n",
        ". . wR\n. . wR\n",
    ),  # end-to-end: after the king is captured, a later click command has no effect -- both prints show the same frozen board
])
def test_main(stdin_text, expected_stdout, capsys):
    main(io.StringIO(stdin_text))
    assert capsys.readouterr().out == expected_stdout
