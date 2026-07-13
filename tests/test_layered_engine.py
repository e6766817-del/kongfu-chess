"""Exercises the new layered kfchess package (model/rules/realtime/
engine/input/io) end-to-end. The old iteration test files are left
untouched and keep testing the old flat modules -- this file is the
one addition covering the new structure, through GameEngine/Controller
only, mirroring a handful of representative scenarios from the old
suite (basic scheduled arrival, illegal-move rejection with a reason,
king capture ending the game, and jump/ambush) without duplicating
every iteration file.
"""

from kfchess.engine.game_engine import REASON_ALREADY_LOCKED, GameEngine
from kfchess.input.controller import Controller
from kfchess.io.validator import build_board
from kfchess.model.game_state import GameState
from kfchess.model.position import Position
from kfchess.realtime.real_time_arbiter import RealTimeArbiter
from kfchess.rules.rule_engine import REASON_WRONG_SHAPE, RuleEngine


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


def test_moving_piece_cannot_be_redirected():
    board = build_board([["wR", ".", ".", "."]])
    engine = GameEngine(board)

    first = engine.request_move(Position(0, 0), Position(0, 3))  # 3-cell move -> arrives at 3000ms
    assert first.accepted is True

    engine.advance_clock(1000)  # still in transit
    redirect = engine.request_move(Position(0, 0), Position(0, 1))
    assert redirect.accepted is False
    assert redirect.reason == REASON_ALREADY_LOCKED

    engine.advance_clock(2000)  # original move arrives, unaffected by the rejected redirect
    assert engine.board().get(Position(0, 0)) is None
    assert engine.board().get(Position(0, 3)).kind == "R"


def _empty_row(width=8):
    return ["."] * width


def test_same_color_piece_stops_before_near_collision():
    # wR travels e1->e8 (vertical, column 4); wQ travels a4->h4 (horizontal,
    # row 3) and would cross the rook's path at e4 (row 3, col 4).
    grid = [_empty_row() for _ in range(8)]
    grid[0][4] = "wR"
    grid[3][0] = "wQ"
    board = build_board(grid)
    engine = GameEngine(board)

    queen_result = engine.request_move(Position(3, 0), Position(3, 7))
    assert queen_result.accepted is True

    engine.advance_clock(2000)  # queen is now partway through her own path

    rook_result = engine.request_move(Position(0, 4), Position(7, 4))
    assert rook_result.accepted is True
    assert rook_result.arrival_time_ms == 4000  # truncated: stops at e3, not e8

    engine.advance_clock(2000)  # clock at 4000ms -- rook's truncated move settles
    assert engine.board().get(Position(0, 4)) is None
    assert engine.board().get(Position(2, 4)).kind == "R"  # stopped one cell short (e3)
    assert engine.board().get(Position(3, 4)) is None  # never reached e4
    assert engine.board().get(Position(7, 4)) is None  # never reached its original destination

    engine.advance_clock(3000)  # clock at 7000ms -- queen's own move is unaffected
    assert engine.board().get(Position(3, 0)) is None
    assert engine.board().get(Position(3, 7)).kind == "Q"


def test_opposite_color_mid_path_collision_captures_earlier_piece():
    # bQ travels a4->h4 (row 3) and wR travels e1->e8 (column 4); their
    # paths cross at e4. The rook reaches e4 later than the queen, so the
    # rook captures the queen mid-flight and continues to its own square.
    #
    # GameEngine.request_move currently refuses to schedule a move for
    # either color while the other color already has one in flight
    # (REASON_OPPONENT_MOVING), so two different-colored pieces can never
    # actually be simultaneously in transit through the public API today.
    # This test drives RealTimeArbiter directly to prove the mid-path
    # capture mechanism itself is correct; see the caller for the
    # unresolved policy question this raises.
    grid = [_empty_row() for _ in range(8)]
    grid[0][4] = "wR"
    grid[3][0] = "bQ"
    board = build_board(grid)
    arbiter = RealTimeArbiter(board, RuleEngine())

    queen_arrival = arbiter.schedule_move(Position(3, 0), Position(3, 7), "b", "Q")
    assert queen_arrival == 7000

    arbiter.advance_clock(2000)

    rook_arrival = arbiter.schedule_move(Position(0, 4), Position(7, 4), "w", "R")
    assert rook_arrival == 9000  # rook's own move is unaffected

    arbiter.advance_clock(2000)  # clock at 4000ms -- mid-path capture resolves
    assert board.get(Position(3, 0)) is None  # queen destroyed in transit
    assert board.get(Position(3, 7)) is None  # queen never arrives

    arbiter.advance_clock(5000)  # clock at 9000ms -- rook arrives at its own destination
    assert board.get(Position(0, 4)) is None
    assert board.get(Position(7, 4)).kind == "R"


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
