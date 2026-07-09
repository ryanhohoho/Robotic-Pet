#!/usr/bin/env python3
"""motor bring-up: each wheel both directions, ramp, spin, stop.
PROP THE ROBOT UP so the wheels are off the ground first.
run from repo root: python scripts/test_motors.py"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from usagi import config
from usagi.drive.motors import Drive


def main():
    drive = Drive(config.load())
    try:
        print("left wheel forward")
        drive.move(0.5, 0)
        time.sleep(1.5)
        print("left wheel backward")
        drive.move(-0.5, 0)
        time.sleep(1.5)
        print("right wheel forward")
        drive.move(0, 0.5)
        time.sleep(1.5)
        print("right wheel backward")
        drive.move(0, -0.5)
        time.sleep(1.5)

        print("ramp both 0 -> max")
        for i in range(0, 11):
            drive.forward(i / 10)
            time.sleep(0.2)
        drive.stop()
        time.sleep(0.5)

        print("spin left, then right")
        drive.turn(-0.5)
        time.sleep(1.0)
        drive.turn(0.5)
        time.sleep(1.0)
        print("done")
    finally:
        drive.close()


if __name__ == "__main__":
    main()
