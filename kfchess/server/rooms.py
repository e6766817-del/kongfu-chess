"""RoomManager/Room: lets two specific players agree to play each other (as
opposed to MatchmakingQueue's anonymous rating-based pairing) plus any number
of read-only spectators.

The creator of a room is always White. The second connection to join becomes
Black and starts the game; every later joiner is a viewer. Room mirrors the
"matched future" pattern PlayerConnection already uses for matchmaking
(session.py) so both White and any viewers who joined before Black can
`await room.matched` for the GameSession to come into existence.
"""

import asyncio
import random
import string

ROOM_ID_LENGTH = 6
ROOM_ID_ALPHABET = string.ascii_uppercase + string.digits


class Room:
    def __init__(self, room_id, white):
        self.room_id = room_id
        self.white = white
        self.black = None
        self.game_session = None
        # Viewers who joined before Black -- handed to GameSession's
        # constructor once it's created so they start receiving broadcasts
        # from the very first tick.
        self.pending_viewers = []
        self.matched = asyncio.get_running_loop().create_future()


class RoomManager:
    def __init__(self):
        self._rooms = {}

    def create_room(self, white_connection):
        room_id = self._generate_unique_id()
        room = Room(room_id, white_connection)
        self._rooms[room_id] = room
        return room

    def get_room(self, room_id):
        return self._rooms.get(room_id)

    def _generate_unique_id(self):
        while True:
            candidate = "".join(random.choices(ROOM_ID_ALPHABET, k=ROOM_ID_LENGTH))
            if candidate not in self._rooms:
                return candidate
