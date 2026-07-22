import asyncio

import pytest

from kfchess.server.matchmaking import MatchmakingQueue
from kfchess.server.session import PlayerConnection


def make_connection(rating=1200):
    return PlayerConnection(websocket=None, rating=rating)


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


@pytest.mark.asyncio
async def test_join_within_rating_range_pairs_immediately():
    queue = MatchmakingQueue()
    first = make_connection(rating=1000)
    second = make_connection(rating=1090)

    assert await queue.join(first) is None
    assert await queue.join(second) is first


@pytest.mark.asyncio
async def test_join_outside_rating_range_waits_for_compatible_arrival():
    queue = MatchmakingQueue()
    first = make_connection(rating=1000)
    second = make_connection(rating=1150)

    assert await queue.join(first) is None
    assert await queue.join(second) is None

    third = make_connection(rating=1120)
    assert await queue.join(third) is second


@pytest.mark.asyncio
async def test_cancel_waiting_removes_only_that_connection():
    queue = MatchmakingQueue()
    first = make_connection(rating=1000)
    second = make_connection(rating=1150)

    assert await queue.join(first) is None
    assert await queue.join(second) is None
    await queue.cancel_waiting(first)

    third = make_connection(rating=1120)
    assert await queue.join(third) is second
