import numpy as np

from usagi.events import EventType
from usagi.senses.vision import VisionAnalyzer


def _blank(w=640, h=480, value=0):
    return np.full((h, w, 3), value, dtype=np.uint8)


def test_no_events_on_static_blank_frames(cfg):
    v = VisionAnalyzer(cfg)
    assert v.analyze(_blank()) == []
    assert v.analyze(_blank()) == []


def test_motion_detected_on_big_change(cfg):
    v = VisionAnalyzer(cfg)
    v.analyze(_blank(value=0))
    frame = _blank(value=0)
    frame[:, :320] = 255   # half the frame flips bright
    events = v.analyze(frame)
    assert any(e.type == EventType.MOTION_DETECTED for e in events)


def test_motion_debounced_by_cooldown(cfg):
    v = VisionAnalyzer(cfg)
    a, b = _blank(value=0), _blank(value=255)
    v.analyze(a)
    first = v.analyze(b)
    second = v.analyze(a)   # immediately after, still inside cooldown
    assert any(e.type == EventType.MOTION_DETECTED for e in first)
    assert not any(e.type == EventType.MOTION_DETECTED for e in second)


def test_obstacle_on_busy_bottom_strip(cfg):
    v = VisionAnalyzer(cfg)
    frame = _blank(value=0)
    # coarse blocks in the bottom third = lots of edges after downscale
    for x in range(0, 640, 32):
        frame[360:, x:x + 16] = 255
    events = v.analyze(frame)
    assert any(e.type == EventType.OBSTACLE_NEAR for e in events)
