"""Exercises the new layered kfchess package (model/rules/realtime/
engine/input/io) end-to-end. The old iteration test files are left
untouched and keep testing the old flat modules -- this file is the
one addition covering the new structure, through GameEngine/Controller
only, mirroring a handful of representative scenarios from the old
suite (basic scheduled arrival, illegal-move rejection with a reason,
king capture ending the game, and jump/ambush) without duplicating
every iteration file.
"""

from kfchess.engine.game_engine import GameEngine
from kfchess.input.controller import Controller
from kfchess.io.validator import build_board
from kfchess.model.game_state import GameState
from kfchess.model.position import Position
from kfchess.rules.rule_engine import REASON_WRONG_SHAPE


def test_move_scheduled_then_arrives():
    board = build_board([["wR", ".", "."]])
    engine = GameEngine(board)

    result = engine.request_move(Position(0, 0), Position(0, 2))
    assert result.accepted is True
    assert result.arrival_time_ms == 2000

    assert engine.board().get(Position(0, 0)) is not None  # not yet moved
    assert engine.board().get(Position(0, 2)) is None

    engine.advance_clock(1000)
    assert engine.board().get(Position(0, 0)) is not None  # still in transit
    assert engine.board().get(Position(0, 2)) is None

    engine.advance_clock(1000)
    assert engine.board().get(Position(0, 0)) is None
    assert engine.board().get(Position(0, 2)).kind == "R"


def test_illegal_move_returns_reason():
    board = build_board([["wR", ".", "."], [".", ".", "."]])
    engine = GameEngine(board)

    result = engine.request_move(Position(0, 0), Position(1, 1))  # rook can't move diagonally
    assert result.accepted is False
    assert result.reason == REASON_WRONG_SHAPE


def test_king_capture_ends_game():
    board = build_board([["wR", ".", "bK"]])
    engine = GameEngine(board)

    result = engine.request_move(Position(0, 0), Position(0, 2))
    assert result.accepted is True

    engine.advance_clock(2000)
    assert engine.is_game_over() is True
    assert engine.board().get(Position(0, 2)).kind == "R"


def test_jump_ambush_destroys_arriving_piece():
    board = build_board([["wN", "bR", "."]])
    engine = GameEngine(board)

    jump_result = engine.request_jump(Position(0, 0))
    assert jump_result.accepted is True

    move_result = engine.request_move(Position(0, 1), Position(0, 0))  # 1-cell move -> arrives at 1000ms
    assert move_result.accepted is True

    engine.advance_clock(1000)
    assert engine.board().get(Position(0, 0)).kind == "N"  # knight intercepted and stayed
    assert engine.board().get(Position(0, 1)) is None  # rook destroyed


def test_controller_click_selection_via_pixel():
    board = build_board([["wR", ".", "."]])
    engine = GameEngine(board)
    game_state = GameState(board)
    controller = Controller(engine, game_state)

    controller.handle_click_at_pixel(50, 50)   # selects (0, 0)
    controller.handle_click_at_pixel(250, 50)  # requests move to (0, 2)

    engine.advance_clock(2000)
    assert engine.board().get(Position(0, 2)).kind == "R"
    assert game_state.selected_position is None
