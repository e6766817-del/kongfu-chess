"""Blocking modal shown after login and before matchmaking: shows the
logged-in player's username/rating and a single Play button -- same
blocking-modal shape as SkinMenu/LoginScreen/MatchmakingScreen (reuses
the same WINDOW_NAME so the next screen can take over the window
afterward).
"""

import cv2
import numpy as np

from kfchess.gui.config import CANVAS_SIZE_PX
from kfchess.gui.img import Img

WINDOW_NAME = "Kung Fu Chess"
QUIT_KEYS = (ord("q"), 27)  # 'q' or Esc

BG_COLOR = (24, 22, 20, 255)  # BGRA
TEXT_COLOR = (235, 235, 235, 255)
HINT_COLOR = (160, 160, 160, 255)
BUTTON_BG_COLOR = (44, 39, 36, 255)
BUTTON_HOVER_BG_COLOR = (60, 53, 49, 255)
BUTTON_BORDER_COLOR = (0, 110, 160, 255)
BUTTON_HOVER_BORDER_COLOR = (0, 179, 255, 255)
BUTTON_TEXT_COLOR = (235, 235, 235, 255)

BUTTON_WIDTH_PX = 200
BUTTON_HEIGHT_PX = 70
BUTTON_TOP_Y = 230
BUTTON_LABEL = "Play"


class HomeScreen:
    """Shows the player's username/rating and a Play button. run() blocks
    until the player clicks Play (returns True) or quits (returns
    None)."""

    def __init__(self, username, rating):
        self._username = username
        self._rating = rating
        self._hovered = False
        self._play_clicked = False

    def run(self):
        cv2.namedWindow(WINDOW_NAME)
        cv2.setMouseCallback(WINDOW_NAME, self._on_mouse)

        while not self._play_clicked:
            canvas = self._render()
            cv2.imshow(WINDOW_NAME, canvas.img)
            key = cv2.waitKey(16) & 0xFF
            if key in QUIT_KEYS:
                return None
            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                return None
        return True

    def _button_rect(self):
        canvas_w, _ = CANVAS_SIZE_PX
        x = (canvas_w - BUTTON_WIDTH_PX) // 2
        return x, BUTTON_TOP_Y, BUTTON_WIDTH_PX, BUTTON_HEIGHT_PX

    def _render(self):
        canvas_w, canvas_h = CANVAS_SIZE_PX
        canvas = Img()
        canvas.img = np.empty((canvas_h, canvas_w, 4), dtype=np.uint8)
        canvas.img[:, :] = BG_COLOR

        greeting = f"Welcome, {self._username}"
        (greeting_w, _), _ = cv2.getTextSize(greeting, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
        canvas.put_text(greeting, (canvas_w - greeting_w) // 2, 100, 0.9, color=TEXT_COLOR, thickness=2)

        rating_text = f"Rating: {self._rating}"
        (rating_w, _), _ = cv2.getTextSize(rating_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        canvas.put_text(rating_text, (canvas_w - rating_w) // 2, 140, 0.7, color=HINT_COLOR, thickness=2)

        x, y, w, h = self._button_rect()
        bg_color = BUTTON_HOVER_BG_COLOR if self._hovered else BUTTON_BG_COLOR
        border_color = BUTTON_HOVER_BORDER_COLOR if self._hovered else BUTTON_BORDER_COLOR
        cv2.rectangle(canvas.img, (x, y), (x + w, y + h), bg_color, -1)
        cv2.rectangle(canvas.img, (x, y), (x + w, y + h), border_color, 2)
        (label_w, label_h), _ = cv2.getTextSize(BUTTON_LABEL, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
        canvas.put_text(
            BUTTON_LABEL, x + (w - label_w) // 2, y + (h + label_h) // 2, 0.9,
            color=BUTTON_TEXT_COLOR, thickness=2,
        )

        return canvas

    def _on_mouse(self, event, x, y, flags, param):
        bx, by, bw, bh = self._button_rect()
        self._hovered = bx <= x < bx + bw and by <= y < by + bh
        if event == cv2.EVENT_LBUTTONDOWN and self._hovered:
            self._play_clicked = True
