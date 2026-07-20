"""Blocking modal shown before matchmaking: collects a username/password,
sends a login request over `network_client`, and waits for the server's
login_ok/login_error reply -- same blocking-modal shape as SkinMenu/
MatchmakingScreen (reuses the same WINDOW_NAME so GameLoop.run() can
take over the window afterward). On login_error the player can retry
without relaunching (e.g. a mistyped password).
"""

import cv2
import numpy as np

from kfchess.gui.config import CANVAS_SIZE_PX
from kfchess.gui.img import Img

WINDOW_NAME = "Kung Fu Chess"
QUIT_KEY = 27  # Esc -- 'q' isn't reserved here since it's a valid username/password character

BACKSPACE_KEYS = (8, 127)
ENTER_KEYS = (13, 10)
TAB_KEY = 9

BG_COLOR = (24, 22, 20, 255)  # BGRA
FIELD_BG_COLOR = (44, 39, 36, 255)
FIELD_ACTIVE_BORDER_COLOR = (0, 179, 255, 255)
FIELD_BORDER_COLOR = (0, 110, 160, 255)
LABEL_COLOR = (235, 235, 235, 255)
TEXT_COLOR = (235, 235, 235, 255)
ERROR_COLOR = (80, 80, 255, 255)
HINT_COLOR = (160, 160, 160, 255)

TITLE = "Log in to play online"
FIELD_WIDTH_PX = 320
FIELD_HEIGHT_PX = 40
FIELD_GAP_PX = 70
FIRST_FIELD_Y = 160


class LoginScreen:
    """Shows username/password fields, then blocks waiting for the
    server's login reply once submitted. run() returns (username,
    password) once login succeeds, or None if the player quits."""

    def __init__(self, network_client):
        self._network_client = network_client
        self._fields = {"username": "", "password": ""}
        self._active_field = "username"
        self._error_message = None
        self._waiting = False

    def run(self):
        cv2.namedWindow(WINDOW_NAME)

        while True:
            canvas = self._render()
            cv2.imshow(WINDOW_NAME, canvas.img)
            key = cv2.waitKey(16) & 0xFF

            if self._waiting:
                result = self._poll_login_reply()
                if result is not None:
                    return result
            elif key != 0xFF:
                submitted = self._handle_key(key)
                if submitted == "quit":
                    return None

            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                return None

    def _handle_key(self, key):
        if key == QUIT_KEY:
            return "quit"
        if key == TAB_KEY:
            self._active_field = "password" if self._active_field == "username" else "username"
        elif key in ENTER_KEYS:
            if self._fields["username"] and self._fields["password"]:
                self._error_message = None
                self._network_client.login(self._fields["username"], self._fields["password"])
                self._waiting = True
        elif key in BACKSPACE_KEYS:
            self._fields[self._active_field] = self._fields[self._active_field][:-1]
        elif 32 <= key < 127:
            self._fields[self._active_field] += chr(key)
        return None

    def _poll_login_reply(self):
        for message in self._network_client.poll_messages():
            if message["type"] == "login_ok":
                return self._fields["username"], self._fields["password"]
            if message["type"] == "login_error":
                self._waiting = False
                self._error_message = message["message"]
                return None
        return None

    def _render(self):
        canvas_w, canvas_h = CANVAS_SIZE_PX
        canvas = Img()
        canvas.img = np.empty((canvas_h, canvas_w, 4), dtype=np.uint8)
        canvas.img[:, :] = BG_COLOR

        (title_w, _), _ = cv2.getTextSize(TITLE, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
        canvas.put_text(TITLE, (canvas_w - title_w) // 2, 80, 1.0, color=TEXT_COLOR, thickness=2)

        field_x = (canvas_w - FIELD_WIDTH_PX) // 2
        self._draw_field(canvas, field_x, FIRST_FIELD_Y, "Username", self._fields["username"], "username")
        self._draw_field(
            canvas, field_x, FIRST_FIELD_Y + FIELD_GAP_PX, "Password",
            "*" * len(self._fields["password"]), "password",
        )

        status_y = FIRST_FIELD_Y + 2 * FIELD_GAP_PX + 20
        if self._waiting:
            canvas.put_text("Logging in...", field_x, status_y, 0.7, color=HINT_COLOR, thickness=2)
        elif self._error_message:
            canvas.put_text(self._error_message, field_x, status_y, 0.7, color=ERROR_COLOR, thickness=2)
        else:
            canvas.put_text("Tab to switch field, Enter to log in", field_x, status_y, 0.6, color=HINT_COLOR, thickness=2)

        return canvas

    def _draw_field(self, canvas, x, y, label, value, field_name):
        canvas.put_text(label, x, y - 10, 0.6, color=LABEL_COLOR, thickness=2)
        is_active = field_name == self._active_field
        border_color = FIELD_ACTIVE_BORDER_COLOR if is_active else FIELD_BORDER_COLOR
        cv2.rectangle(canvas.img, (x, y), (x + FIELD_WIDTH_PX, y + FIELD_HEIGHT_PX), FIELD_BG_COLOR, -1)
        cv2.rectangle(canvas.img, (x, y), (x + FIELD_WIDTH_PX, y + FIELD_HEIGHT_PX), border_color, 2)
        canvas.put_text(value, x + 10, y + FIELD_HEIGHT_PX - 12, 0.6, color=TEXT_COLOR, thickness=2)
