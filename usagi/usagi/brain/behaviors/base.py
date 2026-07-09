"""behavior interface. behaviors only ever talk to drive and eyes."""

from ...events import Event


class Behavior:
    def __init__(self, drive, eyes, cfg: dict):
        self.drive = drive
        self.eyes = eyes
        self.cfg = cfg
        self.done = False   # reacting-style behaviors flip this when finished

    def enter(self, **kwargs):
        self.done = False

    def tick(self, dt: float):
        pass

    def handle_event(self, ev: Event):
        pass

    def exit(self):
        pass
