"""null eye driver.

v2 hardware dropped the OLED displays -- the face is painted and static.
this keeps the same set_state/start/stop interface the brain and behaviors
expect, but drives no hardware. it just records and logs the requested
state so reactions still "run" and tests can inspect them.

if you ever add an expressive output later (rgb led, buzzer, a screen),
implement it behind this same interface and nothing upstream has to change."""

import logging

log = logging.getLogger("usagi.eyes")


class NullEyes:
    def __init__(self, cfg: dict | None = None):
        self.state = "closed"
        self.params: dict = {}

    def set_state(self, state: str, **params):
        """record the requested expression. non-blocking, no hardware."""
        self.state = state
        self.params = params
        log.debug("eyes -> %s %s", state, params)

    def start(self):
        # nothing to spin up without a display
        pass

    def stop(self):
        pass


# keep the old name importable so callers don't care which driver they got
Eyes = NullEyes
