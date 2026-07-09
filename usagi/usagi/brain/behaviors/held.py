"""picked up: motors hard-stopped, worried eyes until put back down."""

from .base import Behavior


class HeldBehavior(Behavior):
    def enter(self, **kwargs):
        super().enter(**kwargs)
        self.drive.stop()
        self.eyes.set_state("react", emotion="worried")
