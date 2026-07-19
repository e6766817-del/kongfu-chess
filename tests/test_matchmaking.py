import asyncio

import pytest

from kfchess.server.matchmaking import MatchmakingQueue
from kfchess.server.session import PlayerConnection


def make_connection():
    return PlayerConnection(websocket=None)


@pytest.mark.asyncio
async def test_second_join_pairs_with_first():
    queue = MatchmakingQueue()
    first = make_connection()
    second = make_connection()

    assert await queue.join(first) is None
    assert await queue.join(second) is first


@pytest.mark.asyncio
async def test_lone_join_times_out_and_clears_waiting_slot():
    queue = MatchmakingQueue()
    first = make_connection()

    assert await queue.join(first) is None
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(first.matched, timeout=0.05)
    await queue.cancel_waiting(first)

    second = make_connection()
    third = make_connection()
    assert await queue.join(second) is None
    assert await queue.join(third) is second
