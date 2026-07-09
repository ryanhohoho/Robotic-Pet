"""mpu6050 over smbus2, polled at ~50hz in its own thread.

detection logic lives in ImuDetector (no hardware) so it's unit testable:
- bump: accel magnitude spike above bump_threshold_g
- pickup: magnitude below pickup-band for a sustained window (lift/freefall)
- put_down: back near 1g steady for a while after a pickup
"""

import math
import threading
import time

from ..events import Event, EventType

# mpu6050 registers
_PWR_MGMT_1 = 0x6B
_ACCEL_XOUT_H = 0x3B
_ACCEL_SCALE = 16384.0  # lsb per g at +-2g


class ImuDetector:
    """pure detection state machine over a stream of accel magnitudes (g)"""

    def __init__(self, cfg: dict):
        i = cfg.get("imu", {})
        self._bump_g = float(i.get("bump_threshold_g", 1.8))
        self._pickup_g = float(i.get("pickup_threshold_g", 0.4))
        self._pickup_window = float(i.get("pickup_window_s", 0.15))
        self._putdown_window = float(i.get("putdown_window_s", 0.8))
        self._bump_cooldown = float(i.get("bump_cooldown_s", 1.0))
        self._held = False
        self._low_since = None
        self._steady_since = None
        self._last_bump = float("-inf")   # so the very first bump isn't swallowed

    def update(self, mag_g: float, now: float) -> list[Event]:
        events: list[Event] = []

        # bump only matters when not held
        if not self._held and mag_g > self._bump_g and now - self._last_bump >= self._bump_cooldown:
            self._last_bump = now
            events.append(Event(EventType.BUMP, {"g": mag_g}))

        if not self._held:
            # low-g sustained = lifted off the ground
            if mag_g < self._pickup_g:
                self._low_since = self._low_since or now
                if now - self._low_since >= self._pickup_window:
                    self._held = True
                    self._steady_since = None
                    events.append(Event(EventType.PICKED_UP))
            else:
                self._low_since = None
        else:
            # near 1g and calm = put back down
            if 0.85 < mag_g < 1.15:
                self._steady_since = self._steady_since or now
                if now - self._steady_since >= self._putdown_window:
                    self._held = False
                    self._low_since = None
                    events.append(Event(EventType.PUT_DOWN))
            else:
                self._steady_since = None

        return events


class ImuSense:
    def __init__(self, cfg: dict, event_queue):
        i = cfg.get("imu", {})
        self._address = int(i.get("address", 0x68))
        self._bus_num = int(i.get("bus", 1))
        self._interval = 1.0 / float(i.get("poll_hz", 50))
        self._queue = event_queue
        self._detector = ImuDetector(cfg)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _read_accel_g(self, bus) -> float:
        data = bus.read_i2c_block_data(self._address, _ACCEL_XOUT_H, 6)
        vals = []
        for hi, lo in ((0, 1), (2, 3), (4, 5)):
            raw = (data[hi] << 8) | data[lo]
            if raw > 32767:
                raw -= 65536
            vals.append(raw / _ACCEL_SCALE)
        return math.sqrt(sum(v * v for v in vals))

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="imu", daemon=True)
        self._thread.start()

    def _run(self):
        from smbus2 import SMBus

        with SMBus(self._bus_num) as bus:
            # wake the chip, it boots in sleep mode
            bus.write_byte_data(self._address, _PWR_MGMT_1, 0)
            time.sleep(0.05)
            while not self._stop.is_set():
                now = time.monotonic()
                try:
                    mag = self._read_accel_g(bus)
                except OSError:
                    # transient i2c hiccup, skip this sample
                    time.sleep(self._interval)
                    continue
                for ev in self._detector.update(mag, now):
                    self._queue.put(ev)
                time.sleep(self._interval)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
