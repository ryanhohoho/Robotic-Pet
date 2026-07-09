"""behavior state machine using the `transitions` library.

states:
  sleeping  -- on base, motors off, eyes closed
  idle      -- awake, no movement, ambient eye animation
  exploring -- wander with obstacle avoidance
  reacting  -- short scripted routine keyed by stimulus
  held      -- picked up, motors hard-stopped

priority events (PICKED_UP) transition immediately from any state.
everything else routes through the current behavior or a trigger."""

import queue
import time

from transitions import Machine

from ..events import Event, EventType
from .behaviors import (
    ExploreBehavior,
    HeldBehavior,
    IdleBehavior,
    ReactBehavior,
    SleepBehavior,
)

STATES = ["sleeping", "idle", "exploring", "reacting", "held"]

TRANSITIONS = [
    {"trigger": "wake", "source": "sleeping", "dest": "idle"},
    {"trigger": "bored", "source": "idle", "dest": "exploring"},
    {"trigger": "stimulus", "source": ["idle", "exploring"], "dest": "reacting"},
    {"trigger": "finished", "source": "reacting", "dest": "idle"},
    {"trigger": "picked_up", "source": "*", "dest": "held"},
    {"trigger": "put_down", "source": "held", "dest": "idle"},
    {"trigger": "sleep", "source": "*", "dest": "sleeping"},
]

# which react routine a stimulus maps to
_STIMULUS_ROUTINE = {
    EventType.LOUD_SOUND: "sound",
    EventType.FACE_DETECTED: "face",
    EventType.BUMP: "bump",
}


class Brain:
    def __init__(self, cfg: dict, event_queue, drive, eyes, on_transition=None):
        b = cfg.get("brain", {})
        self._tick = 1.0 / float(b.get("tick_hz", 20))
        self._idle_timeout = float(b.get("idle_timeout_s", 30))
        self._queue = event_queue
        self._drive = drive
        self._eyes = eyes
        # optional observer(prev_state, new_state) -- used by sim/tracing, off in prod
        self._on_transition = on_transition
        self._behaviors = {
            "sleeping": SleepBehavior(drive, eyes, cfg),
            "idle": IdleBehavior(drive, eyes, cfg),
            "exploring": ExploreBehavior(drive, eyes, cfg),
            "reacting": ReactBehavior(drive, eyes, cfg),
            "held": HeldBehavior(drive, eyes, cfg),
        }
        self._behavior = None
        self._enter_kwargs: dict = {}
        self._state_since = time.monotonic()
        self._running = False

        self.machine = Machine(
            model=self,
            states=STATES,
            transitions=TRANSITIONS,
            initial="sleeping",
            ignore_invalid_triggers=True,   # e.g. put_down while not held is a no-op
            after_state_change="_on_state_change",
        )
        self._on_state_change()

    # -- state plumbing --------------------------------------------------

    def _on_state_change(self):
        prev = self._behavior
        if prev is not None:
            prev.exit()
        self._state_since = time.monotonic()
        new_behavior = self._behaviors[self.state]
        if self._on_transition is not None:
            # prev is a behavior object on real transitions, None on first init
            prev_name = getattr(prev, "_state_name", None)
            self._on_transition(prev_name, self.state)
        new_behavior._state_name = self.state
        self._behavior = new_behavior
        self._behavior.enter(**self._enter_kwargs)
        self._enter_kwargs = {}

    def _dispatch(self, ev: Event):
        # priority: being picked up overrides everything, stop motors first
        if ev.type == EventType.PICKED_UP:
            self._drive.stop()
            self.picked_up()
            return
        if ev.type == EventType.PUT_DOWN:
            self.put_down()
            return
        if ev.type == EventType.SHUTDOWN:
            self._running = False
            return

        if self.state == "sleeping":
            # only a loud sound wakes it up
            if ev.type == EventType.LOUD_SOUND:
                self.wake()
            return

        # bump while exploring is handled by the avoid maneuver, not a routine
        if ev.type == EventType.BUMP and self.state == "exploring":
            self._behavior.handle_event(ev)
            return

        routine = _STIMULUS_ROUTINE.get(ev.type)
        if routine and self.state in ("idle", "exploring"):
            self._enter_kwargs = {"routine": routine}
            self.stimulus()
            return

        # everything else (motion, obstacle) goes to the current behavior
        self._behavior.handle_event(ev)

    # -- main loop --------------------------------------------------------

    def run(self):
        """blocking main loop, exits on SHUTDOWN event"""
        self._running = True
        last = time.monotonic()
        while self._running:
            # drain everything that arrived since last tick
            while True:
                try:
                    ev = self._queue.get_nowait()
                except queue.Empty:
                    break
                self._dispatch(ev)

            now = time.monotonic()
            dt, last = now - last, now

            self._behavior.tick(dt)

            # timers
            if self.state == "idle" and now - self._state_since >= self._idle_timeout:
                self.bored()
            elif self.state == "reacting" and self._behavior.done:
                self.finished()

            time.sleep(self._tick)

        self._drive.stop()
