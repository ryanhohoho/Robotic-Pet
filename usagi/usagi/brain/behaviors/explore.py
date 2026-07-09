"""wander with obstacle avoidance. forward cruise with occasional
gentle turns; obstacle or bump triggers a timed back-and-turn maneuver."""

import random

from ...events import Event, EventType
from .base import Behavior

_CRUISE = 0.45
_TURN = 0.5


class ExploreBehavior(Behavior):
    def enter(self, **kwargs):
        super().enter(**kwargs)
        self.eyes.set_state("idle")
        self._mode = "cruise"          # cruise | turning | backing | avoid_turn
        self._mode_left = self._new_cruise_time()

    def _new_cruise_time(self) -> float:
        return random.uniform(2.0, 5.0)

    def tick(self, dt: float):
        self._mode_left -= dt

        if self._mode == "cruise":
            self.drive.forward(_CRUISE)
            if self._mode_left <= 0:
                # wander: pick a random gentle turn
                self._mode = "turning"
                self._turn_dir = random.choice((-1, 1))
                self._mode_left = random.uniform(0.3, 0.9)
                self.eyes.set_state("look", direction=0.7 * self._turn_dir)

        elif self._mode == "turning":
            self.drive.move(_CRUISE + _TURN * self._turn_dir, _CRUISE - _TURN * self._turn_dir)
            if self._mode_left <= 0:
                self._to_cruise()

        elif self._mode == "backing":
            self.drive.backward(0.4)
            if self._mode_left <= 0:
                self._mode = "avoid_turn"
                self._mode_left = random.uniform(0.6, 1.0)

        elif self._mode == "avoid_turn":
            self.drive.turn(0.6 * self._turn_dir)
            if self._mode_left <= 0:
                self._to_cruise()

    def _to_cruise(self):
        self._mode = "cruise"
        self._mode_left = self._new_cruise_time()
        self.eyes.set_state("idle")

    def _start_avoid(self):
        self._mode = "backing"
        self._mode_left = 0.6
        self._turn_dir = random.choice((-1, 1))
        self.eyes.set_state("react", emotion="surprised")

    def handle_event(self, ev: Event):
        if ev.type in (EventType.OBSTACLE_NEAR, EventType.BUMP):
            self._start_avoid()

    def exit(self):
        self.drive.stop()
