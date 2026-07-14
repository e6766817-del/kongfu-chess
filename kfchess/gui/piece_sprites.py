"""Lazily loads and caches each piece type's sprite frames + state config,
so every on-board piece of the same (kind, color, skin) shares one set of
already-decoded Img frames instead of re-reading files per instance.
"""

from kfchess.gui.config import DEFAULT_SKIN


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
        # TODO: on cache miss, use kfchess.gui.assets.sprite_paths/state_config
        # to build Img().read(path) for each frame and store in self._states.
        raise NotImplementedError


class SpriteSetCache:
    """Keeps one SpriteSet per (kind, color) so images are decoded once
    for the whole game, regardless of how many pieces of that type exist.
    """

    def __init__(self, skin=DEFAULT_SKIN):
        self._skin = skin
        self._sets = {}

    def get(self, kind, color):
        # TODO: return self._sets.setdefault((kind, color), SpriteSet(kind, color, self._skin))
        raise NotImplementedError
