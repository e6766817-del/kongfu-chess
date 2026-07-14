"""Per-piece client-side animation state machine.

The backend (kfchess.engine.GameEngine) exposes no in-flight/pixel
position -- Board only changes atomically on arrival. So this state
machine is driven entirely from this GUI driver's side:

  - idle:        loops forever (is_loop=True) until start_move()/
                  start_jump() is called from a mouse event.
  - move:        starts when GameEngine.request_move() is accepted;
                  also loops (is_loop=True) since its natural duration
                  varies per move -- GameLoop calls on_settled() once
                  GameEngine.is_locked() reports the piece's origin
                  cell has been released, which advances to the
                  config's next_state_when_finished (normally
                  "long_rest").
  - jump/short_rest/long_rest: each is_loop=False in its config.json,
                  so advance() alone finishes the state's own frame
                  sequence and transitions to next_state_when_finished
                  without any external signal.

Frame timing within a state comes from that state's config.json
("graphics": {"frames_per_sec", "is_loop"}); state-to-state transitions
come from "physics": {"next_state_when_finished"}. There is no
"captured" sprite state -- captured pieces are removed outright by
whatever holds the on-screen piece list, not animated out.
"""

from kfchess.gui.config import PIECE_STATES

IDLE = "idle"
MOVE = "move"
JUMP = "jump"
SHORT_REST = "short_rest"
LONG_REST = "long_rest"


class PieceAnimationState:
    def __init__(self, sprite_set):
        self._sprite_set = sprite_set
        self.state_name = IDLE
        self.frame_index = 0
        self.elapsed_ms = 0

    def _enter(self, state_name):
        self.state_name = state_name
        self.frame_index = 0
        self.elapsed_ms = 0

    def start_move(self):
        """Called when GameEngine.request_move(...) is accepted."""
        self._enter(MOVE)

    def start_jump(self):
        """Called when GameEngine.request_jump(...) is accepted."""
        self._enter(JUMP)

    def on_settled(self):
        """Called by GameLoop once a MOVE piece's origin cell is no
        longer locked (the move arrived, was captured mid-path, etc).
        No-op outside MOVE, since the other non-loop states finish on
        their own via advance()."""
        if self.state_name != MOVE:
            return
        _frames, config = self._sprite_set.frames(self.state_name)
        self._enter(config["physics"]["next_state_when_finished"])

    def advance(self, dt_ms):
        """Progress the current state's animation by dt_ms."""
        frames, config = self._sprite_set.frames(self.state_name)
        fps = config["graphics"]["frames_per_sec"]
        is_loop = config["graphics"]["is_loop"]
        ms_per_frame = 1000 / fps

        self.elapsed_ms += dt_ms
        total_frames = len(frames)

        if is_loop:
            self.frame_index = int(self.elapsed_ms // ms_per_frame) % total_frames
            return

        if self.elapsed_ms >= total_frames * ms_per_frame:
            next_state = config["physics"]["next_state_when_finished"]
            self._enter(next_state)
            return

        self.frame_index = min(int(self.elapsed_ms // ms_per_frame), total_frames - 1)

    def current_frame(self):
        """Return the Img to draw right now for this piece."""
        frames, _config = self._sprite_set.frames(self.state_name)
        return frames[self.frame_index]


assert set(PIECE_STATES) == {IDLE, MOVE, JUMP, SHORT_REST, LONG_REST}
