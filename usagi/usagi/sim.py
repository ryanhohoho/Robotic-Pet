"""simulation mode -- run the whole robot brain on any computer, no hardware.

it uses the real Brain, real behaviors, real calibration and the real state
machine. only the leaf hardware is faked:
- SimDrive prints/records every wheel command (calibrated values, so you see
  exactly what the motors would get)
- NullEyes is already hardware-free
- sensors are replaced by a scripted timeline that injects Events

because it runs the real Brain + Calibration, a routine that behaves well
here will behave the same on hardware up to the calibration knobs in
config.yaml. tune routines here, then correct real turns/speed/timing by
editing the `calibration` block -- no routine rewrite.

usage:
  python -m usagi.sim                 # default demo timeline
  python -m usagi.sim --timeline face_hello
  python -m usagi.sim --speed 4       # run 4x faster than real time
"""

import argparse
import queue
import threading
import time

from . import config
from .brain.state_machine import Brain
from .drive.calibration import CalibratedDrive, Calibration
from .events import Event, EventType
from .face.eyes import NullEyes


class SimDrive:
    """fake motors: records and prints wheel commands instead of driving."""

    def __init__(self, printer):
        self._print = printer
        self.last = (0.0, 0.0)
        self.log: list[tuple[float, float, float]] = []  # (t, left, right)

    def move(self, left, right):
        left, right = round(left, 3), round(right, 3)
        if (left, right) != self.last:
            self._print(f"    motors L={left:+.2f} R={right:+.2f} {_wheel_hint(left, right)}")
            self.last = (left, right)
        self.log.append((time.monotonic(), left, right))

    def forward(self, s=0.5): self.move(s, s)
    def backward(self, s=0.5): self.move(-s, -s)
    def turn(self, r): self.move(r, -r)
    def stop(self): self.move(0.0, 0.0)
    def close(self): self.stop()


def _wheel_hint(l, r) -> str:
    if l == 0 and r == 0:
        return "(stop)"
    if abs(l - r) < 0.05:
        return "(forward)" if l > 0 else "(reverse)"
    if l > r:
        return "(turn right)"
    return "(turn left)"


# scripted stimulus timelines: (delay_s_after_previous, EventType, data)
TIMELINES = {
    "demo": [
        (1.0, EventType.LOUD_SOUND, {"level_db": -8}),   # wake
        (2.0, EventType.FACE_DETECTED, {"x_offset": 0.3}),  # happy react
        (4.0, EventType.MOTION_DETECTED, {"ratio": 0.05}),
        (2.0, EventType.OBSTACLE_NEAR, {"density": 0.4}),
        (3.0, EventType.BUMP, {"g": 2.4}),
        (2.0, EventType.PICKED_UP, {}),
        (3.0, EventType.PUT_DOWN, {}),
        (2.0, EventType.SHUTDOWN, {}),
    ],
    "face_hello": [
        (1.0, EventType.LOUD_SOUND, {"level_db": -8}),
        (1.5, EventType.FACE_DETECTED, {"x_offset": 0.0}),
        (4.0, EventType.SHUTDOWN, {}),
    ],
    "bump_recovery": [
        (1.0, EventType.LOUD_SOUND, {"level_db": -8}),
        (0.5, None, None),   # let it get bored -> exploring (see --idle-timeout)
        (6.0, EventType.OBSTACLE_NEAR, {"density": 0.5}),
        (3.0, EventType.BUMP, {"g": 2.5}),
        (4.0, EventType.SHUTDOWN, {}),
    ],
}


def _feed(events: queue.Queue, timeline, speed: float, printer):
    for delay, etype, data in timeline:
        time.sleep(delay / speed)
        if etype is None:
            continue
        printer(f">>> stimulus: {etype.name} {data or ''}")
        events.put(Event(etype, data or {}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", default="demo", choices=list(TIMELINES))
    ap.add_argument("--speed", type=float, default=1.0, help="time multiplier")
    ap.add_argument("--config", default=None)
    ap.add_argument("--idle-timeout", type=float, default=None,
                    help="override brain.idle_timeout_s for the sim")
    args = ap.parse_args()

    cfg = config.load(args.config)
    for w in config.validate(cfg):
        print(f"[config warning] {w}")
    if args.idle_timeout is not None:
        cfg.setdefault("brain", {})["idle_timeout_s"] = args.idle_timeout

    lock = threading.Lock()

    def printer(msg):
        with lock:
            print(msg)

    def on_transition(prev, new):
        printer(f"[state] {prev or 'init'} -> {new.upper()}")

    events: queue.Queue = queue.Queue()
    drive = CalibratedDrive(SimDrive(printer), Calibration.from_cfg(cfg))
    eyes = _TracingEyes(printer)
    brain = Brain(cfg, events, drive, eyes, on_transition=on_transition)

    cal = cfg.get("calibration", {})
    printer(f"--- usagi sim | timeline={args.timeline} speed={args.speed}x ---")
    printer(f"--- calibration: {cal} ---\n")

    feeder = threading.Thread(
        target=_feed, args=(events, TIMELINES[args.timeline], args.speed, printer),
        daemon=True,
    )
    feeder.start()
    brain.run()
    printer("\n--- sim ended ---")


class _TracingEyes(NullEyes):
    """like NullEyes but prints each expression change so you can see the
    'face' the robot would show alongside the motor commands."""

    def __init__(self, printer):
        super().__init__()
        self._print = printer

    def set_state(self, state, **params):
        if state != self.state or params != self.params:
            self._print(f"    eyes -> {state} {params or ''}")
        super().set_state(state, **params)


if __name__ == "__main__":
    main()
