import json

import pytest

from kfchess.server.accounts import AccountStore
from kfchess.server.game_session import GameSession
from kfchess.server.session import PlayerConnection


class FakeWebSocket:
    def __init__(self):
        self.sent = []

    async def send(self, data):
        self.sent.append(json.loads(data))


@pytest.fixture
def store(tmp_path):
    store = AccountStore(str(tmp_path / "accounts.db"))
    store.login("alice", "pw")
    store.login("bob", "pw")
    return store


def make_connection(username):
    connection = PlayerConnection(websocket=FakeWebSocket())
    connection.username = username
    return connection


@pytest.mark.asyncio
async def test_handle_disconnect_sends_countdown_then_resigns_and_records_result(store):
    white = make_connection("alice")
    black = make_connection("bob")
    session = GameSession(white, black, store, disconnect_resign_seconds=0.05)

    await session.handle_disconnect(white)

    messages = [m["type"] for m in black.websocket.sent]
    assert messages == ["opponent_disconnected", "opponent_resigned"]
    assert black.websocket.sent[0]["resign_in_seconds"] == 0.05

    assert store.get_rating("bob") > 1200
    assert store.get_rating("alice") < 1200


@pytest.mark.asyncio
async def test_handle_disconnect_is_a_no_op_once_session_already_inactive(store):
    white = make_connection("alice")
    black = make_connection("bob")
    session = GameSession(white, black, store, disconnect_resign_seconds=0.01)

    await session.handle_disconnect(white)
    black.websocket.sent.clear()

    await session.handle_disconnect(black)
    assert black.websocket.sent == []
