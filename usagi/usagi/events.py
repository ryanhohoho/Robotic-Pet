"""shared event types. every sensor thread publishes these onto one queue,
the brain consumes them. keeps subsystems decoupled from each other."""

from dataclasses import dataclass, field
from enum import Enum, auto
import time


class EventType(Enum):
    # vision
    MOTION_DETECTED = auto()
    FACE_DETECTED = auto()
    OBSTACLE_NEAR = auto()
    # audio
    LOUD_SOUND = auto()
    # imu
    BUMP = auto()
    PICKED_UP = auto()
    PUT_DOWN = auto()
    # system
    LOW_BATTERY = auto()
    SHUTDOWN = auto()


@dataclass
class Event:
    type: EventType
    data: dict = field(default_factory=dict)   # e.g. {"x_offset": -0.3} for face position
    timestamp: float = field(default_factory=time.monotonic)
