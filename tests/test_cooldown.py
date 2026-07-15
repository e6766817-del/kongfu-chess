"""Exercises the RESTING lock state added to RealTimeArbiter: a piece
that just arrived from a move (long_rest, scaled by distance traveled)
or just landed a jump (short_rest, flat -- a jump has no distance) must
be genuinely un-selectable/un-movable via GameEngine.is_locked()/
request_move()/request_jump() until its rest duration elapses,
mirroring the scenarios in test_layered_engine.py.
"""

from kfchess.engine.game_engine import REASON_ALREADY_LOCKED, GameEngine
from kfchess.io.validator import build_board
from kfchess.model.position import Position
from kfchess.realtime.motion import JUMP_DURATION_MS, LONG_REST_MS_PER_CELL, SHORT_REST_DURATION_MS
from kfchess.realtime.real_time_arbiter import MS_PER_CELL


def test_move_arrival_starts_long_rest_then_unlocks():
    board = build_board([["wR", ".", "."]])
    engine = GameEngine(board)
    long_rest_ms = 2 * LONG_REST_MS_PER_CELL  # 2-cell move

    engine.request_move(Position(0, 0), Position(0, 2))
    engine.advance_clock(2 * MS_PER_CELL)  # move arrives
    assert engine.board().get(Position(0, 2)).kind == "R"
    assert engine.is_locked(Position(0, 2)) is True

    result = engine.request_move(Position(0, 2), Position(0, 1))
    assert result.accepted is False
    assert result.reason == REASON_ALREADY_LOCKED

    engine.advance_clock(long_rest_ms - 1)
    assert engine.is_locked(Position(0, 2)) is True

    engine.advance_clock(1)
    assert engine.is_locked(Position(0, 2)) is False
    result = engine.request_move(Position(0, 2), Position(0, 1))
    assert result.accepted is True


def test_long_rest_scales_with_distance_traveled():
    board = build_board([["wR", ".", ".", "."]])
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 3))  # 3-cell move
    engine.advance_clock(3 * MS_PER_CELL)  # move arrives
    assert engine.is_locked(Position(0, 3)) is True

    # A 1-cell move's worth of rest isn't enough for a 3-cell move.
    engine.advance_clock(1 * LONG_REST_MS_PER_CELL)
    assert engine.is_locked(Position(0, 3)) is True

    engine.advance_clock(2 * LONG_REST_MS_PER_CELL)
    assert engine.is_locked(Position(0, 3)) is False


def test_jump_landing_starts_short_rest_then_unlocks():
    board = build_board([["wN", "."]])
    engine = GameEngine(board)

    result = engine.request_jump(Position(0, 0))
    assert result.accepted is True
    engine.advance_clock(JUMP_DURATION_MS)  # jump lands
    assert engine.is_locked(Position(0, 0)) is True

    result = engine.request_jump(Position(0, 0))
    assert result.accepted is False
    assert result.reason == REASON_ALREADY_LOCKED

    engine.advance_clock(SHORT_REST_DURATION_MS - 1)
    assert engine.is_locked(Position(0, 0)) is True

    engine.advance_clock(1)
    assert engine.is_locked(Position(0, 0)) is False
    result = engine.request_jump(Position(0, 0))
    assert result.accepted is True


def test_resting_piece_can_still_be_captured_and_capturer_starts_own_rest():
    board = build_board([["wR", ".", "bR"]])
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 1))
    engine.advance_clock(MS_PER_CELL)  # wR arrives at (0, 1), starts long_rest
    assert engine.is_locked(Position(0, 1)) is True

    result = engine.request_move(Position(0, 2), Position(0, 1))
    assert result.accepted is True
    engine.advance_clock(MS_PER_CELL)  # bR captures the resting wR
    assert engine.board().get(Position(0, 1)).color == "b"
    assert engine.is_locked(Position(0, 1)) is True  # capturer now resting

    engine.advance_clock(1 * LONG_REST_MS_PER_CELL)  # capturer's move was also 1 cell
    assert engine.is_locked(Position(0, 1)) is False


def test_ambush_leaves_jumper_resting_not_immediately_idle():
    # bN jumps (airborne until JUMP_DURATION_MS=1000); wR's one-cell move
    # (MS_PER_CELL=667ms) arrives while bN is still airborne, so the mover
    # is destroyed and the jumper survives -- the ambush branch.
    board = build_board([["wR", "bN"]])
    engine = GameEngine(board)

    engine.request_jump(Position(0, 1))
    result = engine.request_move(Position(0, 0), Position(0, 1))
    assert result.accepted is True

    engine.advance_clock(MS_PER_CELL)  # move arrives while bN still airborne
    assert engine.board().get(Position(0, 0)) is None  # mover destroyed
    assert engine.board().get(Position(0, 1)).color == "b"  # jumper survives
    assert engine.is_locked(Position(0, 1)) is True  # jumper resting, not idle

    engine.advance_clock(SHORT_REST_DURATION_MS)
    assert engine.is_locked(Position(0, 1)) is False
