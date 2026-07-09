#!/usr/bin/env python3
"""imu bring-up: stream accel magnitude, print BUMP/PICKED_UP/PUT_DOWN.
poke it, then pick it up and set it down.
run from repo root: python scripts/test_imu.py"""

import queue
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from usagi import config
from usagi.senses.imu import ImuSense


def main():
    cfg = config.load()
    events: queue.Queue = queue.Queue()
    sense = ImuSense(cfg, events)
    sense.start()
    print("streaming for 30s: tap it, pick it up, set it down...")
    end = time.time() + 30
    try:
        while time.time() < end:
            try:
                ev = events.get(timeout=0.5)
                print(f"  {ev.type.name} {ev.data}")
            except queue.Empty:
                pass
    finally:
        sense.stop()
    print("done")


if __name__ == "__main__":
    main()
