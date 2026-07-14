"""Resolves piece/board asset paths and reads each state's config.json.

Layout on disk (see assets/pieces1/, assets/pieces2/):
    assets/<skin>/<KIND><COLOR>/states/<state>/config.json
    assets/<skin>/<KIND><COLOR>/states/<state>/sprites/1.png .. 5.png

<KIND> is one of K, Q, R, B, N, P (kfchess.model.piece.PIECE_TYPES) and
<COLOR> is W or B (kfchess.model.piece.COLORS, upper-cased).
"""

from kfchess.gui.config import ASSETS_ROOT, DEFAULT_SKIN


def board_image_path(skin=DEFAULT_SKIN):
    """Path to the board background image (board.png)."""
    # TODO: return ASSETS_ROOT / "board.png" (skin currently unused --
    # only one board image exists today, kept as a param for symmetry).
    raise NotImplementedError


def piece_folder(kind, color, skin=DEFAULT_SKIN):
    """Path to a piece's asset folder, e.g. kind="P", color="w" -> assets/pieces1/PW."""
    # TODO: ASSETS_ROOT / skin / f"{kind}{color.upper()}"
    raise NotImplementedError


def sprite_paths(kind, color, state, skin=DEFAULT_SKIN):
    """Sorted list of the state's frame image paths (1.png .. 5.png)."""
    # TODO: sorted(piece_folder(...) / "states" / state / "sprites" glob, by frame number)
    raise NotImplementedError


def state_config(kind, color, state, skin=DEFAULT_SKIN):
    """Parsed config.json for one piece state: physics + graphics dict."""
    # TODO: json.load(piece_folder(...) / "states" / state / "config.json")
    raise NotImplementedError
