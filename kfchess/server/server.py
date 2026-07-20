"""websockets entrypoint: wires one shared MatchmakingQueue to each
incoming connection, following the login handshake and then the
matchmaking flow up to a 60s "no opponent found" timeout, then hands
off to the GameSession's message loop once a match is formed.
"""

import asyncio
import json

import websockets

from kfchess.server import protocol
from kfchess.server.accounts import AccountStore
from kfchess.server.game_session import GameSession
from kfchess.server.matchmaking import MatchmakingQueue
from kfchess.server.session import PlayerConnection

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
        await websocket.send(json.dumps(protocol.login_error(result.reason), cls=protocol.Encoder))
        return False

    active_usernames.add(username)
    connection.username = username
    connection.rating = result.rating
    await websocket.send(json.dumps(protocol.login_ok(result.rating), cls=protocol.Encoder))
    return True


async def handle_connection(websocket, queue, account_store, active_usernames):
    connection = PlayerConnection(websocket)

    if not await _login(websocket, connection, account_store, active_usernames):
        return

    try:
        join_message = json.loads(await websocket.recv())
        if join_message.get("type") != "join_queue":
            await websocket.send(json.dumps(protocol.error("expected join_queue"), cls=protocol.Encoder))
            return
        await websocket.send(json.dumps(protocol.queued(), cls=protocol.Encoder))

        opponent = await queue.join(connection)
        if opponent is not None:
            session = GameSession(white=opponent, black=connection, account_store=account_store)
            asyncio.create_task(session.run())
            opponent.matched.set_result((connection, session))
        else:
            try:
                _, session = await asyncio.wait_for(connection.matched, timeout=MATCHMAKING_TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                await queue.cancel_waiting(connection)
                await websocket.send(json.dumps(protocol.no_opponent_found(), cls=protocol.Encoder))
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


def make_handler(queue, account_store, active_usernames):
    async def handler(websocket):
        await handle_connection(websocket, queue, account_store, active_usernames)
    return handler


async def serve(host="localhost", port=8765, accounts_db_path=DEFAULT_ACCOUNTS_DB_PATH):
    queue = MatchmakingQueue()
    account_store = AccountStore(accounts_db_path)
    active_usernames = set()
    async with websockets.serve(make_handler(queue, account_store, active_usernames), host, port):
        await asyncio.Future()  # run forever
