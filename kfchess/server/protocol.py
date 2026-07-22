"""Dataclass definitions for the server->client wire protocol.

Each message is a dataclass, so field names/types are checked by
dataclasses instead of only by convention. `Encoder` (a
json.JSONEncoder) knows how to turn a message dataclass into a plain
dict via dataclasses.asdict, so existing `json.dumps(msg, cls=Encoder)`
calls work unchanged whether msg is one of these or a plain dict.
Client->server messages are still just parsed dicts read directly in
game_session.py/server.py (join_queue/move/jump).
"""

import json
from dataclasses import dataclass, asdict, is_dataclass
from typing import Optional


class Encoder(json.JSONEncoder):
    """`from` is a Python keyword, so OpponentMove/MoveSettled store it as
    `from_` and declare _rename so the wire format still says "from"."""

    def default(self, o):
        if is_dataclass(o):
            d = asdict(o)
            for attr_name, wire_name in getattr(o, "_rename", {}).items():
                d[wire_name] = d.pop(attr_name)
            return d
        return super().default(o)


@dataclass
class LoginOk:
    rating: int
    type: str = "login_ok"


@dataclass
class LoginError:
    message: str
    type: str = "login_error"


@dataclass
class Queued:
    type: str = "queued"


@dataclass
class MatchFound:
    color: str
    board: list
    username: str
    opponent_username: str
    rating: int
    opponent_rating: int
    type: str = "match_found"


@dataclass
class NoOpponentFound:
    type: str = "no_opponent_found"


@dataclass
class MoveResult:
    accepted: bool
    reason: Optional[str] = None
    arrival_time_ms: Optional[int] = None
    type: str = "move_result"


@dataclass
class OpponentMove:
    """Sent to the *other* connection the instant a move is accepted (not
    when it settles) -- lets a networked GUI client replay the move into
    its own local GameEngine right away, so it animates the same way a
    locally-clicked move would."""

    color: str
    piece_type: str
    from_: list
    to: list
    type: str = "opponent_move"
    _rename = {"from_": "from"}


@dataclass
class OpponentJump:
    color: str
    piece_type: str
    position: list
    type: str = "opponent_jump"


@dataclass
class MoveSettled:
    color: str
    piece_type: str
    from_: list
    to: list
    type: str = "move_settled"
    _rename = {"from_": "from"}


@dataclass
class PieceCaptured:
    color: str
    piece_type: str
    type: str = "piece_captured"


@dataclass
class GameOver:
    winner: Optional[str] = None
    type: str = "game_over"


@dataclass
class OpponentDisconnected:
    resign_in_seconds: float
    type: str = "opponent_disconnected"


@dataclass
class OpponentResigned:
    type: str = "opponent_resigned"


@dataclass
class Error:
    message: str
    type: str = "error"


def login_ok(rating):
    return LoginOk(rating=rating)


def login_error(message):
    return LoginError(message=message)


def queued():
    return Queued()


def match_found(color, board_rows, username, opponent_username, rating, opponent_rating):
    return MatchFound(
        color=color, board=board_rows, username=username, opponent_username=opponent_username,
        rating=rating, opponent_rating=opponent_rating,
    )


def no_opponent_found():
    return NoOpponentFound()


def move_result(accepted, reason=None, arrival_time_ms=None):
    return MoveResult(accepted=accepted, reason=reason, arrival_time_ms=arrival_time_ms)


def opponent_move(color, piece_type, from_position, to_position):
    return OpponentMove(
        color=color,
        piece_type=piece_type,
        from_=[from_position.row, from_position.col],
        to=[to_position.row, to_position.col],
    )


def opponent_jump(color, piece_type, position):
    return OpponentJump(color=color, piece_type=piece_type, position=[position.row, position.col])


def move_settled(color, piece_type, from_position, to_position):
    return MoveSettled(
        color=color,
        piece_type=piece_type,
        from_=[from_position.row, from_position.col],
        to=[to_position.row, to_position.col],
    )


def piece_captured(color, piece_type):
    return PieceCaptured(color=color, piece_type=piece_type)


def game_over(winner=None):
    return GameOver(winner=winner)


def opponent_disconnected(resign_in_seconds):
    return OpponentDisconnected(resign_in_seconds=resign_in_seconds)


def opponent_resigned():
    return OpponentResigned()


def error(message):
    return Error(message=message)
