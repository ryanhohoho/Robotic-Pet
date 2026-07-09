#!/usr/bin/env python3
"""mic bring-up: print live rms level and LOUD_SOUND events for 20s.
run from repo root: python scripts/test_audio.py"""

import math
import queue
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import sounddevice as sd

from usagi import config
from usagi.senses.audio import AudioSense


def main():
    cfg = config.load()
    print("input devices:")
    print(sd.query_devices())

    # live level meter, separate stream just for display
    def meter(indata, frames, t, status):
        rms = float(np.sqrt(np.mean(np.square(indata[:, 0]))))
        db = 20 * math.log10(rms) if rms > 0 else -120
        bar = "#" * max(0, int((db + 60) / 2))
        print(f"\r{db:6.1f} dB {bar:30s}", end="", flush=True)

    events: queue.Queue = queue.Queue()
    sense = AudioSense(cfg, events)
    sense.start()

    with sd.InputStream(samplerate=cfg["audio"]["sample_rate"], channels=1, callback=meter):
        end = time.time() + 20
        while time.time() < end:
            try:
                ev = events.get(timeout=0.2)
                print(f"\n  EVENT: {ev.type.name} {ev.data}")
            except queue.Empty:
                pass

    sense.stop()
    print("\ndone")


if __name__ == "__main__":
    main()
