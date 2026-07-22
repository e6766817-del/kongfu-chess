"""MatchmakingQueue: pairs waiting connections whose ratings are within
RATING_RANGE of each other.

A single "waiting slot" isn't enough once rating matters -- two waiting
players outside each other's range must both stay queued until a
compatible third arrival, so this keeps a list instead.
"""

import asyncio

RATING_RANGE = 100


class MatchmakingQueue:
    def __init__(self):
        self._waiting = []
        self._lock = asyncio.Lock()

    async def join(self, connection):
        """Returns the first already-waiting connection within
        RATING_RANGE of `connection`'s rating (pairing the two under the
        lock), or appends `connection` to the waiting list and returns
        None."""
        async with self._lock:
            for opponent in self._waiting:
                if abs(opponent.rating - connection.rating) <= RATING_RANGE:
                    self._waiting.remove(opponent)
                    return opponent
            self._waiting.append(connection)
            return None

    async def cancel_waiting(self, connection):
        """Removes `connection` from the waiting list if it's still
        there -- called on timeout so a timed-out connection can never be
        paired with a later arrival."""
        async with self._lock:
            if connection in self._waiting:
                self._waiting.remove(connection)
