"""scripted reaction routines, data not code.

a routine is a list of keyframes:
  (duration_s, (left, right) | None, eye_state, eye_params)
None for drive means leave motors stopped. add new routines by adding data.
"""

from ...drive.calibration import Calibration
from .base import Behavior

ROUTINES: dict[str, list] = {
    # heard something: freeze, look both ways
    "sound": [
        (0.4, None, "react", {"emotion": "surprised"}),
        (0.8, None, "look", {"direction": -0.8}),
        (0.8, None, "look", {"direction": 0.8}),
        (0.5, None, "idle", {}),
    ],
    # saw a face: happy wiggle
    "face": [
        (0.3, None, "react", {"emotion": "happy"}),
        (0.35, (0.6, -0.6), "react", {"emotion": "happy"}),
        (0.35, (-0.6, 0.6), "react", {"emotion": "happy"}),
        (0.35, (0.6, -0.6), "react", {"emotion": "happy"}),
        (0.5, None, "react", {"emotion": "happy"}),
    ],
    # got bumped while parked: startle, back off, settle
    "bump": [
        (0.3, None, "react", {"emotion": "surprised"}),
        (0.6, (-0.4, -0.4), "react", {"emotion": "worried"}),
        (1.0, None, "react", {"emotion": "worried"}),
        (0.5, None, "idle", {}),
    ],
}


class ReactBehavior(Behavior):
    def enter(self, routine: str = "sound", **kwargs):
        super().enter()
        self._frames = ROUTINES.get(routine, ROUTINES["sound"])
        self._cal = Calibration.from_cfg(self.cfg)
        self._index = -1
        self._left = 0.0
        self._advance()

    def _advance(self):
        self._index += 1
        if self._index >= len(self._frames):
            self.drive.stop()
            self.done = True
            return
        duration, motors, eye_state, eye_params = self._frames[self._index]
        # duration_scale lets you stretch/compress routine timing globally
        self._left = self._cal.duration(duration)
        if motors is None:
            self.drive.stop()
        else:
            self.drive.move(*motors)
        self.eyes.set_state(eye_state, **eye_params)

    def tick(self, dt: float):
        if self.done:
            return
        self._left -= dt
        if self._left <= 0:
            self._advance()

    def exit(self):
        self.drive.stop()
