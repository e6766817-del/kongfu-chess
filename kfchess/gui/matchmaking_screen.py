"""Blocking modal shown after connecting to kfchess.server and before
the game starts: polls the NetworkClient for match_found/
no_opponent_found while showing a waiting message, same blocking-modal
shape as SkinMenu (reuses the same WINDOW_NAME so GameLoop.run() can
take over the window afterward).
"""

import time

import cv2
import numpy as np

from kfchess.gui.config import CANVAS_SIZE_PX
from kfchess.gui.img import Img

WINDOW_NAME = "Kung Fu Chess"
QUIT_KEYS = (ord("q"), 27)  # 'q' or Esc

BG_COLOR = (24, 22, 20, 255)  # BGRA
TEXT_COLOR = (235, 235, 235, 255)
ERROR_COLOR = (80, 80, 255, 255)

WAITING_TEXT = "Waiting for an opponent..."
NO_OPPONENT_TEXT = "No opponent found. Press any key to quit."


class MatchmakingScreen:
    """Shows a waiting message while polling `network_client` for the
    server's matchmaking result. run() blocks until either:
      - match_found arrives: returns (color, board_rows)
      - no_opponent_found arrives, or the player quits: returns None
    """

    def __init__(self, network_client):
        self._network_client = network_client

    def run(self):
        cv2.namedWindow(WINDOW_NAME)
        start_time = time.perf_counter()

        while True:
            for message in self._network_client.poll_messages():
                if message["type"] == "match_found":
                    return message["color"], message["board"]
                if message["type"] == "no_opponent_found":
                    self._show(NO_OPPONENT_TEXT)
                    cv2.waitKey(0)
                    return None

            elapsed_seconds = int(time.perf_counter() - start_time)
            self._show(f"{WAITING_TEXT} ({elapsed_seconds}s)")

            key = cv2.waitKey(16) & 0xFF
            if key in QUIT_KEYS:
                return None
            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                return None

    def _show(self, text):
        canvas_w, canvas_h = CANVAS_SIZE_PX
        canvas = Img()
        canvas.img = np.empty((canvas_h, canvas_w, 4), dtype=np.uint8)
        canvas.img[:, :] = BG_COLOR
        (text_w, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        canvas.put_text(text, (canvas_w - text_w) // 2, canvas_h // 2, 0.8, color=TEXT_COLOR, thickness=2)
        cv2.imshow(WINDOW_NAME, canvas.img)
