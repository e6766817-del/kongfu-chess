"""GameSession: the networked analog of the GUI's GameLoop -- owns a
GameEngine for one match, drives its tick loop, authorizes/dispatches
client move requests, and broadcasts settlement events to both
connections.
"""

import asyncio
import json

from kfchess.engine.game_engine import GameEngine
from kfchess.io.board_printer import render as render_board
from kfchess.io.validator import build_board
from kfchess.model.position import Position
from kfchess.realtime.observers import ArbiterObserver
from kfchess.server import protocol

STARTING_GRID = [
    "bR bN bB bQ bK bB bN bR".split(),
    ["bP"] * 8,
    ["."] * 8,
    ["."] * 8,
    ["."] * 8,
    ["."] * 8,
    ["wP"] * 8,
    "wR wN wB wQ wK wB wN wR".split(),
]


class _BroadcastObserver(ArbiterObserver):
    """Queues broadcast messages instead of sending them directly --
    ArbiterObserver callbacks fire synchronously inside advance_clock()
    (a sync call), but websocket sends are coroutines, so GameSession's
    tick loop drains and awaits-sends this queue after each tick."""

    def __init__(self, outgoing):
        self._outgoing = outgoing

    def on_move_settled(self, color, piece_type, from_position, to_position):
        self._outgoing.append(protocol.move_settled(color, piece_type, from_position, to_position))

    def on_piece_captured(self, color, piece_type):
        self._outgoing.append(protocol.piece_captured(color, piece_type))


class GameSession:
    def __init__(self, white, black, tick_ms=50):
        board = build_board(STARTING_GRID)
        self._engine = GameEngine(board)
        self._outgoing = []
        self._engine.add_observer(_BroadcastObserver(self._outgoing))
        white.color, black.color = "w", "b"
        self._connections = {"w": white, "b": black}
        self._tick_ms = tick_ms

    async def _send(self, connection, message):
        await connection.websocket.send(json.dumps(message))

    async def _broadcast(self, message):
        for connection in self._connections.values():
            await self._send(connection, message)

    async def run(self):
        board_rows = render_board(self._engine.board()).split("\n")
        for color, connection in self._connections.items():
            await self._send(connection, protocol.match_found(color, board_rows))

        while not self._engine.is_game_over():
            self._engine.advance_clock(self._tick_ms)
            while self._outgoing:
                await self._broadcast(self._outgoing.pop(0))
            await asyncio.sleep(self._tick_ms / 1000)

        await self._broadcast(protocol.game_over())

    async def handle_client_message(self, connection, message):
        message_type = message.get("type")
        if message_type == "move":
            from_position = Position(*message["from"])
            to_position = Position(*message["to"])
            await self._dispatch(connection, from_position, lambda: self._engine.request_move(from_position, to_position))
        elif message_type == "jump":
            position = Position(*message["position"])
            await self._dispatch(connection, position, lambda: self._engine.request_jump(position))
        else:
            await self._send(connection, protocol.error(f"unknown message type: {message_type}"))

    async def _dispatch(self, connection, piece_position, request):
        piece = self._engine.board().get(piece_position)
        if piece is None or piece.color != connection.color:
            await self._send(connection, protocol.error("no piece of your color at that position"))
            return
        result = request()
        await self._send(connection, protocol.move_result(result.accepted, result.reason, result.arrival_time_ms))
