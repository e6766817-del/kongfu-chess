"""Iteration 6 tests: moves complete after a delay instead of instantly.

Run: pytest --cov -q
Each parametrized list below is a table of test cases; every row is one
test, with a trailing comment explaining what that row checks.

Note: this file does not modify test_iteration2/3/4/5.py, but those
suites assumed a click-to-move completed the same instant it was
requested. Now every move takes move_duration_ms() to arrive, so their
click-then-assert-moved checks (made with the clock at 0) will fail
against the current code -- that's the expected effect of this
iteration's change, not a bug in this file.
"""
import io

import pytest

from board import Board
from game_state import GameState
from main_iteration1 import main
from movement_rules import move_duration_ms


@pytest.mark.parametrize("delta_row, delta_col, expected_ms", [
    (0, 1, 1000),   # one cell = 1000ms
    (0, 3, 3000),   # three cells in a straight line = 3000ms
    (3, 3, 3000),   # three cells diagonally = 3000ms (Chebyshev distance, not Euclidean)
])
def test_move_duration_ms(delta_row, delta_col, expected_ms):
    assert move_duration_ms(delta_row, delta_col) == expected_ms


def test_board_shows_original_position_immediately_after_a_move_request():
    state = GameState(Board([["wK", ".", "."]]))
    state.handle_click(0, 0)
    state.handle_click(0, 1)  # legal one-cell move, but 1000ms haven't passed
    assert state.board().get(0, 0) == "wK"
    assert state.board().get(0, 1) == "."


def test_board_still_shows_original_position_before_full_duration_elapses():
    state = GameState(Board([["wK", ".", "."]]))
    state.handle_click(0, 0)
    state.handle_click(0, 1)
    state.handle_wait(999)  # one millisecond short of the 1000ms this move needs
    assert state.board().get(0, 0) == "wK"
    assert state.board().get(0, 1) == "."


def test_board_shows_destination_once_duration_fully_elapses():
    state = GameState(Board([["wK", ".", "."]]))
    state.handle_click(0, 0)
    state.handle_click(0, 1)
    state.handle_wait(1000)  # exactly the required duration
    assert state.board().get(0, 1) == "wK"
    assert state.board().get(0, 0) == "."


def test_board_shows_destination_after_more_than_enough_wait():
    state = GameState(Board([["wK", ".", "."]]))
    state.handle_click(0, 0)
    state.handle_click(0, 1)
    state.handle_wait(2500)
    assert state.board().get(0, 1) == "wK"


def test_multiple_waits_accumulate_toward_the_same_arrival_time():
    state = GameState(Board([["wK", ".", "."]]))
    state.handle_click(0, 0)
    state.handle_click(0, 1)
    state.handle_wait(400)
    state.handle_wait(400)
    assert state.board().get(0, 0) == "wK"  # 800ms total, still short of 1000ms
    state.handle_wait(400)
    assert state.board().get(0, 1) == "wK"  # 1200ms total, now arrived


def test_longer_move_takes_proportionally_longer_to_arrive():
    state = GameState(Board([["wR", ".", ".", "."]]))
    state.handle_click(0, 0)
    state.handle_click(0, 3)  # 3-cell rook move -> 3000ms
    state.handle_wait(2999)
    assert state.board().get(0, 0) == "wR"  # not yet arrived
    state.handle_wait(1)
    assert state.board().get(0, 3) == "wR"  # arrived at exactly 3000ms


@pytest.mark.parametrize("stdin_text, expected_stdout", [
    (
        "Board:\nwK . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 150 50\nprint board\n",
        "wK . .\n. . .\n. . .\n",
    ),  # end-to-end: printing right after the move request still shows the original position
    (
        "Board:\nwK . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 150 50\nwait 500\nprint board\n",
        "wK . .\n. . .\n. . .\n",
    ),  # end-to-end: a partial wait (500 of 1000ms) still isn't enough to arrive
    (
        "Board:\nwK . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 150 50\nprint board\nwait 1000\nprint board\n",
        "wK . .\n. . .\n. . .\n. wK .\n. . .\n. . .\n",
    ),  # end-to-end: the first print shows the piece still in flight, the second shows it arrived
])
def test_main(stdin_text, expected_stdout, capsys):
    main(io.StringIO(stdin_text))
    assert capsys.readouterr().out == expected_stdout
