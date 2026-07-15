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
                  "long_rest"). While in this state, current_pixel()
                  slides the sprite from the origin cell to the
                  destination cell over exactly Controller's reported
                  arrival_time_ms window, so the sprite lands the same
                  moment the engine actually unlocks the cell -- see
                  start_move().
  - jump:        is_loop=False, so advance() alone finishes its frame
                  sequence and transitions to next_state_when_finished
                  ("short_rest") without any external signal -- purely
                  cosmetic air-time.
  - short_rest/long_rest: is_loop=False, but these states are the real
                  enforced cooldown (RealTimeArbiter.RESTING), which
                  doesn't necessarily finish in exactly this state's own
                  frame_count/frames_per_sec window -- per-piece-kind
                  sprite packs don't all have the same frame count (e.g.
                  the rook's rest states have 4 frames, not 5). So
                  advance() plays through the frames once and then holds
                  on the last frame instead of auto-transitioning; only
                  GameLoop calling on_rest_settled(), once
                  GameEngine.is_locked() reports the piece's own cell
                  free again, actually advances past it -- same
                  polling pattern as MOVE's on_settled().

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
        self._move_origin_px = None
        self._move_destination_px = None
        self._move_duration_ms = 0

    def _enter(self, state_name):
        self.state_name = state_name
        self.frame_index = 0
        self.elapsed_ms = 0

    def start_move(self, origin_px, destination_px, duration_ms):
        """Called when GameEngine.request_move(...) is accepted.

        origin_px/destination_px are the (x, y) top-left pixels of the
        from/to cells; duration_ms is result.arrival_time_ms minus the
        engine clock at accept time -- the exact real-time window
        GameEngine will keep this cell locked for (itself derived from
        RealTimeArbiter.PIECE_SPEED_M_PER_SEC, not a guess). current_pixel()
        interpolates across that window so the sprite lands on
        destination_px at the same moment the engine actually unlocks the
        cell, rather than teleporting there.
        """
        self._enter(MOVE)
        self._move_origin_px = origin_px
        self._move_destination_px = destination_px
        self._move_duration_ms = duration_ms

    def start_jump(self):
        """Called when GameEngine.request_jump(...) is accepted."""
        self._enter(JUMP)

    def on_settled(self):
        """Called by GameLoop once a MOVE piece's origin cell is no
        longer locked (the move arrived, was captured mid-path, etc).
        No-op outside MOVE, since JUMP finishes on its own via advance()
        and SHORT_REST/LONG_REST wait for on_rest_settled() instead."""
        if self.state_name != MOVE:
            return
        _frames, config = self._sprite_set.frames(self.state_name)
        self._enter(config["physics"]["next_state_when_finished"])

    def on_rest_settled(self):
        """Called by GameLoop once a SHORT_REST/LONG_REST piece's own
        cell is no longer locked by GameEngine -- i.e. the real cooldown
        RealTimeArbiter enforces, not just this state's own frame count,
        which can finish earlier or later depending on the piece kind's
        sprite pack. No-op outside SHORT_REST/LONG_REST."""
        if self.state_name not in (SHORT_REST, LONG_REST):
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
            if self.state_name in (SHORT_REST, LONG_REST):
                self.frame_index = total_frames - 1  # hold here for on_rest_settled()
                return
            next_state = config["physics"]["next_state_when_finished"]
            self._enter(next_state)
            return

        self.frame_index = min(int(self.elapsed_ms // ms_per_frame), total_frames - 1)

    def current_frame(self):
        """Return the Img to draw right now for this piece."""
        frames, _config = self._sprite_set.frames(self.state_name)
        return frames[self.frame_index]

    def current_pixel(self):
        """(x, y) to draw current_frame() at right now, or None if this
        piece isn't mid-slide (renderer should fall back to its logical
        cell's pixel). Linearly interpolates origin_px -> destination_px
        over _move_duration_ms -- see start_move()."""
        if self.state_name != MOVE or self._move_origin_px is None:
            return None
        if self._move_duration_ms <= 0:
            return self._move_destination_px
        fraction = min(1.0, self.elapsed_ms / self._move_duration_ms)
        origin_x, origin_y = self._move_origin_px
        destination_x, destination_y = self._move_destination_px
        x = origin_x + (destination_x - origin_x) * fraction
        y = origin_y + (destination_y - origin_y) * fraction
        return x, y


assert set(PIECE_STATES) == {IDLE, MOVE, JUMP, SHORT_REST, LONG_REST}
