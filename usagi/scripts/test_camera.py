#!/usr/bin/env python3
"""camera bring-up: run capture + vision for 30s, print detections and fps,
save one frame to /tmp/usagi_frame.jpg for a visual check.
run from repo root: python scripts/test_camera.py"""

import queue
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from usagi import config
from usagi.senses.camera import CameraSense


def main():
    cfg = config.load()
    events: queue.Queue = queue.Queue()
    cam = CameraSense(cfg, events)

    # save one raw frame first for focus/orientation check
    from picamera2 import Picamera2
    import cv2

    p = Picamera2()
    p.configure(p.create_still_configuration(main={"size": (640, 480), "format": "RGB888"}))
    p.start()
    time.sleep(1)
    frame = p.capture_array("main")
    p.stop()
    p.close()
    cv2.imwrite("/tmp/usagi_frame.jpg", frame)
    print("saved /tmp/usagi_frame.jpg")

    cam.start()
    print("watching for 30s, wave / show your face / put a hand close...")
    end = time.time() + 30
    try:
        while time.time() < end:
            try:
                ev = events.get(timeout=0.5)
                print(f"  {ev.type.name} {ev.data}")
            except queue.Empty:
                pass
    finally:
        cam.stop()
    print("done")


if __name__ == "__main__":
    main()
