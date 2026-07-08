"""Iteration 2 tests: click/wait/print board command handling.

Run: pytest --cov -q
Each parametrized list below is a table of test cases; every row is one
test, with a trailing comment explaining what that row checks.
"""
import io

import pytest

from board import Board
from commands import execute_commands, parse_commands_section, pixel_to_cell
from game_state import GameState
from main_iteration1 import main
from pieces_config import color_of, is_piece


@pytest.mark.parametrize("x, y, expected_cell", [
    (50, 50, (0, 0)),  # center of the top-left cell maps to row 0, col 0
    (150, 50, (0, 1)),  # one cell to the right shifts only the column
    (50, 150, (1, 0)),  # one cell down shifts only the row
    (250, 250, (2, 2)),  # arbitrary cell further into the board
])
def test_pixel_to_cell(x, y, expected_cell):
    assert pixel_to_cell(x, y) == expected_cell


@pytest.mark.parametrize("token, expected", [
    ("wK", True),  # a piece token is a piece
    (".", False),  # the empty token is not a piece
])
def test_is_piece(token, expected):
    assert is_piece(token) == expected


@pytest.mark.parametrize("token, expected_color", [
    ("wK", "w"),  # color is the token's first character
    ("bQ", "b"),  # works the same for the other color
    (".", None),  # empty cells have no color
])
def test_color_of(token, expected_color):
    assert color_of(token) == expected_color


def test_board_set_overwrites_a_cell():
    board = Board([["wK", "."]])
    board.set(0, 1, "wQ")
    assert board.get(0, 1) == "wQ"  # set() writes directly into the grid


def test_board_move_relocates_token_and_clears_source():
    board = Board([["wK", "."]])
    board.move(0, 0, 0, 1, ".")
    assert board.get(0, 0) == "."  # source cell becomes empty
    assert board.get(0, 1) == "wK"  # destination cell now holds the moved token


def test_parse_commands_section_splits_each_line_into_tokens():
    lines = ["Board:", "wK", "Commands:", "click 50 50", "wait 100", "print board"]
    assert parse_commands_section(lines) == [["click", "50", "50"], ["wait", "100"], ["print", "board"]]  # each command line is tokenized


def test_click_outside_board_is_ignored():
    state = GameState(Board([["wK", "."], [".", "bK"]]))
    state.handle_click(5, 5)  # row/col out of range
    assert state.board().get(0, 0) == "wK"  # board is untouched


def test_click_empty_cell_with_no_selection_is_ignored():
    state = GameState(Board([["wK", "."], [".", "bK"]]))
    state.handle_click(0, 1)  # empty cell, nothing selected yet
    state.handle_click(1, 1)  # "move" attempt with still nothing selected -> ignored
    assert state.board().get(1, 1) == "bK"  # nothing changed


def test_click_piece_then_empty_cell_moves_it():
    state = GameState(Board([["wK", "."], [".", "bK"]]))
    state.handle_click(0, 0)  # select the white king
    state.handle_click(0, 1)  # move it to the empty cell to its right
    assert state.board().get(0, 1) == "wK"  # move applied
    assert state.board().get(0, 0) == "."  # source cleared


def test_click_second_friendly_piece_replaces_selection_instead_of_moving():
    board = Board([["wK", "wQ"], [".", "."]])
    state = GameState(board)
    state.handle_click(0, 0)  # select wK
    state.handle_click(0, 1)  # wQ is friendly -> replaces selection, no move happens
    state.handle_click(1, 1)  # now moves wQ (the replaced selection), not wK
    assert board.get(1, 1) == "wQ"
    assert board.get(0, 1) == "."  # wQ's original cell cleared
    assert board.get(0, 0) == "wK"  # wK was never moved


def test_click_non_friendly_cell_moves_selected_piece_onto_it():
    board = Board([["wK", "bQ"]])
    state = GameState(board)
    state.handle_click(0, 0)  # select wK
    state.handle_click(0, 1)  # bQ is not friendly -> move request lands on it
    assert board.get(0, 1) == "wK"
    assert board.get(0, 0) == "."


def test_wait_does_not_change_board_or_clear_selection():
    state = GameState(Board([["wK", "."], [".", "."]]))
    state.handle_click(0, 0)  # select wK
    state.handle_wait(500)  # clock advance is a no-op in this iteration
    state.handle_click(1, 0)  # completes the move that was pending before the wait
    assert state.board().get(1, 0) == "wK"  # selection survived the wait untouched


def test_execute_commands_dispatches_click_and_print(capsys):
    state = GameState(Board([["wK", "."], [".", "."]]))
    commands = [["click", "50", "50"], ["click", "150", "50"], ["print", "board"]]
    execute_commands(commands, state, print)
    assert capsys.readouterr().out == ". wK\n. .\n"  # click selects then moves wK one cell right, then prints


@pytest.mark.parametrize("stdin_text, expected_stdout", [
    (
        "Board:\nwK . . bK\n. . . .\nwR . . bR\nCommands:\nclick 50 50\nclick 150 50\nprint board\n",
        ". wK . bK\n. . . .\nwR . . bR\n",
    ),  # end-to-end: select wK, move it one cell right, print settled board
    (
        "Board:\nwK .\n. .\nCommands:\nclick 999 999\nprint board\n",
        "wK .\n. .\n",
    ),  # end-to-end: click outside the board is ignored, board prints unchanged
    (
        "Board:\nwK .\n. .\nCommands:\nwait 250\nprint board\n",
        "wK .\n. .\n",
    ),  # end-to-end: wait alone changes nothing, board still prints
])
def test_main(stdin_text, expected_stdout, capsys):
    main(io.StringIO(stdin_text))
    assert capsys.readouterr().out == expected_stdout
