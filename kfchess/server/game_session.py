"""GameSession: the networked analog of the GUI's GameLoop -- owns a
GameEngine for one match, drives its tick loop, authorizes/dispatches
client move requests, and broadcasts settlement events to both
connections.
"""

import asyncio
import json

import websockets

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

DISCONNECT_RESIGN_SECONDS = 20.0


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
    def __init__(self, white, black, account_store, tick_ms=50, disconnect_resign_seconds=DISCONNECT_RESIGN_SECONDS):
        board = build_board(STARTING_GRID)
        self._engine = GameEngine(board)
        self._outgoing = []
        self._engine.add_observer(_BroadcastObserver(self._outgoing))
        white.color, black.color = "w", "b"
        self._connections = {"w": white, "b": black}
        self._account_store = account_store
        self._tick_ms = tick_ms
        self._disconnect_resign_seconds = disconnect_resign_seconds
        # Set once by handle_disconnect (a player's socket closing mid-game)
        # or once the game reaches a natural end -- either way, run()'s tick
        # loop stops and no further per-tick broadcasts are sent.
        self._active = True

    async def _send(self, connection, message):
        # A player closing their window mid-game is a normal disconnect,
        # not a session-ending error -- swallow it so the tick loop keeps
        # running (and the other player's own requests keep getting
        # replies) rather than crashing the whole session task.
        try:
            await connection.websocket.send(json.dumps(message, cls=protocol.Encoder))
        except websockets.exceptions.ConnectionClosed:
            pass

    async def _broadcast(self, message):
        for connection in self._connections.values():
            await self._send(connection, message)

    async def run(self):
        board_rows = render_board(self._engine.board()).split("\n")
        for color, connection in self._connections.items():
            opponent = self._opponent_of(connection)
            await self._send(
                connection,
                protocol.match_found(
                    color, board_rows, connection.username, opponent.username,
                    connection.rating, opponent.rating,
                ),
            )

        while self._active and not self._engine.is_game_over():
            self._engine.advance_clock(self._tick_ms)
            while self._outgoing:
                await self._broadcast(self._outgoing.pop(0))
            await asyncio.sleep(self._tick_ms / 1000)

        if self._active:
            winner_color = self._engine.winner_color()
            await self._broadcast(protocol.game_over(winner=winner_color))
            if winner_color is not None:
                loser_color = self._opponent_color(winner_color)
                self._account_store.record_result(
                    self._connections[winner_color].username, self._connections[loser_color].username
                )

    async def handle_disconnect(self, connection):
        """Called once a player's socket closes -- stops run()'s tick loop
        (a disconnected game shouldn't keep ticking for a lone remaining
        player) and tells the other connection why, instead of just going
        silent or letting them play on alone. There is no reconnect
        concept in this codebase (see session.py), so after a grace
        period the disconnected player is auto-resigned and the result is
        recorded."""
        if not self._active:
            return
        self._active = False
        opponent = self._opponent_of(connection)
        await self._send(opponent, protocol.opponent_disconnected(self._disconnect_resign_seconds))
        await asyncio.sleep(self._disconnect_resign_seconds)
        await self._send(opponent, protocol.opponent_resigned())
        self._account_store.record_result(opponent.username, connection.username)

    async def handle_client_message(self, connection, message):
        message_type = message.get("type")
        if message_type == "move":
            from_position = Position(*message["from"])
            to_position = Position(*message["to"])
            await self._dispatch(
                connection, from_position,
                request=lambda: self._engine.request_move(from_position, to_position),
                on_accept=lambda piece: protocol.opponent_move(piece.color, piece.kind, from_position, to_position),
            )
        elif message_type == "jump":
            position = Position(*message["position"])
            await self._dispatch(
                connection, position,
                request=lambda: self._engine.request_jump(position),
                on_accept=lambda piece: protocol.opponent_jump(piece.color, piece.kind, position),
            )
        else:
            await self._send(connection, protocol.error(f"unknown message type: {message_type}"))

    async def _dispatch(self, connection, piece_position, request, on_accept):
        piece = self._engine.board().get(piece_position)
        if piece is None or piece.color != connection.color:
            await self._send(connection, protocol.error("no piece of your color at that position"))
            return
        result = request()
        await self._send(connection, protocol.move_result(result.accepted, result.reason, result.arrival_time_ms))
        if result.accepted:
            opponent = self._opponent_of(connection)
            await self._send(opponent, on_accept(piece))

    def _opponent_of(self, connection):
        return self._connections["b"] if connection is self._connections["w"] else self._connections["w"]

    @staticmethod
    def _opponent_color(color):
        return "b" if color == "w" else "w"
