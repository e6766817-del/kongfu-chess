"""MatchmakingQueue: pairs exactly two waiting connections at a time.

This is strictly 2-player pairing, not general N-way matchmaking, so
a single "waiting slot" guarded by a lock is enough -- asyncio.Queue
machinery would be unnecessary here.
"""

import asyncio


class MatchmakingQueue:
    def __init__(self):
        self._waiting = None
        self._lock = asyncio.Lock()

    async def join(self, connection):
        """Returns the opponent immediately if someone was already
        waiting (pairing the two under the lock), or records
        `connection` as the new waiting slot and returns None."""
        async with self._lock:
            opponent = self._waiting
            if opponent is None:
                self._waiting = connection
                return None
            self._waiting = None
            return opponent

    async def cancel_waiting(self, connection):
        """Clears the waiting slot if `connection` is still the one
        recorded as waiting -- called on timeout so a timed-out
        connection can never be paired with a later arrival."""
        async with self._lock:
            if self._waiting is connection:
                self._waiting = None
