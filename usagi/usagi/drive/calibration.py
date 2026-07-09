"""global calibration layer.

routines and behaviors are authored with *relative* motor values and
timings. the numbers here scale those at runtime, so a routine that looks
right in simulation can be corrected on real hardware by editing the
`calibration` block in config.yaml -- never the routine itself.

- speed_scale     multiplies the forward (common) component of a move
- turn_scale      multiplies the differential (turning) component
- left/right_trim per-wheel correction for motor mismatch / drift
- duration_scale  stretches or compresses routine step timing

CalibratedDrive wraps any drive (real or simulated) and applies the wheel
math transparently, so behaviors keep calling move/forward/turn as normal.
"""

from dataclasses import dataclass


@dataclass
class Calibration:
    speed_scale: float = 1.0
    turn_scale: float = 1.0
    duration_scale: float = 1.0
    left_trim: float = 1.0
    right_trim: float = 1.0

    @classmethod
    def from_cfg(cls, cfg: dict) -> "Calibration":
        c = cfg.get("calibration", {}) or {}
        return cls(
            speed_scale=float(c.get("speed_scale", 1.0)),
            turn_scale=float(c.get("turn_scale", 1.0)),
            duration_scale=float(c.get("duration_scale", 1.0)),
            left_trim=float(c.get("left_trim", 1.0)),
            right_trim=float(c.get("right_trim", 1.0)),
        )

    def wheels(self, left: float, right: float) -> tuple[float, float]:
        """apply forward/turn scaling and per-wheel trim.
        decomposes into common (drive) + differential (turn) so the two can
        be scaled independently, then recombines and trims each wheel."""
        common = (left + right) / 2.0
        diff = (left - right) / 2.0
        common *= self.speed_scale
        diff *= self.turn_scale
        l = (common + diff) * self.left_trim
        r = (common - diff) * self.right_trim
        return l, r

    def duration(self, seconds: float) -> float:
        return seconds * self.duration_scale


class CalibratedDrive:
    """decorator over a drive object. same interface, calibrated output."""

    def __init__(self, inner, cal: Calibration):
        self._inner = inner
        self._cal = cal

    def move(self, left: float, right: float):
        l, r = self._cal.wheels(left, right)
        self._inner.move(l, r)

    def forward(self, speed: float = 0.5):
        self.move(speed, speed)

    def backward(self, speed: float = 0.5):
        self.move(-speed, -speed)

    def turn(self, rate: float):
        self.move(rate, -rate)

    def stop(self):
        # bypass scaling so stop is always a true stop
        self._inner.move(0.0, 0.0)

    def close(self):
        self._inner.close()
