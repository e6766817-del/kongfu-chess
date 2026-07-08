"""Iteration 8 tests: advanced real-time interaction cases.

A move is re-validated against the live board at arrival time, not just
once when it was requested. This one mechanism covers all three
scenarios below: a same-color piece settling into another's path mid
route, a request that was legal when made but not anymore by the time
it would apply, and two friendly pieces racing to the same cell.

Run: pytest --cov -q
Each parametrized list below is a table of test cases; every row is one
test, with a trailing comment explaining what that row checks.

Note: as with iteration6/7, this file does not modify
test_iteration2/3/4/5/6/7.py.
"""
import io

import pytest

from board import Board
from game_state import GameState
from main_iteration1 import main


def test_slower_piece_is_blocked_by_a_faster_same_color_piece_that_lands_in_its_path():
    state = GameState(Board([
        ["wR", ".", ".", "."],
        [".", ".", ".", "wN"],
    ]))
    state.handle_click(0, 0)
    state.handle_click(0, 3)  # rook: 3-cell move -> 3000ms
    state.handle_click(1, 3)
    state.handle_click(0, 1)  # knight: L-shaped move -> 2000ms, lands squarely on the rook's path

    state.handle_wait(2000)  # knight arrives first and occupies (0, 1)
    assert state.board().get(0, 1) == "wN"

    state.handle_wait(1000)  # rook's original arrival time (3000ms total)
    assert state.board().get(0, 0) == "wR"  # blocked at the last moment -- move cancelled, rook stayed put
    assert state.board().get(0, 3) == "."   # never arrived


def test_cancelled_move_leaves_the_piece_selectable_and_movable_again():
    state = GameState(Board([
        ["wR", ".", ".", "."],
        [".", ".", ".", "wN"],
    ]))
    state.handle_click(0, 0)
    state.handle_click(0, 3)  # will be blocked, same setup as above
    state.handle_click(1, 3)
    state.handle_click(0, 1)
    state.handle_wait(3000)  # knight arrives, then rook's move is cancelled
    assert state.board().get(0, 0) == "wR"  # confirm the cancellation happened

    state.handle_click(0, 0)  # rook is not "moving" anymore -- its pending entry was dropped
    state.handle_click(1, 0)  # a fresh, unrelated move
    state.handle_wait(1000)
    assert state.board().get(1, 0) == "wR"
    assert state.board().get(0, 0) == "."


def test_two_friendly_pieces_racing_to_the_same_cell_the_first_to_arrive_wins():
    state = GameState(Board([
        ["wR", ".", "."],
        [".", ".", "."],
        ["wB", ".", "."],
    ]))
    state.handle_click(0, 0)
    state.handle_click(0, 2)  # rook: 2-cell move -> 2000ms
    state.handle_click(2, 0)
    state.handle_click(0, 2)  # bishop: 2-cell diagonal move -> also 2000ms, same destination

    state.handle_wait(2000)  # both arrive at the same instant; rook was requested first
    assert state.board().get(0, 2) == "wR"   # rook wins the race
    assert state.board().get(2, 0) == "wB"   # bishop's move was cancelled -- it never left
    assert state.board().get(0, 0) == "."


def test_losing_piece_of_the_race_can_be_redirected_afterward():
    state = GameState(Board([
        ["wR", ".", "."],
        [".", ".", "."],
        ["wB", ".", "."],
    ]))
    state.handle_click(0, 0)
    state.handle_click(0, 2)
    state.handle_click(2, 0)
    state.handle_click(0, 2)
    state.handle_wait(2000)  # bishop's move is cancelled, it's still at (2, 0)

    state.handle_click(2, 0)  # bishop is selectable again
    state.handle_click(1, 1)  # a fresh, unobstructed diagonal move
    state.handle_wait(1000)
    assert state.board().get(1, 1) == "wB"


@pytest.mark.parametrize("stdin_text, expected_stdout", [
    (
        "Board:\nwR . .\n. . .\nwB . .\nCommands:\nclick 50 50\nclick 250 50\nclick 50 250\nclick 250 50\nwait 2000\nprint board\n",
        ". . wR\n. . .\nwB . .\n",
    ),  # end-to-end: two friendly pieces target the same cell; the rook (requested first) wins, the bishop's move is cancelled
])
def test_main(stdin_text, expected_stdout, capsys):
    main(io.StringIO(stdin_text))
    assert capsys.readouterr().out == expected_stdout
