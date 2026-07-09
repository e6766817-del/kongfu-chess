"""Iteration 11 tests: jumping. A jump lasts 1000ms, the piece never
leaves its cell, and it's immune to capture for that window -- an
enemy move that arrives during the jump is destroyed instead, and the
jump ends immediately. A moving or already-airborne piece can't jump.

Note: move_duration_ms() was corrected here to max(1, steps - 1) * 1000
instead of steps * 1000 (confirmed against VPL: a 2-cell move takes
1000ms, not 2000ms). This changes multi-cell timing for every earlier
iteration too, but test_iteration6/7/8/9/10.py are left untouched per
instructions -- they may no longer pass as a result.

Run: pytest --cov -q
Each parametrized list below is a table of test cases; every row is one
test, with a trailing comment explaining what that row checks.
"""
import io

import pytest

from board import Board
from game_state import GameState
from main_iteration1 import main
from movement_rules import move_duration_ms


@pytest.mark.parametrize("delta_row, delta_col, expected_ms", [
    (0, 1, 1000),  # adjacent move: 1 unit
    (0, 2, 1000),  # 2-cell move: still 1 unit (steps - 1, floored at 1)
    (0, 3, 2000),  # 3-cell move: 2 units
    (2, 1, 1000),  # knight-shaped delta (Chebyshev steps = 2): 1 unit
])
def test_move_duration_ms(delta_row, delta_col, expected_ms):
    assert move_duration_ms(delta_row, delta_col) == expected_ms


def test_jump_locks_the_piece_from_being_selected():
    state = GameState(Board([["wN", "."]]))
    state.handle_jump(0, 0)
    state.handle_click(0, 0)  # try to select the airborne piece
    state.handle_click(0, 1)  # if selection had worked, this would move it
    assert state.board().get(0, 0) == "wN"  # untouched -- selection never happened


def test_no_enemy_arrival_the_piece_just_lands_and_is_usable_again():
    state = GameState(Board([["wR", ".", "."]]))
    state.handle_jump(0, 0)
    state.handle_wait(1000)  # jump window elapses with nothing arriving
    assert state.board().get(0, 0) == "wR"  # unaffected

    state.handle_click(0, 0)  # selectable again, no lock remains
    state.handle_click(0, 2)  # ordinary 2-cell move -> 1000ms
    state.handle_wait(1000)
    assert state.board().get(0, 2) == "wR"


def test_moving_piece_cannot_jump():
    state = GameState(Board([["wR", ".", "."]]))
    state.handle_click(0, 0)
    state.handle_click(0, 2)  # rook starts a 2-cell move, in flight until 1000ms
    state.handle_jump(0, 0)  # attempt to jump it mid-route -- ignored
    state.handle_wait(1000)
    assert state.board().get(0, 2) == "wR"  # original move completed normally


def test_airborne_piece_cannot_jump_again():
    state = GameState(Board([["wR", ".", "."]]))
    state.handle_jump(0, 0)
    state.handle_jump(0, 0)  # already airborne -- second jump request is ignored
    state.handle_wait(1000)  # only one jump was ever scheduled, so it lands right on time
    state.handle_click(0, 0)
    state.handle_click(0, 2)  # 2-cell move -> 1000ms
    state.handle_wait(1000)
    assert state.board().get(0, 2) == "wR"


def test_enemy_still_en_route_when_the_jump_lands_safely():
    state = GameState(Board([["wN", ".", ".", "bR"]]))
    state.handle_jump(0, 0)  # white knight airborne until 1000ms
    state.handle_click(0, 3)  # select the black rook
    state.handle_click(0, 0)  # rook aims at the airborne knight's cell -- a 3-cell move, 2000ms
    state.handle_wait(1000)  # only the jump's own window has elapsed; the rook isn't due until 2000ms
    assert state.board().get(0, 0) == "wN"  # knight landed, unharmed
    assert state.board().get(0, 3) == "bR"  # rook hasn't arrived yet


def test_ambush_when_enemy_arrives_exactly_as_the_jump_ends():
    state = GameState(Board([["wN", "bR", "."]]))
    state.handle_jump(0, 0)  # white knight airborne until 1000ms
    state.handle_click(0, 1)  # select the black rook, adjacent to the knight
    state.handle_click(0, 0)  # rook's 1-cell move -> arrives at 1000ms, exactly when the jump ends
    state.handle_wait(1000)
    assert state.board().get(0, 0) == "wN"  # knight intercepted the rook and stayed put
    assert state.board().get(0, 1) == "."   # rook was destroyed, its origin cell is empty


