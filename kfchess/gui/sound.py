"""Plays short WAV sound effects for GUI events (click, move, jump,
capture, invalid move, game over).

Uses the stdlib winsound module (Windows only, no extra dependency --
see kfchess.gui.game_loop, which is itself Windows/cv2-driven here)
with SND_ASYNC so playback never blocks a frame. On any other platform,
or if winsound is unavailable, every play_*() call is a silent no-op
rather than raising, so the GUI still runs without sound.

Doubles as an ArbiterObserver (see kfchess.realtime.observers) so it
can be registered via GameEngine.add_observer() alongside SidePanel to
catch capture events without GameLoop having to notice them itself.
"""

from kfchess.gui.config import ASSETS_ROOT
from kfchess.realtime.observers import ArbiterObserver

try:
    import winsound
except ImportError:
    winsound = None

SOUNDS_DIR = ASSETS_ROOT / "sounds"

CLICK = "click.wav"
MOVE = "move.wav"
JUMP = "jump.wav"
CAPTURE = "capture.wav"
INVALID = "invalid.wav"
GAME_OVER = "game_over.wav"


class SoundPlayer(ArbiterObserver):
    def __init__(self, enabled=True):
        self._enabled = enabled and winsound is not None

    def play_click(self):
        self._play(CLICK)

    def play_move(self):
        self._play(MOVE)

    def play_jump(self):
        self._play(JUMP)

    def play_capture(self):
        self._play(CAPTURE)

    def play_invalid(self):
        self._play(INVALID)

    def play_game_over(self):
        self._play(GAME_OVER)

    # -- ArbiterObserver interface --

    def on_move_settled(self, color, piece_type, from_position, to_position):
        pass

    def on_piece_captured(self, color, piece_type):
        self.play_capture()

    def _play(self, filename):
        if not self._enabled:
            return
        path = SOUNDS_DIR / filename
        if not path.exists():
            return
        winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
