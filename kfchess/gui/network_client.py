"""NetworkClient: a background-thread bridge between the cv2 GUI's
synchronous per-frame loop and the async websocket connection to
kfchess.server -- GameLoop.run() is a blocking cv2 loop on the main
thread, so it polls poll_messages() once per frame rather than using
async/await directly; sending is fire-and-forget via
run_coroutine_threadsafe onto the background thread's own event loop.
"""

import asyncio
import json
import queue
import threading

import websockets


class NetworkClient:
    def __init__(self, uri):
        self._uri = uri
        self._incoming = queue.Queue()
        self._loop = None
        self._websocket = None
        self._connected = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._connected.wait()

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._main())

    async def _main(self):
        async with websockets.connect(self._uri) as websocket:
            self._websocket = websocket
            self._connected.set()
            await websocket.send(json.dumps({"type": "join_queue"}))
            async for raw_message in websocket:
                self._incoming.put(json.loads(raw_message))

    def poll_messages(self):
        """Non-blocking: returns all messages received since the last
        call, oldest first. Call once per frame from the main thread."""
        messages = []
        while True:
            try:
                messages.append(self._incoming.get_nowait())
            except queue.Empty:
                break
        return messages

    def send_move(self, from_position, to_position):
        self._send({
            "type": "move",
            "from": [from_position.row, from_position.col],
            "to": [to_position.row, to_position.col],
        })

    def send_jump(self, position):
        self._send({"type": "jump", "position": [position.row, position.col]})

    def _send(self, message):
        asyncio.run_coroutine_threadsafe(self._websocket.send(json.dumps(message)), self._loop)
