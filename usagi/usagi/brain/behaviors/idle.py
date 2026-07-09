"""awake but parked: no movement, eyes drift and auto-blink,
glance toward motion."""

from ...events import Event, EventType
from .base import Behavior


class IdleBehavior(Behavior):
    def enter(self, **kwargs):
        super().enter(**kwargs)
        self.drive.stop()
        self.eyes.set_state("idle")
        self._glance_timer = 0.0

    def tick(self, dt: float):
        # return to idle drift after a glance
        if self._glance_timer > 0:
            self._glance_timer -= dt
            if self._glance_timer <= 0:
                self.eyes.set_state("idle")

    def handle_event(self, ev: Event):
        if ev.type == EventType.MOTION_DETECTED:
            # something moved, glance around for a moment
            self.eyes.set_state("look", direction=0.6)
            self._glance_timer = 1.5
