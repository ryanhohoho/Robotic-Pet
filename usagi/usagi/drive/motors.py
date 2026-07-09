"""differential drive via tb6612fng using gpiozero.

wiring per side: in1/in2 set direction, pwm pin sets speed.
standby pin gates the whole chip, pulled low on close as a failsafe.
gpiozero imports are inside __init__ so this module imports fine off-pi."""

import atexit


def _clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


class _MotorChannel:
    """one side of the tb6612: two direction pins + one pwm pin"""

    def __init__(self, in1: int, in2: int, pwm: int):
        from gpiozero import DigitalOutputDevice, PWMOutputDevice

        self._in1 = DigitalOutputDevice(in1)
        self._in2 = DigitalOutputDevice(in2)
        # hardware pwm on gpio 12/13 when pigpio/lgpio factory is available,
        # software pwm otherwise -- fine for tt motors
        self._pwm = PWMOutputDevice(pwm, frequency=1000)

    def set(self, speed: float):
        # speed -1..1, sign is direction
        if speed > 0:
            self._in1.on()
            self._in2.off()
        elif speed < 0:
            self._in1.off()
            self._in2.on()
        else:
            # short brake (both low = coast on tb6612, both high = brake;
            # coast is gentler for a pet robot)
            self._in1.off()
            self._in2.off()
        self._pwm.value = abs(speed)

    def close(self):
        self.set(0.0)
        self._pwm.close()
        self._in1.close()
        self._in2.close()


class Drive:
    """owns both motors. all speeds are -1.0..1.0, scaled by max_speed."""

    def __init__(self, cfg: dict):
        from gpiozero import DigitalOutputDevice

        m = cfg["motors"]
        self._max = float(m.get("max_speed", 1.0))
        self._left = _MotorChannel(m["left"]["in1"], m["left"]["in2"], m["left"]["pwm"])
        self._right = _MotorChannel(m["right"]["in1"], m["right"]["in2"], m["right"]["pwm"])
        self._stby = DigitalOutputDevice(m["standby"], initial_value=True)
        self._closed = False
        # never leave motors spinning if the process dies
        atexit.register(self.close)

    def move(self, left: float, right: float):
        """set wheel speeds directly, clamped and scaled by max_speed"""
        self._left.set(_clamp(left) * self._max)
        self._right.set(_clamp(right) * self._max)

    def forward(self, speed: float = 0.5):
        self.move(speed, speed)

    def backward(self, speed: float = 0.5):
        self.move(-speed, -speed)

    def turn(self, rate: float):
        """rate -1 (full left spin) .. 1 (full right spin)"""
        rate = _clamp(rate)
        self.move(rate, -rate)

    def stop(self):
        self.move(0.0, 0.0)

    def close(self):
        """stop and release gpio, pull standby low"""
        if self._closed:
            return
        self._closed = True
        try:
            self.stop()
        finally:
            self._stby.off()
            self._stby.close()
            self._left.close()
            self._right.close()
