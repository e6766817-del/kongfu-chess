"""Resolves piece/board asset paths and reads each state's config.json.

Layout on disk (see assets/pieces1/, assets/pieces2/):
    assets/<skin>/<KIND><COLOR>/states/<state>/config.json
    assets/<skin>/<KIND><COLOR>/states/<state>/sprites/1.png .. 5.png

<KIND> is one of K, Q, R, B, N, P (kfchess.model.piece.PIECE_TYPES) and
<COLOR> is W or B (kfchess.model.piece.COLORS, upper-cased).
"""

import json
import re

from kfchess.gui.config import ASSETS_ROOT, AVAILABLE_SKINS, DEFAULT_SKIN

# Some downloaded asset copies (notably pieces2) contain Windows
# "duplicate download" filenames alongside the canonical ones, e.g.
# "4.png" missing but "4 (42).png" present, or "config.json" missing
# but "config (58).json" present. Match both so a frame or config file
# is never silently dropped just because its canonical filename is
# missing.
_FRAME_NAME_RE = re.compile(r"^(\d+)(?:\s*\(\d+\))?$")
_CONFIG_NAME_RE = re.compile(r"^config(?:\s*\(\d+\))?$")


def _check_skin(skin):
    if skin not in AVAILABLE_SKINS:
        raise ValueError(f"Unknown skin {skin!r}; available: {AVAILABLE_SKINS}")


def board_image_path(skin=DEFAULT_SKIN):
    """Path to the board background image (board.png, shared by all skins)."""
    _check_skin(skin)
    return ASSETS_ROOT / "board.png"


def piece_folder(kind, color, skin=DEFAULT_SKIN):
    """Path to a piece's asset folder, e.g. kind="P", color="w" -> assets/pieces1/PW."""
    _check_skin(skin)
    return ASSETS_ROOT / skin / f"{kind}{color.upper()}"


def sprite_paths(kind, color, state, skin=DEFAULT_SKIN):
    """Sorted list of the state's frame image paths (1.png .. 5.png),
    one per frame number -- prefers the canonical "N.png" over a
    "N (dup).png" duplicate when both exist for the same frame number."""
    sprites_dir = piece_folder(kind, color, skin) / "states" / state / "sprites"
    path_by_frame_number = {}
    for path in sprites_dir.glob("*.png"):
        match = _FRAME_NAME_RE.match(path.stem)
        if match is None:
            continue
        frame_number = int(match.group(1))
        is_canonical = path.stem == match.group(1)
        if is_canonical or frame_number not in path_by_frame_number:
            path_by_frame_number[frame_number] = path
    return [path_by_frame_number[number] for number in sorted(path_by_frame_number)]


def state_config(kind, color, state, skin=DEFAULT_SKIN):
    """Parsed config.json for one piece state: physics + graphics dict.

    Prefers the canonical "config.json" over a "config (dup).json"
    duplicate when both exist.
    """
    state_dir = piece_folder(kind, color, skin) / "states" / state
    candidates = [path for path in state_dir.glob("config*.json") if _CONFIG_NAME_RE.match(path.stem)]
    if not candidates:
        raise FileNotFoundError(f"No config.json found in {state_dir}")
    config_path = min(candidates, key=lambda path: path.stem != "config")
    with open(config_path, encoding="utf-8") as handle:
        return json.load(handle)
