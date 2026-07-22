import pytest

from kfchess.server.rooms import ROOM_ID_LENGTH, RoomManager
from kfchess.server.session import PlayerConnection


def make_connection(username="alice"):
    connection = PlayerConnection(websocket=None)
    connection.username = username
    return connection


@pytest.mark.asyncio
async def test_create_room_generates_id_and_stores_room():
    manager = RoomManager()
    white = make_connection("alice")

    room = manager.create_room(white)

    assert room.white is white
    assert room.black is None
    assert len(room.room_id) == ROOM_ID_LENGTH
    assert manager.get_room(room.room_id) is room


@pytest.mark.asyncio
async def test_get_room_returns_none_for_unknown_id():
    manager = RoomManager()
    assert manager.get_room("NOPE00") is None


@pytest.mark.asyncio
async def test_create_room_ids_are_unique(monkeypatch):
    manager = RoomManager()
    ids = iter(["AAAAAA", "AAAAAA", "BBBBBB"])
    monkeypatch.setattr("kfchess.server.rooms.random.choices", lambda alphabet, k: list(next(ids)))

    first = manager.create_room(make_connection("alice"))
    second = manager.create_room(make_connection("bob"))

    assert first.room_id == "AAAAAA"
    assert second.room_id == "BBBBBB"
