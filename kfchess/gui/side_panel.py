"""One player's own column of HUD state -- score, captured pieces, and
move history -- drawn in the strip beside the board (white's on the
left, black's on the right; see kfchess.gui.config.LEFT_PANEL_X /
RIGHT_PANEL_X).

Wired as an ArbiterObserver (kfchess.realtime.observers) via
GameEngine.add_observer(): each SidePanel only reacts to the events
that belong to its own color, so nothing needs to poll or diff the
board to keep these lists in sync -- a move/capture updates only the
piece involved, not the whole panel.
"""

import cv2
import numpy as np

from kfchess.gui import assets
from kfchess.gui.config import CANVAS_SIZE_PX, DEFAULT_SKIN, SIDE_PANEL_WIDTH_PX
from kfchess.gui.img import Img
from kfchess.gui.notation import algebraic
from kfchess.model.piece import PIECE_VALUES

PIECE_NAMES = {"K": "K", "Q": "Q", "R": "R", "B": "B", "N": "N", "P": "P"}

# -- Theme: a dark, gold-trimmed "game HUD" look shared by both panels,
# with only the color-label chip flipped per side (a light plate for
# White, a dark plate for Black) -- think a chess clock's nameplate. --
BG_TOP_COLOR = (30, 26, 24, 255)  # BGRA, near-black warm brown
BG_BOTTOM_COLOR = (14, 12, 11, 255)  # BGRA, darker still
ACCENT_COLOR = (0, 179, 255, 255)  # BGRA, gold
ACCENT_DIM_COLOR = (0, 110, 160, 255)  # BGRA, muted gold (borders/underlines)
BORDER_EDGE_COLOR = ACCENT_DIM_COLOR
TEXT_PRIMARY_COLOR = (235, 235, 235, 255)  # BGRA, near-white
TEXT_SECONDARY_COLOR = (150, 150, 150, 255)  # BGRA, gray
WHITE_DOT_COLOR = (232, 232, 232, 255)
BLACK_DOT_COLOR = (58, 56, 55, 255)
SLOT_BG_COLOR = (44, 39, 36, 255)
BADGE_BG_COLOR = (40, 35, 33, 255)

PANEL_TEXT_X_PAD = 16

# The header is a single full-width nameplate card: a color-indicator
# dot, the player's username with their rating on a second line below it
# (or a WHITE/BLACK fallback for local, non-networked play where neither
# exists), and a small WHITE/BLACK tag in the corner -- replaces the old
# small fixed-width color chip, which had no room to fit a real username
# next to it.
HEADER_HEIGHT_PX = 66
HEADER_MARGIN_PX = 8
HEADER_RADIUS_PX = 8
HEADER_DOT_RADIUS_PX = 7
HEADER_DOT_PAD_PX = 14
HEADER_TAG_FONT_SCALE = 0.34
HEADER_RATING_FONT_SCALE = 0.42

SCORE_BADGE_TOP_Y = HEADER_HEIGHT_PX + 12
SCORE_BADGE_HEIGHT_PX = 32
SCORE_BADGE_RADIUS_PX = 6
SCORE_BADGE_BORDER_PX = 2

SECTION_LABEL_GAP_PX = 22
UNDERLINE_DROP_PX = 6
UNDERLINE_WIDTH_PX = 90

CAPTURED_SLOT_SIZE_PX = 28
CAPTURED_SLOT_GAP_PX = 6
CAPTURED_SLOT_RADIUS_PX = 6
CAPTURED_ICON_SIZE_PX = 20

MOVES_TOP_GAP_PX = 20
MOVE_LINE_HEIGHT = 22

# How many captured-piece slots fit across the panel before wrapping to
# a new row, so a lopsided capture count (e.g. 8 pawns) still stays
# readable instead of running off the edge of the panel.
_SLOTS_PER_ROW = max(
    1,
    (SIDE_PANEL_WIDTH_PX - 2 * PANEL_TEXT_X_PAD) // (CAPTURED_SLOT_SIZE_PX + CAPTURED_SLOT_GAP_PX),
)


