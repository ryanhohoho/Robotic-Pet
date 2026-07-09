"""sleeping on the base: motors off, eyes closed, nothing else."""

from .base import Behavior


class SleepBehavior(Behavior):
    def enter(self, **kwargs):
        super().enter(**kwargs)
        self.drive.stop()
        self.eyes.set_state("closed")
