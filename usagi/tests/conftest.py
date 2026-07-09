"""shared fakes so brain/behavior tests never touch hardware."""

import queue
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class FakeDrive:
    def __init__(self):
        self.speeds = (0.0, 0.0)
        self.stopped = True
        self.calls = []

    def move(self, left, right):
        self.speeds = (left, right)
        self.stopped = left == 0 and right == 0
        self.calls.append(("move", left, right))

    def forward(self, speed=0.5):
        self.move(speed, speed)

    def backward(self, speed=0.5):
        self.move(-speed, -speed)

    def turn(self, rate):
        self.move(rate, -rate)

    def stop(self):
        self.move(0.0, 0.0)

    def close(self):
        self.stop()


class FakeEyes:
    def __init__(self):
        self.state = "closed"
        self.params = {}
        self.history = []

    def set_state(self, state, **params):
        self.state = state
        self.params = params
        self.history.append((state, params))


@pytest.fixture
def cfg():
    # minimal config covering everything the brain and detectors need
    return {
        "brain": {"tick_hz": 20, "idle_timeout_s": 30},
        "vision": {},
        "imu": {},
        "audio": {},
    }


@pytest.fixture
def drive():
    return FakeDrive()


@pytest.fixture
def eyes():
    return FakeEyes()


@pytest.fixture
def events():
    return queue.Queue()
