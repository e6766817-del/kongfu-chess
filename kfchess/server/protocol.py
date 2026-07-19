"""JSON-message builders for the client<->server wire protocol.

These are transient wire messages, not domain objects, so plain
dict-building functions are used instead of a dataclass per message
type. Every message has a "type" field; server->client messages are
built here, client->server messages are just parsed dicts read
directly in game_session.py/server.py (join_queue/move/jump).
"""


def queued():
    return {"type": "queued"}


def match_found(color, board_rows):
    return {"type": "match_found", "color": color, "board": board_rows}


def no_opponent_found():
    return {"type": "no_opponent_found"}


def move_result(accepted, reason=None, arrival_time_ms=None):
    return {
        "type": "move_result",
        "accepted": accepted,
        "reason": reason,
        "arrival_time_ms": arrival_time_ms,
    }


def opponent_move(color, piece_type, from_position, to_position):
    """Sent to the *other* connection the instant a move is accepted (not
    when it settles) -- lets a networked GUI client replay the move into
    its own local GameEngine right away, so it animates the same way a
    locally-clicked move would."""
    return {
        "type": "opponent_move",
        "color": color,
        "piece_type": piece_type,
        "from": [from_position.row, from_position.col],
        "to": [to_position.row, to_position.col],
    }


def opponent_jump(color, piece_type, position):
    return {
        "type": "opponent_jump",
        "color": color,
        "piece_type": piece_type,
        "position": [position.row, position.col],
    }


def move_settled(color, piece_type, from_position, to_position):
    return {
        "type": "move_settled",
        "color": color,
        "piece_type": piece_type,
        "from": [from_position.row, from_position.col],
        "to": [to_position.row, to_position.col],
    }


def piece_captured(color, piece_type):
    return {"type": "piece_captured", "color": color, "piece_type": piece_type}


def game_over():
    return {"type": "game_over"}


def error(message):
    return {"type": "error", "message": message}
