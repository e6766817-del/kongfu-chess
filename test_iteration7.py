"""Iteration 7 tests: a piece can't be redirected mid-move, but can move
again immediately (no cooldown) once it has arrived.

Run: pytest --cov -q
Each parametrized list below is a table of test cases; every row is one
test, with a trailing comment explaining what that row checks.

Note: as with iteration6, this file does not modify
test_iteration2/3/4/5/6.py.
"""
import io

import pytest

from board import Board
from game_state import GameState
from main_iteration1 import main


def test_clicking_a_moving_piece_with_no_selection_does_not_select_it():
    state = GameState(Board([["wK", ".", "."]]))
    state.handle_click(0, 0)  # select
    state.handle_click(0, 1)  # request the move -> now in flight, selection cleared
    state.handle_click(0, 0)  # try to reselect the same piece mid-route
    state.handle_click(0, 2)  # if that reselect had worked, this would redirect it
    state.handle_wait(1000)  # let the original move arrive
    assert state.board().get(0, 1) == "wK"  # arrived at its original destination, not (0, 2)
    assert state.board().get(0, 2) == "."


def test_clicking_a_moving_friendly_piece_while_something_else_is_selected_is_ignored():
    state = GameState(Board([["wK", "wQ", "."]]))
    state.handle_click(0, 1)  # select the queen
    state.handle_click(0, 2)  # queen starts moving toward (0, 2), now in flight
    state.handle_click(0, 0)  # select the king
    state.handle_click(0, 1)  # queen's own cell -- friendly, but it's moving, so this is ignored
    state.handle_wait(1000)  # let the queen's move arrive
    assert state.board().get(0, 0) == "wK"  # king never moved (its move request was ignored)
    assert state.board().get(0, 2) == "wQ"  # queen arrived at its original destination


def test_a_second_piece_can_still_be_selected_while_a_different_piece_is_moving():
    state = GameState(Board([["wK", ".", "wQ"], [".", ".", "."]]))
    state.handle_click(0, 0)  # select king
    state.handle_click(0, 1)  # king starts moving toward (0, 1), now in flight
    state.handle_click(0, 2)  # select the queen -- unrelated piece, not itself moving
    state.handle_click(1, 2)  # queen moves straight down, a cell the king's route never touches
    state.handle_wait(1000)  # both moves were requested at clock 0, so both arrive together
    assert state.board().get(0, 1) == "wK"  # king reached its own destination
    assert state.board().get(1, 2) == "wQ"  # queen reached its own destination, unaffected by the king


def test_piece_can_move_again_immediately_after_arriving_with_no_cooldown():
    state = GameState(Board([["wK", ".", "."], [".", ".", "."]]))
    state.handle_click(0, 0)
    state.handle_click(0, 1)  # first move requested
    state.handle_wait(1000)  # arrives, exactly on time
    state.handle_click(0, 1)  # immediately selectable again -- no cooldown after arriving
    state.handle_click(1, 1)  # second move requested in the very same instant it arrived
    assert state.board().get(0, 1) == "wK"  # second move is in flight, hasn't arrived yet
    state.handle_wait(1000)
    assert state.board().get(1, 1) == "wK"  # second move completed normally
    assert state.board().get(0, 1) == "."   # left the first destination once the second move arrived


def test_redirect_attempt_during_flight_leaves_the_original_route_unaffected():
    state = GameState(Board([["wR", ".", ".", "."]]))
    state.handle_click(0, 0)
    state.handle_click(0, 3)  # 3-cell rook move -> 3000ms, still in flight for a while
    state.handle_wait(1500)  # partway through the route
    state.handle_click(0, 0)  # rook's cell still shows the token, but it's moving -- ignored
    state.handle_click(0, 1)  # attempted redirect target -- also ignored, nothing was selected
    state.handle_wait(1500)  # finish the remaining time
    assert state.board().get(0, 3) == "wR"  # arrived at the original destination
    assert state.board().get(0, 1) == "."   # redirect target was never touched


def test_opposite_color_move_request_is_ignored_while_the_other_color_is_in_flight():
    state = GameState(Board([["wR", ".", "."], [".", ".", "."], ["bR", ".", "."]]))
    state.handle_click(0, 0)  # select white rook
    state.handle_click(0, 2)  # white rook starts moving, in flight until 2000ms
    state.handle_click(2, 0)  # select black rook (selecting is still fine)
    state.handle_click(2, 2)  # black rook's move request is refused -- white is still moving
    state.handle_wait(2000)  # let the white rook's move finish
    assert state.board().get(0, 2) == "wR"  # white rook arrived normally
    assert state.board().get(2, 0) == "bR"  # black rook never moved -- its request was ignored
    assert state.board().get(2, 2) == "."


def test_same_color_pieces_may_move_concurrently():
    state = GameState(Board([["wR", ".", ".", "."], ["wN", ".", ".", "."], [".", ".", ".", "."]]))
    state.handle_click(0, 0)  # select the rook
    state.handle_click(0, 2)  # rook starts a 2-cell move, in flight until 2000ms
    state.handle_click(1, 0)  # select the knight -- same color as the moving rook
    state.handle_click(2, 2)  # knight's L-shaped move (delta 1,2) succeeds despite the rook still being in flight
    state.handle_wait(2000)
    assert state.board().get(0, 2) == "wR"
    assert state.board().get(2, 2) == "wN"


def test_move_request_succeeds_once_the_blocking_color_has_settled():
    state = GameState(Board([["wR", ".", "."], [".", ".", "."], ["bR", ".", "."]]))
    state.handle_click(0, 0)
    state.handle_click(0, 2)  # white rook in flight until 2000ms
    state.handle_click(2, 0)
    state.handle_click(2, 2)  # refused while white is still moving; black rook stays selected
    state.handle_wait(2000)  # white settles
    state.handle_click(2, 2)  # retried with no reselect needed -- succeeds now that white has arrived
    state.handle_wait(2000)
    assert state.board().get(2, 2) == "bR"


@pytest.mark.parametrize("stdin_text, expected_stdout", [
    (
        "Board:\nwK . .\n. . .\nCommands:\nclick 50 50\nclick 150 50\nclick 50 50\nclick 250 50\nwait 1000\nprint board\n",
        ". wK .\n. . .\n",
    ),  # end-to-end: mid-flight reselect+redirect attempt is ignored, piece arrives at its original target
    (
        "Board:\nwK . .\n. . .\nCommands:\nclick 50 50\nclick 150 50\nwait 1000\nclick 150 50\nclick 250 50\nwait 1000\nprint board\n",
        ". . wK\n. . .\n",
    ),  # end-to-end: right after arriving, the piece can be selected and moved again with no cooldown
    (
        "Board:\nwR . .\n. . .\nbR . .\nCommands:\nclick 50 50\nclick 250 50\nclick 50 250\nclick 250 250\nwait 2000\nprint board\n",
        ". . wR\n. . .\nbR . .\n",
    ),  # end-to-end: black's move is refused while white's rook is still in flight, even though the two paths never cross
])
def test_main(stdin_text, expected_stdout, capsys):
    main(io.StringIO(stdin_text))
    assert capsys.readouterr().out == expected_stdout