class SidePanel:
    def __init__(self, color, panel_x, board_height, skin=DEFAULT_SKIN, username=None, rating=None):
        self._color = color
        self._panel_x = panel_x
        self._board_height = board_height
        self._skin = skin
        # Set by the networked GUI (kfchess.gui.main.build_online_game),
        # from the server's match_found reply -- both None for local
        # (non-online) play, where the WHITE/BLACK label is the only
        # identity shown.
        self._username = username
        self._rating = rating
        self._score = 0
        self._captured = []
        self._moves = []
        self._icons_by_piece_type = {}

    # -- ArbiterObserver interface --

    def on_move_settled(self, color, piece_type, from_position, to_position):
        if color != self._color:
            return
        move_number = len(self._moves) + 1
        origin = algebraic(from_position, self._board_height)
        destination = algebraic(to_position, self._board_height)
        self._moves.append(f"{move_number}. {PIECE_NAMES[piece_type]} {origin}-{destination}")

    def on_piece_captured(self, color, piece_type):
        if color == self._color:
            self._captured.append(piece_type)
        else:
            self._score += PIECE_VALUES[piece_type]

    # -- HUD --

    def draw(self, canvas):
        panel_height = CANVAS_SIZE_PX[1]
        self._draw_background(canvas, panel_height)

        x = self._panel_x + PANEL_TEXT_X_PAD
        self._draw_header(canvas)
        self._draw_score_badge(canvas, x)

        captured_label_y = SCORE_BADGE_TOP_Y + SCORE_BADGE_HEIGHT_PX + SECTION_LABEL_GAP_PX
        row_count = self._draw_captured(canvas, x, captured_label_y)

        icons_top_y = captured_label_y + UNDERLINE_DROP_PX + 10
        moves_label_y = icons_top_y + row_count * (CAPTURED_SLOT_SIZE_PX + CAPTURED_SLOT_GAP_PX) + SECTION_LABEL_GAP_PX
        moves_start_y = moves_label_y + MOVES_TOP_GAP_PX

        self._draw_section_label(canvas, "MOVES", x, moves_label_y)
        visible_count = max(0, (panel_height - moves_start_y) // MOVE_LINE_HEIGHT)
        visible_moves = self._moves[-visible_count:]
        for row, line in enumerate(visible_moves):
            y = moves_start_y + row * MOVE_LINE_HEIGHT
            is_latest = row == len(visible_moves) - 1
            color = TEXT_PRIMARY_COLOR if is_latest else TEXT_SECONDARY_COLOR
            canvas.put_text(line, x, y, 0.5, color=color)

    def _draw_background(self, canvas, panel_height):
        """Vertical gradient fill for the whole panel column, plus a
        thin gold seam along the board-facing edge, so each panel reads
        as its own HUD plate rather than bare background."""
        x0 = self._panel_x
        x1 = self._panel_x + SIDE_PANEL_WIDTH_PX
        channels = canvas.img.shape[2]
        gradient = np.linspace(BG_TOP_COLOR[:channels], BG_BOTTOM_COLOR[:channels], panel_height, dtype=np.float32)
        canvas.img[:panel_height, x0:x1] = gradient[:, np.newaxis, :].astype(canvas.img.dtype)

        edge_x = x1 - 1 if self._panel_x == 0 else x0
        cv2.line(canvas.img, (edge_x, 0), (edge_x, panel_height - 1), BORDER_EDGE_COLOR, 2)

    def _draw_header(self, canvas):
        """A single full-width nameplate card: a color-indicator dot,
        the player's username as the headline (falling back to WHITE/
        BLACK when no username is known, i.e. local non-networked play),
        and -- only once a username is actually shown -- a small WHITE/
        BLACK tag in the card's corner so the color is never ambiguous."""
        card_x = self._panel_x + HEADER_MARGIN_PX
        card_y = HEADER_MARGIN_PX
        card_w = SIDE_PANEL_WIDTH_PX - 2 * HEADER_MARGIN_PX
        card_h = HEADER_HEIGHT_PX - 2 * HEADER_MARGIN_PX
        is_white = self._color == "w"

        _rounded_rect(canvas.img, card_x, card_y, card_w, card_h, HEADER_RADIUS_PX, BADGE_BG_COLOR)
        _rounded_rect(
            canvas.img, card_x, card_y, card_w, card_h, HEADER_RADIUS_PX, ACCENT_DIM_COLOR, thickness=1,
        )

        dot_color = WHITE_DOT_COLOR if is_white else BLACK_DOT_COLOR
        dot_cx = card_x + HEADER_DOT_PAD_PX
        dot_cy = card_y + card_h // 2
        cv2.circle(canvas.img, (dot_cx, dot_cy), HEADER_DOT_RADIUS_PX, dot_color, -1)
        cv2.circle(canvas.img, (dot_cx, dot_cy), HEADER_DOT_RADIUS_PX, ACCENT_DIM_COLOR, 1)

        color_tag = "WHITE" if is_white else "BLACK"
        text_x = dot_cx + HEADER_DOT_RADIUS_PX + 10

        if self._username:
            tag_w, _ = cv2.getTextSize(color_tag, cv2.FONT_HERSHEY_SIMPLEX, HEADER_TAG_FONT_SCALE, 1)[0]
            tag_x = card_x + card_w - tag_w - 10
            canvas.put_text(color_tag, tag_x, card_y + 16, HEADER_TAG_FONT_SCALE, color=ACCENT_COLOR, thickness=1)

            max_width = tag_x - text_x - 8
            display_name = _truncate_to_width(self._username, max_width, 0.58, 2)
            canvas.put_text(display_name, text_x, card_y + 30, 0.58, color=TEXT_PRIMARY_COLOR, thickness=2)

            if self._rating is not None:
                rating_text = f"Rating {self._rating}"
                canvas.put_text(
                    rating_text, text_x, card_y + card_h - 10, HEADER_RATING_FONT_SCALE,
                    color=TEXT_SECONDARY_COLOR, thickness=1,
                )
        else:
            baseline_y = card_y + card_h // 2 + 6
            canvas.put_text(color_tag, text_x, baseline_y, 0.58, color=TEXT_PRIMARY_COLOR, thickness=2)

    def _draw_score_badge(self, canvas, x):
        badge_w = SIDE_PANEL_WIDTH_PX - 2 * PANEL_TEXT_X_PAD
        _rounded_rect(
            canvas.img, x, SCORE_BADGE_TOP_Y, badge_w, SCORE_BADGE_HEIGHT_PX, SCORE_BADGE_RADIUS_PX, BADGE_BG_COLOR
        )
        _rounded_rect(
            canvas.img, x, SCORE_BADGE_TOP_Y, badge_w, SCORE_BADGE_HEIGHT_PX, SCORE_BADGE_RADIUS_PX,
            ACCENT_DIM_COLOR, thickness=SCORE_BADGE_BORDER_PX,
        )
        text_y = SCORE_BADGE_TOP_Y + SCORE_BADGE_HEIGHT_PX - 10
        canvas.put_text("SCORE", x + 10, text_y, 0.42, color=ACCENT_COLOR, thickness=1)
        score_text = str(self._score)
        (text_w, _), _ = cv2.getTextSize(score_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        canvas.put_text(score_text, x + badge_w - text_w - 10, text_y, 0.6, color=TEXT_PRIMARY_COLOR, thickness=2)

    def _draw_section_label(self, canvas, label, x, y):
        canvas.put_text(label, x, y, 0.42, color=ACCENT_COLOR, thickness=1)
        underline_y = y + UNDERLINE_DROP_PX
        cv2.line(canvas.img, (x, underline_y), (x + UNDERLINE_WIDTH_PX, underline_y), ACCENT_DIM_COLOR, 1)

    def _draw_captured(self, canvas, x, label_y):
        self._draw_section_label(canvas, "CAPTURED", x, label_y)
        icons_top_y = label_y + UNDERLINE_DROP_PX + 10

        if not self._captured:
            canvas.put_text("-", x, icons_top_y + CAPTURED_SLOT_SIZE_PX - 10, 0.5, color=TEXT_SECONDARY_COLOR)
            return 1

        for index, piece_type in enumerate(self._captured):
            row, col = divmod(index, _SLOTS_PER_ROW)
            slot_x = x + col * (CAPTURED_SLOT_SIZE_PX + CAPTURED_SLOT_GAP_PX)
            slot_y = icons_top_y + row * (CAPTURED_SLOT_SIZE_PX + CAPTURED_SLOT_GAP_PX)
            _rounded_rect(
                canvas.img, slot_x, slot_y, CAPTURED_SLOT_SIZE_PX, CAPTURED_SLOT_SIZE_PX,
                CAPTURED_SLOT_RADIUS_PX, SLOT_BG_COLOR,
            )
            _rounded_rect(
                canvas.img, slot_x, slot_y, CAPTURED_SLOT_SIZE_PX, CAPTURED_SLOT_SIZE_PX,
                CAPTURED_SLOT_RADIUS_PX, ACCENT_DIM_COLOR, thickness=1,
            )
            inset = (CAPTURED_SLOT_SIZE_PX - CAPTURED_ICON_SIZE_PX) // 2
            self._icon_for(piece_type).draw_on(canvas, slot_x + inset, slot_y + inset)

        return -(-len(self._captured) // _SLOTS_PER_ROW)  # ceil div

    def _icon_for(self, piece_type):
        """Lazily load+cache a small idle-pose icon for one of this
        panel's own captured piece types (all share self._color), so a
        capture list reads as piece icons rather than bare letters."""
        if piece_type not in self._icons_by_piece_type:
            path = assets.sprite_paths(piece_type, self._color, "idle", self._skin)[0]
            icon_size = (CAPTURED_ICON_SIZE_PX, CAPTURED_ICON_SIZE_PX)
            self._icons_by_piece_type[piece_type] = Img().read(path, size=icon_size, keep_aspect=True)
        return self._icons_by_piece_type[piece_type]


def _truncate_to_width(text, max_width, font_scale, thickness):
    """Shortens `text` with a trailing ellipsis until it fits max_width
    px at the given font settings -- a long username otherwise runs off
    the nameplate card into the tag or off the panel edge entirely."""
    if max_width <= 0:
        return ""
    width, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
    if width <= max_width:
        return text
    for cut in range(len(text) - 1, 0, -1):
        candidate = text[:cut] + "..."
        width, _ = cv2.getTextSize(candidate, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
        if width <= max_width:
            return candidate
    return "..."


def _rounded_rect(img, x, y, w, h, radius, color, thickness=-1):
    """Fills or outlines a rounded rectangle by compositing a plus-shape
    of rectangles with quarter-circles at the corners -- cv2 has no
    native rounded-rect primitive, and this is cheap enough to redraw
    every frame for the panel's chips/badges/slots."""
    radius = min(radius, w // 2, h // 2)
    if thickness < 0:
        cv2.rectangle(img, (x + radius, y), (x + w - radius, y + h), color, -1)
        cv2.rectangle(img, (x, y + radius), (x + w, y + h - radius), color, -1)
        for cx, cy in ((x + radius, y + radius), (x + w - radius, y + radius),
                       (x + radius, y + h - radius), (x + w - radius, y + h - radius)):
            cv2.circle(img, (cx, cy), radius, color, -1)
    else:
        cv2.ellipse(img, (x + radius, y + radius), (radius, radius), 180, 0, 90, color, thickness)
        cv2.ellipse(img, (x + w - radius, y + radius), (radius, radius), 270, 0, 90, color, thickness)
        cv2.ellipse(img, (x + radius, y + h - radius), (radius, radius), 90, 0, 90, color, thickness)
        cv2.ellipse(img, (x + w - radius, y + h - radius), (radius, radius), 0, 0, 90, color, thickness)
        cv2.line(img, (x + radius, y), (x + w - radius, y), color, thickness)
        cv2.line(img, (x + radius, y + h), (x + w - radius, y + h), color, thickness)
        cv2.line(img, (x, y + radius), (x, y + h - radius), color, thickness)
        cv2.line(img, (x + w, y + radius), (x + w, y + h - radius), color, thickness)
