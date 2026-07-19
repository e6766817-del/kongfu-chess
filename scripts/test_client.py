"""Throwaway manual verification script for kfchess/server -- not part
of the package. Connects, joins the matchmaking queue, prints every
message received, and sends one hardcoded move once matched (as white)
to prove the pairing/authorization/broadcast round-trip works.

Run the server first: python -m kfchess.server
Then run two copies of this script in separate terminals:
    python scripts/test_client.py
"""

import asyncio
import json
import sys

import websockets

SERVER_URI = "ws://localhost:8765"


async def main():
    async with websockets.connect(SERVER_URI) as websocket:
        await websocket.send(json.dumps({"type": "join_queue"}))

        while True:
            try:
                raw_message = await asyncio.wait_for(websocket.recv(), timeout=5)
            except asyncio.TimeoutError:
                print("(no more messages, exiting)", flush=True)
                break

            message = json.loads(raw_message)
            print(message, flush=True)

            if message["type"] == "match_found" and message["color"] == "w":
                # e2-e4 in (row, col), row 0 = black's back rank.
                await websocket.send(json.dumps({"type": "move", "from": [6, 4], "to": [4, 4]}))

            if message["type"] in ("no_opponent_found", "game_over"):
                break


if __name__ == "__main__":
    asyncio.run(main())
