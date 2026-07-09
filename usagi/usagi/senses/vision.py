"""pure frame analysis, no hardware -- unit testable with synthetic frames.

detectors (all on a downscaled grayscale copy, sized for pi 3 cpu):
- motion: frame differencing, every frame
- face: haar cascade, every nth frame only (expensive)
- obstacle: edge density in the bottom strip of the frame (heuristic,
  imu bump detection is the real backstop)
"""

import time

import cv2
import numpy as np

from ..events import Event, EventType

_ANALYZE_W, _ANALYZE_H = 160, 120


class VisionAnalyzer:
    def __init__(self, cfg: dict):
        v = cfg.get("vision", {})
        self._motion_ratio = float(v.get("motion_ratio", 0.02))
        self._motion_cooldown = float(v.get("motion_cooldown_s", 1.0))
        self._face_every = int(v.get("face_every_n_frames", 5))
        self._face_cooldown = float(v.get("face_cooldown_s", 1.0))
        self._edge_density = float(v.get("obstacle_edge_density", 0.12))
        self._obstacle_cooldown = float(v.get("obstacle_cooldown_s", 0.5))

        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self._face_cascade = cv2.CascadeClassifier(cascade_path)
        self._prev_gray = None
        self._frame_count = 0
        # per-detector debounce timestamps
        self._last = {t: 0.0 for t in ("motion", "face", "obstacle")}

    def _ready(self, key: str, cooldown: float, now: float) -> bool:
        if now - self._last[key] >= cooldown:
            self._last[key] = now
            return True
        return False

    def analyze(self, frame: np.ndarray) -> list[Event]:
        """frame: bgr or rgb uint8 array. returns list[Event] for this frame."""
        now = time.monotonic()
        events: list[Event] = []
        self._frame_count += 1

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (_ANALYZE_W, _ANALYZE_H))
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        # motion: fraction of pixels that changed since last frame
        if self._prev_gray is not None:
            diff = cv2.absdiff(gray, self._prev_gray)
            changed = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
            ratio = float(np.count_nonzero(changed)) / changed.size
            if ratio > self._motion_ratio and self._ready("motion", self._motion_cooldown, now):
                events.append(Event(EventType.MOTION_DETECTED, {"ratio": ratio}))
        self._prev_gray = gray

        # face: only every nth frame, haar is the expensive one
        if self._frame_count % self._face_every == 0:
            faces = self._face_cascade.detectMultiScale(gray, 1.2, 4, minSize=(24, 24))
            if len(faces) > 0 and self._ready("face", self._face_cooldown, now):
                # biggest face wins, report horizontal offset -1..1 for look/follow
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                cx = (x + w / 2) / _ANALYZE_W
                events.append(Event(EventType.FACE_DETECTED, {"x_offset": cx * 2 - 1}))

        # obstacle: lots of edges close to the ground usually means something ahead
        bottom = gray[int(_ANALYZE_H * 0.7):, :]
        edges = cv2.Canny(bottom, 50, 150)
        density = float(np.count_nonzero(edges)) / edges.size
        if density > self._edge_density and self._ready("obstacle", self._obstacle_cooldown, now):
            events.append(Event(EventType.OBSTACLE_NEAR, {"density": density}))

        return events
