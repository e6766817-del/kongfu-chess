"""Skin-selection menu shown before the game starts: one card per
AVAILABLE_SKINS entry, each previewing a sample piece sprite from that
skin, so the player can see what a skin looks like before picking it
with the mouse (rather than guessing from a --skin CLI flag)."""

import cv2
import numpy as np

from kfchess.gui import assets
from kfchess.gui.config import AVAILABLE_SKINS, CANVAS_SIZE_PX
from kfchess.gui.img import Img

WINDOW_NAME = "Kung Fu Chess"
QUIT_KEYS = (ord("q"), 27)  # 'q' or Esc

TITLE = "Choose a piece skin"
TITLE_Y = 60

CARD_WIDTH_PX = 220
CARD_HEIGHT_PX = 280
CARD_GAP_PX = 40
CARD_TOP_Y = 110

SAMPLE_SIZE_PX = (160, 160)
SAMPLE_TOP_PAD_PX = 50

BG_COLOR = (24, 22, 20, 255)  # BGRA
CARD_BG_COLOR = (44, 39, 36, 255)
CARD_HOVER_BG_COLOR = (60, 53, 49, 255)
CARD_BORDER_COLOR = (0, 110, 160, 255)
CARD_HOVER_BORDER_COLOR = (0, 179, 255, 255)
TITLE_COLOR = (235, 235, 235, 255)
LABEL_COLOR = (235, 235, 235, 255)


class SkinMenu:
    """Blocking modal: shows one card per available skin and returns the
    chosen skin name once the player clicks a card, or None if they
    close the window / press Esc first."""

    def __init__(self, skins=AVAILABLE_SKINS, sample_kind="K", sample_color="w"):
        self._skins = list(skins)
        self._sample_kind = sample_kind
        self._sample_color = sample_color
        self._samples_by_skin = {}
        self._hovered_skin = None
        self._selected_skin = None

    def run(self):
        """Show the menu and block until the player picks a skin (or
        quits), then return the chosen skin name / None. Leaves the cv2
        window open on success -- GameLoop.run() reuses the same
        WINDOW_NAME for the game itself."""
        cv2.namedWindow(WINDOW_NAME)
        cv2.setMouseCallback(WINDOW_NAME, self._on_mouse)

        while self._selected_skin is None:
            canvas = self._render()
            cv2.imshow(WINDOW_NAME, canvas.img)
            key = cv2.waitKey(16) & 0xFF
            if key in QUIT_KEYS:
                return None
            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                return None
        return self._selected_skin

    def _sample_for(self, skin):
        if skin not in self._samples_by_skin:
            path = assets.sprite_paths(self._sample_kind, self._sample_color, "idle", skin)[0]
            self._samples_by_skin[skin] = Img().read(path, size=SAMPLE_SIZE_PX, keep_aspect=True)
        return self._samples_by_skin[skin]

    def _card_rects(self):
        """(x, y, w, h, skin) for each card, centered as a row under the title."""
        total_width = len(self._skins) * CARD_WIDTH_PX + (len(self._skins) - 1) * CARD_GAP_PX
        start_x = (CANVAS_SIZE_PX[0] - total_width) // 2
        return [
            (start_x + index * (CARD_WIDTH_PX + CARD_GAP_PX), CARD_TOP_Y, CARD_WIDTH_PX, CARD_HEIGHT_PX, skin)
            for index, skin in enumerate(self._skins)
        ]

    def _render(self):
        canvas_w, canvas_h = CANVAS_SIZE_PX
        canvas = Img()
        canvas.img = np.empty((canvas_h, canvas_w, 4), dtype=np.uint8)
        canvas.img[:, :] = BG_COLOR

        (title_w, _), _ = cv2.getTextSize(TITLE, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
        canvas.put_text(TITLE, (canvas_w - title_w) // 2, TITLE_Y, 1.0, color=TITLE_COLOR, thickness=2)

        for x, y, w, h, skin in self._card_rects():
            self._draw_card(canvas, x, y, w, h, skin)

        return canvas

    def _draw_card(self, canvas, x, y, w, h, skin):
        is_hover = skin == self._hovered_skin
        bg_color = CARD_HOVER_BG_COLOR if is_hover else CARD_BG_COLOR
        border_color = CARD_HOVER_BORDER_COLOR if is_hover else CARD_BORDER_COLOR
        cv2.rectangle(canvas.img, (x, y), (x + w, y + h), bg_color, -1)
        cv2.rectangle(canvas.img, (x, y), (x + w, y + h), border_color, 2)

        sample = self._sample_for(skin)
        sample_h, sample_w = sample.img.shape[:2]
        sample.draw_on(canvas, x + (w - sample_w) // 2, y + SAMPLE_TOP_PAD_PX + (SAMPLE_SIZE_PX[1] - sample_h) // 2)

        (label_w, _), _ = cv2.getTextSize(skin, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        canvas.put_text(skin, x + (w - label_w) // 2, y + h - 20, 0.6, color=LABEL_COLOR, thickness=2)

    def _on_mouse(self, event, x, y, flags, param):
        self._hovered_skin = next(
            (skin for cx, cy, cw, ch, skin in self._card_rects() if cx <= x < cx + cw and cy <= y < cy + ch),
            None,
        )
        if event == cv2.EVENT_LBUTTONDOWN and self._hovered_skin is not None:
            self._selected_skin = self._hovered_skin
