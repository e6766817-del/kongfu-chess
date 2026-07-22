"""Blocking modal shown from HomeScreen's "Room" button: lets the player
either Create a new room (server generates an ID) or Join an existing one
by typing its ID, then waits for the room's game to start -- same
blocking-modal shape as LoginScreen/MatchmakingScreen (reuses WINDOW_NAME so
GameLoop.run() can take over the window afterward). The room ID is shown at
the top of the screen as soon as it's known (immediately on Join, or once
the server's room_created reply arrives on Create), per the room ID display
requirement.

run() returns one of:
  - None                                                    (quit/cancel)
  - ("player", color, board_rows, username, opponent_username,
     rating, opponent_rating)                                (2nd joiner: match_found)
  - ("viewer", board_rows, white_username, black_username,
     white_rating, black_rating)                              (3rd+ joiner: spectate_start)
"""

import cv2
import numpy as np

from kfchess.gui.config import CANVAS_SIZE_PX
from kfchess.gui.img import Img

WINDOW_NAME = "Kung Fu Chess"
QUIT_KEY = 27  # Esc

BACKSPACE_KEYS = (8, 127)
ENTER_KEYS = (13, 10)

BG_COLOR = (24, 22, 20, 255)  # BGRA
FIELD_BG_COLOR = (44, 39, 36, 255)
FIELD_BORDER_COLOR = (0, 110, 160, 255)
LABEL_COLOR = (235, 235, 235, 255)
TEXT_COLOR = (235, 235, 235, 255)
ROOM_ID_COLOR = (0, 200, 255, 255)
ERROR_COLOR = (80, 80, 255, 255)
HINT_COLOR = (160, 160, 160, 255)
BUTTON_BG_COLOR = (44, 39, 36, 255)
BUTTON_HOVER_BG_COLOR = (60, 53, 49, 255)
BUTTON_BORDER_COLOR = (0, 110, 160, 255)
BUTTON_HOVER_BORDER_COLOR = (0, 179, 255, 255)
BUTTON_TEXT_COLOR = (235, 235, 235, 255)

TITLE = "Play in a Room"
FIELD_WIDTH_PX = 320
FIELD_HEIGHT_PX = 40
FIELD_Y = 190

BUTTON_WIDTH_PX = 150
BUTTON_HEIGHT_PX = 60
BUTTON_GAP_PX = 20
BUTTON_Y = 270
BUTTON_LABELS = ("Create", "Join", "Cancel")


