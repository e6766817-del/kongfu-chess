"""websockets entrypoint: wires one shared MatchmakingQueue to each
incoming connection, following the login handshake and then the
matchmaking flow up to a 60s "no opponent found" timeout, then hands
off to the GameSession's message loop once a match is formed.
"""

import asyncio
import json
import logging

import websockets

from kfchess.server import protocol
from kfchess.server.accounts import AccountStore
from kfchess.server.game_session import GameSession
from kfchess.server.logging_config import setup_logging
from kfchess.server.matchmaking import MatchmakingQueue
from kfchess.server.rooms import RoomManager
from kfchess.server.session import PlayerConnection

logger = logging.getLogger("kfchess.server")

MATCHMAKING_TIMEOUT_SECONDS = 60.0
DEFAULT_ACCOUNTS_DB_PATH = "kfchess_accounts.db"


async def _login(websocket, connection, account_store, active_usernames):
    """Reads the first client message as a login request and validates
    it against account_store -- returns True on success (with
    connection.username/rating set and the username added to
    active_usernames) or False after sending a login_error/error reply
    (the caller should stop handling this connection either way)."""
    login_message = json.loads(await websocket.recv())
    if login_message.get("type") != "login":
        await websocket.send(json.dumps(protocol.error("expected login"), cls=protocol.Encoder))
        return False

    username = login_message.get("username")
    password = login_message.get("password")
    if username in active_usernames:
        await websocket.send(json.dumps(protocol.login_error("already logged in"), cls=protocol.Encoder))
        return False

    result = account_store.login(username, password)
    if not result.ok:
        logger.info("login failed for %s: %s", username, result.reason)
        await websocket.send(json.dumps(protocol.login_error(result.reason), cls=protocol.Encoder))
        return False

    active_usernames.add(username)
    connection.username = username
    connection.rating = result.rating
    logger.info("login ok: %s (rating %s)", username, result.rating)
    await websocket.send(json.dumps(protocol.login_ok(result.rating), cls=protocol.Encoder))
    return True


async def _join_matchmaking(websocket, connection, queue, account_store):
    """Existing anonymous rating-based pairing -- returns the GameSession
    once matched, or None on a no-opponent-found timeout (caller should
    stop handling the connection either way)."""
    await websocket.send(json.dumps(protocol.queued(), cls=protocol.Encoder))

    opponent = await queue.join(connection)
    if opponent is not None:
        session = GameSession(white=opponent, black=connection, account_store=account_store)
        logger.info("matched %s vs %s", opponent.username, connection.username)
        asyncio.create_task(session.run())
        opponent.matched.set_result((connection, session))
        return session

    try:
        _, session = await asyncio.wait_for(connection.matched, timeout=MATCHMAKING_TIMEOUT_SECONDS)
        return session
    except asyncio.TimeoutError:
        await queue.cancel_waiting(connection)
        await websocket.send(json.dumps(protocol.no_opponent_found(), cls=protocol.Encoder))
        return None


async def _create_room(websocket, connection, room_manager):
    """The creator (White) waits here until a second player joins the
    room and starts the GameSession -- see kfchess.server.rooms."""
    room = room_manager.create_room(connection)
    logger.info("room %s created by %s", room.room_id, connection.username)
    await websocket.send(json.dumps(protocol.room_created(room.room_id), cls=protocol.Encoder))
    return await room.matched


async def _join_room(websocket, connection, room_manager, account_store, room_id):
    """Second joiner becomes Black and starts the game; every later
    joiner is a read-only viewer (added immediately if the game has
    already started, or queued as a pending viewer otherwise)."""
    room = room_manager.get_room(room_id)
    if room is None:
        logger.info("%s tried to join unknown room %s", connection.username, room_id)
        await websocket.send(json.dumps(protocol.error("room not found"), cls=protocol.Encoder))
        return None

    if room.black is None:
        room.black = connection
        session = GameSession(
            white=room.white, black=connection, account_store=account_store, viewers=room.pending_viewers,
        )
        logger.info("room %s: %s joined as black, starting game", room.room_id, connection.username)
        asyncio.create_task(session.run())
        room.game_session = session
        room.matched.set_result(session)
        return session

    logger.info("room %s: %s joined as viewer", room.room_id, connection.username)
    if room.game_session is not None:
        await room.game_session.add_viewer(connection)
        return room.game_session
    room.pending_viewers.append(connection)
    return await room.matched


async def handle_connection(websocket, queue, account_store, active_usernames, room_manager):
    connection = PlayerConnection(websocket)

    if not await _login(websocket, connection, account_store, active_usernames):
        return

    try:
        join_message = json.loads(await websocket.recv())
        message_type = join_message.get("type")
        if message_type == "join_queue":
            session = await _join_matchmaking(websocket, connection, queue, account_store)
        elif message_type == "create_room":
            session = await _create_room(websocket, connection, room_manager)
        elif message_type == "join_room":
            session = await _join_room(websocket, connection, room_manager, account_store, join_message.get("room_id"))
        else:
            await websocket.send(json.dumps(protocol.error("expected join_queue, create_room, or join_room"), cls=protocol.Encoder))
            return
        if session is None:
            return

        try:
            async for raw_message in websocket:
                await session.handle_client_message(connection, json.loads(raw_message))
        except websockets.exceptions.ConnectionClosed:
            pass  # the other player's window closing mid-game is a normal disconnect, not an error
        finally:
            await session.handle_disconnect(connection)
    finally:
        active_usernames.discard(connection.username)
        logger.info("connection closed: %s", connection.username)


def make_handler(queue, account_store, active_usernames, room_manager):
    async def handler(websocket):
        logger.info("connection opened")
        await handle_connection(websocket, queue, account_store, active_usernames, room_manager)
    return handler


async def serve(host="localhost", port=8765, accounts_db_path=DEFAULT_ACCOUNTS_DB_PATH):
    setup_logging()
    queue = MatchmakingQueue()
    room_manager = RoomManager()
    account_store = AccountStore(accounts_db_path)
    active_usernames = set()
    async with websockets.serve(make_handler(queue, account_store, active_usernames, room_manager), host, port):
        logger.info("server listening on %s:%s", host, port)
        await asyncio.Future()  # run forever
