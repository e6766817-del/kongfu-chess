"""Per-piece client-side animation state machine.

The backend (kfchess.engine.GameEngine) exposes no in-flight/pixel
position -- Board only changes atomically on arrival. So this state
machine is driven entirely from this GUI driver's side:

  - idle:        loops forever until start_move()/start_jump() is called.
  - move:        starts when GameEngine.request_move() is accepted; runs
                  until `arrival_time_ms` (from the returned MoveResult)
                  is reached, then advances to its config's
                  next_state_when_finished (normally "long_rest").
  - jump:        starts when GameEngine.request_jump() is accepted; runs
                  once (its config.json's is_loop is False) then advances
                  to next_state_when_finished (normally "short_rest").
  - short_rest / long_rest: play once per their own config.json, then
                  advance to next_state_when_finished (normally "idle").

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
        self._move_arrival_time_ms = None

    def start_move(self, arrival_time_ms):
        """Called when GameEngine.request_move(...) is accepted."""
        # TODO: switch to MOVE state, reset frame_index/elapsed_ms,
        # remember arrival_time_ms so advance() knows when to transition.
        raise NotImplementedError

    def start_jump(self):
        """Called when GameEngine.request_jump(...) is accepted."""
        # TODO: switch to JUMP state, reset frame_index/elapsed_ms.
        raise NotImplementedError

    def advance(self, dt_ms, now_ms=None):
        """Progress the current state's animation by dt_ms.

        TODO:
          - accumulate elapsed_ms, advance frame_index per the current
            state's frames_per_sec (from sprite_set.frames(state_name)[1])
          - if MOVE: transition once now_ms >= self._move_arrival_time_ms
          - else if not is_loop and the frame sequence has finished:
            transition to config's next_state_when_finished
          - if is_loop: wrap frame_index instead of transitioning
        """
        raise NotImplementedError

    def current_frame(self):
        """Return the Img to draw right now for this piece."""
        # TODO: return sprite_set.frames(self.state_name)[0][self.frame_index]
        raise NotImplementedError


assert set(PIECE_STATES) == {IDLE, MOVE, JUMP, SHORT_REST, LONG_REST}
