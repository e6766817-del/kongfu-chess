"""Covers path-collision resolution in RealTimeArbiter/piece_rules: same-
color pieces whose paths nearly cross get stopped short, different-color
pieces that cross get the earlier arrival captured, and paths that never
share a cell (or aren't a straight line, e.g. a knight) are unaffected.
"""

from kfchess.io.validator import build_board
from kfchess.model.position import Position
from kfchess.realtime.real_time_arbiter import RealTimeArbiter
from kfchess.rules.piece_rules import line_path_cells
from kfchess.rules.rule_engine import RuleEngine


def _empty_row(width=8):
    return ["."] * width


def _arbiter(grid):
    board = build_board(grid)
    return RealTimeArbiter(board, RuleEngine()), board


def test_line_path_cells_straight_and_diagonal():
    assert line_path_cells(Position(0, 4), Position(3, 4)) == [Position(1, 4), Position(2, 4)]
    assert line_path_cells(Position(0, 0), Position(3, 3)) == [Position(1, 1), Position(2, 2)]


def test_line_path_cells_none_for_non_straight_move():
    assert line_path_cells(Position(0, 0), Position(2, 1)) is None  # knight-shaped delta


def test_paths_that_never_share_a_cell_do_not_collide():
    grid = [_empty_row() for _ in range(8)]
    grid[0][0] = "wR"
    grid[7][7] = "wB"
    arbiter, _ = _arbiter(grid)

    rook_arrival = arbiter.schedule_move(Position(0, 0), Position(0, 3), "w", "R")
    bishop_arrival = arbiter.schedule_move(Position(7, 7), Position(4, 4), "w", "B")

    assert rook_arrival == 3000
    assert bishop_arrival == 3000  # neither move gets truncated


def test_same_color_later_arrival_stops_one_cell_short():
    grid = [_empty_row() for _ in range(8)]
    grid[0][4] = "wR"
    grid[3][0] = "wQ"
    arbiter, _ = _arbiter(grid)

    arbiter.schedule_move(Position(3, 0), Position(3, 7), "w", "Q")  # queen reaches e4 at 4000ms
    arbiter.advance_clock(2000)
    rook_arrival = arbiter.schedule_move(Position(0, 4), Position(7, 4), "w", "R")  # would reach e4 at 5000ms

    assert rook_arrival == 4000  # truncated: stops at e3 instead of e8


def test_opposite_color_earlier_arrival_is_captured_mid_path():
    grid = [_empty_row() for _ in range(8)]
    grid[0][4] = "wR"
    grid[3][0] = "bQ"
    arbiter, board = _arbiter(grid)

    arbiter.schedule_move(Position(3, 0), Position(3, 7), "b", "Q")  # queen reaches e4 at 4000ms
    arbiter.advance_clock(2000)
    rook_arrival = arbiter.schedule_move(Position(0, 4), Position(7, 4), "w", "R")  # reaches e4 at 5000ms

    assert rook_arrival == 9000  # winner's own move is untouched

    arbiter.advance_clock(2000)  # clock at 4000ms -- capture resolves
    assert board.get(Position(3, 0)) is None  # queen destroyed in transit, never arrives
    assert board.get(Position(3, 7)) is None
