import json

import pytest

from kfchess.server.accounts import AccountStore
from kfchess.server.server import _login
from kfchess.server.session import PlayerConnection


class FakeWebSocket:
    def __init__(self, incoming_messages):
        self._incoming = [json.dumps(message) for message in incoming_messages]
        self.sent = []

    async def recv(self):
        return self._incoming.pop(0)

    async def send(self, data):
        self.sent.append(json.loads(data))


@pytest.fixture
def account_store(tmp_path):
    return AccountStore(str(tmp_path / "accounts.db"))


@pytest.mark.asyncio
async def test_new_username_logs_in_at_default_rating(account_store):
    websocket = FakeWebSocket([{"type": "login", "username": "alice", "password": "pw"}])
    connection = PlayerConnection(websocket)
    active_usernames = set()

    ok = await _login(websocket, connection, account_store, active_usernames)

    assert ok is True
    assert connection.username == "alice"
    assert connection.rating == 1200
    assert "alice" in active_usernames
    assert websocket.sent == [{"type": "login_ok", "rating": 1200}]


@pytest.mark.asyncio
async def test_wrong_password_is_rejected(account_store):
    account_store.login("alice", "pw")
    websocket = FakeWebSocket([{"type": "login", "username": "alice", "password": "wrong"}])
    connection = PlayerConnection(websocket)

    ok = await _login(websocket, connection, account_store, set())

    assert ok is False
    assert websocket.sent[0]["type"] == "login_error"


@pytest.mark.asyncio
async def test_duplicate_active_username_is_rejected(account_store):
    websocket = FakeWebSocket([{"type": "login", "username": "alice", "password": "pw"}])
    connection = PlayerConnection(websocket)
    active_usernames = {"alice"}

    ok = await _login(websocket, connection, account_store, active_usernames)

    assert ok is False
    assert websocket.sent[0]["type"] == "login_error"


@pytest.mark.asyncio
async def test_non_login_message_is_rejected(account_store):
    websocket = FakeWebSocket([{"type": "join_queue"}])
    connection = PlayerConnection(websocket)

    ok = await _login(websocket, connection, account_store, set())

    assert ok is False
    assert websocket.sent[0]["type"] == "error"