class RoomDialog:
    def __init__(self, network_client):
        self._network_client = network_client
        self._room_id_field = ""
        self._state = "input"  # "input" or "waiting"
        self._status_message = ""
        self._error_message = None
        self._display_room_id = None
        self._quit = False
        self._hovered_button = None

    def run(self):
        cv2.namedWindow(WINDOW_NAME)
        cv2.setMouseCallback(WINDOW_NAME, self._on_mouse)

        while True:
            canvas = self._render()
            cv2.imshow(WINDOW_NAME, canvas.img)
            key = cv2.waitKey(16) & 0xFF

            if self._quit:
                return None

            if self._state == "waiting":
                result = self._poll_reply()
                if result is not None:
                    return result
            elif key != 0xFF:
                if key == QUIT_KEY:
                    return None
                self._handle_key(key)

            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                return None

    def _handle_key(self, key):
        if key in ENTER_KEYS:
            self._try_join()
        elif key in BACKSPACE_KEYS:
            self._room_id_field = self._room_id_field[:-1]
        elif 32 <= key < 127:
            self._room_id_field += chr(key).upper()

    def _try_create(self):
        self._error_message = None
        self._network_client.create_room()
        self._status_message = "Creating room..."
        self._state = "waiting"

    def _try_join(self):
        room_id = self._room_id_field.strip()
        if not room_id:
            self._error_message = "Enter a room ID to join"
            return
        self._error_message = None
        self._network_client.join_room(room_id)
        self._display_room_id = room_id
        self._status_message = "Joining room..."
        self._state = "waiting"

    def _poll_reply(self):
        for message in self._network_client.poll_messages():
            message_type = message["type"]
            if message_type == "room_created":
                self._display_room_id = message["room_id"]
                self._status_message = "Waiting for opponent..."
            elif message_type == "error":
                self._error_message = message["message"]
                self._state = "input"
                self._display_room_id = None
            elif message_type == "match_found":
                return (
                    "player", message["color"], message["board"], message["username"],
                    message["opponent_username"], message["rating"], message["opponent_rating"],
                )
            elif message_type == "spectate_start":
                return (
                    "viewer", message["board"], message["white_username"], message["black_username"],
                    message["white_rating"], message["black_rating"],
                )
        return None

    def _button_rects(self):
        canvas_w, _ = CANVAS_SIZE_PX
        total_width = 3 * BUTTON_WIDTH_PX + 2 * BUTTON_GAP_PX
        start_x = (canvas_w - total_width) // 2
        rects = {}
        for index, label in enumerate(BUTTON_LABELS):
            x = start_x + index * (BUTTON_WIDTH_PX + BUTTON_GAP_PX)
            rects[label] = (x, BUTTON_Y, BUTTON_WIDTH_PX, BUTTON_HEIGHT_PX)
        return rects

    def _on_mouse(self, event, x, y, flags, param):
        if self._state != "input":
            self._hovered_button = None
            return

        self._hovered_button = None
        for label, (bx, by, bw, bh) in self._button_rects().items():
            if bx <= x < bx + bw and by <= y < by + bh:
                self._hovered_button = label
                break

        if event == cv2.EVENT_LBUTTONDOWN and self._hovered_button is not None:
            if self._hovered_button == "Create":
                self._try_create()
            elif self._hovered_button == "Join":
                self._try_join()
            elif self._hovered_button == "Cancel":
                self._quit = True

    def _render(self):
        canvas_w, canvas_h = CANVAS_SIZE_PX
        canvas = Img()
        canvas.img = np.empty((canvas_h, canvas_w, 4), dtype=np.uint8)
        canvas.img[:, :] = BG_COLOR

        (title_w, _), _ = cv2.getTextSize(TITLE, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
        canvas.put_text(TITLE, (canvas_w - title_w) // 2, 60, 1.0, color=TEXT_COLOR, thickness=2)

        if self._display_room_id:
            room_text = f"Room: {self._display_room_id}"
            (room_w, _), _ = cv2.getTextSize(room_text, cv2.FONT_HERSHEY_SIMPLEX, 1.1, 2)
            canvas.put_text(room_text, (canvas_w - room_w) // 2, 110, 1.1, color=ROOM_ID_COLOR, thickness=2)

        if self._state == "input":
            self._render_input(canvas)
        else:
            (status_w, _), _ = cv2.getTextSize(self._status_message, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
            canvas.put_text(
                self._status_message, (canvas_w - status_w) // 2, 200, 0.8, color=HINT_COLOR, thickness=2,
            )

        if self._error_message:
            (error_w, _), _ = cv2.getTextSize(self._error_message, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            canvas.put_text(
                self._error_message, (canvas_w - error_w) // 2, canvas_h - 40, 0.7, color=ERROR_COLOR, thickness=2,
            )

        return canvas

    def _render_input(self, canvas):
        canvas_w, _ = CANVAS_SIZE_PX
        field_x = (canvas_w - FIELD_WIDTH_PX) // 2
        canvas.put_text("Room ID (to Join)", field_x, FIELD_Y - 10, 0.6, color=LABEL_COLOR, thickness=2)
        cv2.rectangle(
            canvas.img, (field_x, FIELD_Y), (field_x + FIELD_WIDTH_PX, FIELD_Y + FIELD_HEIGHT_PX),
            FIELD_BG_COLOR, -1,
        )
        cv2.rectangle(
            canvas.img, (field_x, FIELD_Y), (field_x + FIELD_WIDTH_PX, FIELD_Y + FIELD_HEIGHT_PX),
            FIELD_BORDER_COLOR, 2,
        )
        canvas.put_text(
            self._room_id_field, field_x + 10, FIELD_Y + FIELD_HEIGHT_PX - 12, 0.6, color=TEXT_COLOR, thickness=2,
        )

        for label, (x, y, w, h) in self._button_rects().items():
            is_hovered = self._hovered_button == label
            bg_color = BUTTON_HOVER_BG_COLOR if is_hovered else BUTTON_BG_COLOR
            border_color = BUTTON_HOVER_BORDER_COLOR if is_hovered else BUTTON_BORDER_COLOR
            cv2.rectangle(canvas.img, (x, y), (x + w, y + h), bg_color, -1)
            cv2.rectangle(canvas.img, (x, y), (x + w, y + h), border_color, 2)
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            canvas.put_text(
                label, x + (w - label_w) // 2, y + (h + label_h) // 2, 0.7, color=BUTTON_TEXT_COLOR, thickness=2,
            )