def test_ambush_also_triggers_when_the_arriving_move_needed_more_time_than_the_jump():
    # Regression test for the exact VPL failure: airborne_piece_captures_arriving_enemy.
    state = GameState(Board([[".", ".", "."], ["wK", ".", "bR"], [".", ".", "."]]))
    state.handle_jump(1, 0)  # white king airborne until 1000ms
    state.handle_click(1, 2)  # select the black rook
    state.handle_click(1, 0)  # rook's 2-cell move -> 1000ms, arrives exactly as the jump ends
    state.handle_wait(1000)
    assert state.board().get(1, 0) == "wK"  # king intercepted the rook and stayed put
    assert state.board().get(1, 2) == "."   # rook was destroyed


def test_jump_requested_after_the_enemy_already_arrived_is_too_late():
    # Regression test for the exact VPL failure: jump_too_late_does_not_save_piece.
    state = GameState(Board([[".", ".", "."], ["wK", ".", "bR"], [".", ".", "."]]))
    state.handle_click(1, 2)  # select the black rook first, before any jump
    state.handle_click(1, 0)  # rook's 2-cell move -> 1000ms
    state.handle_wait(1000)  # the rook arrives and captures the king normally -- no jump was active
    assert state.is_game_over() is True

    state.handle_jump(1, 0)  # too late -- the king is already gone, and the game is already over
    assert state.board().get(1, 0) == "bR"  # the capturing rook is undisturbed


def test_jump_ends_immediately_on_ambush_piece_is_usable_right_away():
    state = GameState(Board([["wN", "bR", "."], [".", ".", "."], [".", ".", "."]]))
    state.handle_jump(0, 0)
    state.handle_click(0, 1)
    state.handle_click(0, 0)  # ambush happens once this rook move arrives, at clock 1000
    state.handle_wait(1000)
    assert state.board().get(0, 0) == "wN"  # confirm the ambush happened

    state.handle_click(0, 0)  # no longer airborne -- selectable right away, no leftover lock
    state.handle_click(2, 1)  # a real knight move (delta 2, 1) -> 1000ms
    state.handle_wait(1000)
    assert state.board().get(2, 1) == "wN"


def test_king_arriving_during_an_ambush_also_ends_the_game():
    state = GameState(Board([["wN", "bK", "."]]))
    state.handle_jump(0, 0)
    state.handle_click(0, 1)
    state.handle_click(0, 0)  # black king walks straight into the airborne knight
    state.handle_wait(1000)
    assert state.board().get(0, 0) == "wN"
    assert state.is_game_over() is True


def test_a_move_arriving_after_the_jump_already_landed_is_a_normal_capture():
    state = GameState(Board([["wN", ".", "bR"]]))
    state.handle_jump(0, 0)
    state.handle_wait(1000)  # jump lands with nothing arriving

    state.handle_click(0, 2)  # now select the rook
    state.handle_click(0, 0)  # rook targets the knight's cell (2-cell move) -- knight is no longer airborne
    state.handle_wait(1000)
    assert state.board().get(0, 0) == "bR"  # ordinary capture, knight is gone


@pytest.mark.parametrize("stdin_text, expected_stdout", [
    (
        "Board:\nwN bR .\nCommands:\njump 50 50\nclick 150 50\nclick 50 50\nwait 1000\nprint board\n",
        "wN . .\n",
    ),  # end-to-end: rook's 1-cell move arrives exactly at the jump's end -- ambushed, rook destroyed
    (
        "Board:\nwR . .\nCommands:\njump 50 50\nwait 1000\nclick 50 50\nclick 250 50\nwait 1000\nprint board\n",
        ". . wR\n",
    ),  # end-to-end: nothing arrives during the jump -- piece lands, then a 2-cell move (1000ms) completes normally
    (
        "Board:\n. . .\nwK . bR\n. . .\nCommands:\njump 50 150\nclick 250 150\nclick 50 150\nwait 1000\nprint board\n",
        ". . .\nwK . .\n. . .\n",
    ),  # end-to-end regression: airborne_piece_captures_arriving_enemy
    (
        "Board:\n. . .\nwK . bR\n. . .\nCommands:\nclick 250 150\nclick 50 150\nwait 1000\njump 50 150\nprint board\n",
        ". . .\nbR . .\n. . .\n",
    ),  # end-to-end regression: jump_too_late_does_not_save_piece
])
def test_main(stdin_text, expected_stdout, capsys):
    main(io.StringIO(stdin_text))
    assert capsys.readouterr().out == expected_stdout
