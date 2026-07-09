"""camera capture thread using picamera2.
grabs frames at configured fps, runs them through VisionAnalyzer,
publishes resulting events to the shared queue.
picamera2 import is inside start() so this module imports off-pi."""

import threading
import time

from .vision import VisionAnalyzer


class CameraSense:
    def __init__(self, cfg: dict, event_queue):
        c = cfg["camera"]
        self._width = int(c.get("width", 640))
        self._height = int(c.get("height", 480))
        self._interval = 1.0 / float(c.get("fps", 15))
        self._queue = event_queue
        self._analyzer = VisionAnalyzer(cfg)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="camera", daemon=True)
        self._thread.start()

    def _run(self):
        from picamera2 import Picamera2

        cam = Picamera2()
        config = cam.create_video_configuration(
            main={"size": (self._width, self._height), "format": "RGB888"}
        )
        cam.configure(config)
        cam.start()
        try:
            while not self._stop.is_set():
                t0 = time.monotonic()
                frame = cam.capture_array("main")
                for ev in self._analyzer.analyze(frame):
                    self._queue.put(ev)
                # keep to target fps, analysis time counts against the budget
                sleep = self._interval - (time.monotonic() - t0)
                if sleep > 0:
                    time.sleep(sleep)
        finally:
            cam.stop()
            cam.close()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
