"""websockets entrypoint: wires one shared MatchmakingQueue to each
incoming connection, following the matchmaking flow up to a 60s
"no opponent found" timeout, then hands off to the GameSession's
message loop once a match is formed.
"""

import asyncio
import json

import websockets

from kfchess.server import protocol
from kfchess.server.game_session import GameSession
from kfchess.server.matchmaking import MatchmakingQueue
from kfchess.server.session import PlayerConnection

MATCHMAKING_TIMEOUT_SECONDS = 60.0


async def handle_connection(websocket, queue):
    connection = PlayerConnection(websocket)

    join_message = json.loads(await websocket.recv())
    if join_message.get("type") != "join_queue":
        await websocket.send(json.dumps(protocol.error("expected join_queue")))
        return
    await websocket.send(json.dumps(protocol.queued()))

    opponent = await queue.join(connection)
    if opponent is not None:
        session = GameSession(white=opponent, black=connection)
        asyncio.create_task(session.run())
        opponent.matched.set_result((connection, session))
    else:
        try:
            _, session = await asyncio.wait_for(connection.matched, timeout=MATCHMAKING_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            await queue.cancel_waiting(connection)
            await websocket.send(json.dumps(protocol.no_opponent_found()))
            return

    try:
        async for raw_message in websocket:
            await session.handle_client_message(connection, json.loads(raw_message))
    except websockets.exceptions.ConnectionClosed:
        pass  # the other player's window closing mid-game is a normal disconnect, not an error


def make_handler(queue):
    async def handler(websocket):
        await handle_connection(websocket, queue)
    return handler


async def serve(host="localhost", port=8765):
    queue = MatchmakingQueue()
    async with websockets.serve(make_handler(queue), host, port):
        await asyncio.Future()  # run forever
