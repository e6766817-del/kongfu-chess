"""Lazily loads and caches each piece type's sprite frames + state config,
so every on-board piece of the same (kind, color, skin) shares one set of
already-decoded Img frames instead of re-reading files per instance.
"""

from kfchess.gui import assets
from kfchess.gui.config import DEFAULT_SKIN, SPRITE_SIZE_PX
from kfchess.gui.img import Img


class SpriteSet:
    """All animation data for one (kind, color) under a given skin.

    self._states: dict[str, tuple[list[Img], dict]]
        state name -> (ordered list of 5 Img frames, parsed config.json)
    """

    def __init__(self, kind, color, skin=DEFAULT_SKIN):
        self._kind = kind
        self._color = color
        self._skin = skin
        self._states = {}

    def frames(self, state):
        """Return (list[Img], config_dict) for `state`, loading + caching on first use."""
        if state not in self._states:
            paths = assets.sprite_paths(self._kind, self._color, state, self._skin)
            frames = [
                Img().read(path, size=SPRITE_SIZE_PX, keep_aspect=True) for path in paths
            ]
            config = assets.state_config(self._kind, self._color, state, self._skin)
            self._states[state] = (frames, config)
        return self._states[state]


class SpriteSetCache:
    """Keeps one SpriteSet per (kind, color) so images are decoded once
    for the whole game, regardless of how many pieces of that type exist.
    """

    def __init__(self, skin=DEFAULT_SKIN):
        self._skin = skin
        self._sets = {}

    def get(self, kind, color):
        key = (kind, color)
        if key not in self._sets:
            self._sets[key] = SpriteSet(kind, color, self._skin)
        return self._sets[key]
