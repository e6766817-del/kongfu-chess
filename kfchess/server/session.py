"""PlayerConnection: the smallest session concept needed for
matchmaking + move authorization -- there is no reconnect concept
anywhere else in the codebase, so this is scoped tightly to this
feature (a websocket, its assigned color once matched, the logged-in
username/rating set by the login handshake in server.py, and a future
that resolves when matchmaking pairs it with an opponent).
"""

import asyncio
from dataclasses import dataclass, field


@dataclass
class PlayerConnection:
    websocket: object
    color: str = None
    username: str = None
    rating: int = None
    matched: asyncio.Future = field(default_factory=lambda: asyncio.get_running_loop().create_future())
