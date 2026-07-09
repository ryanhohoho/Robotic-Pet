"""loads and validates config.yaml.

validate() catches the mistakes that cause confusing runtime bugs -- two
signals wired to the same gpio, a pwm pin that isn't pwm-capable, clashing
i2c addresses, nonsense thresholds -- before any hardware is touched."""

from pathlib import Path

import yaml

# default search: repo root (one level above this package)
_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "config.yaml"

# bcm pins with hardware pwm on the pi 3 b+
_HW_PWM_PINS = {12, 13, 18, 19}
_VALID_BCM = set(range(2, 28))


class ConfigError(ValueError):
    """raised when the config has a fault that would break the robot"""


def load(path: str | None = None) -> dict:
    cfg_path = Path(path) if path else _DEFAULT_PATH
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        raise ConfigError(f"bad config file: {cfg_path}")
    return cfg


def validate(cfg: dict) -> list[str]:
    """raise ConfigError on hard faults, return a list of soft warnings.
    pure function over the dict, so it's fully unit testable."""
    errors: list[str] = []
    warnings: list[str] = []

    m = cfg.get("motors", {})
    # collect every gpio the motor driver uses, checking for reuse
    pin_owners: dict[int, str] = {}

    def claim(pin, who):
        if pin is None:
            errors.append(f"{who}: missing pin")
            return
        if not isinstance(pin, int) or pin not in _VALID_BCM:
            errors.append(f"{who}: pin {pin} is not a valid BCM pin (2-27)")
            return
        if pin in pin_owners:
            errors.append(f"pin {pin} used by both {pin_owners[pin]} and {who}")
        else:
            pin_owners[pin] = who

    for side in ("left", "right"):
        s = m.get(side, {})
        claim(s.get("in1"), f"motors.{side}.in1")
        claim(s.get("in2"), f"motors.{side}.in2")
        pwm = s.get("pwm")
        claim(pwm, f"motors.{side}.pwm")
        if isinstance(pwm, int) and pwm not in _HW_PWM_PINS:
            warnings.append(
                f"motors.{side}.pwm={pwm} is not a hardware-PWM pin "
                f"{sorted(_HW_PWM_PINS)}; software PWM works but is jittier"
            )
    claim(m.get("standby"), "motors.standby")

    max_speed = m.get("max_speed", 1.0)
    if not (0 < max_speed <= 1.0):
        errors.append(f"motors.max_speed={max_speed} must be in (0, 1]")

    # i2c: imu address distinct and in range (eyes removed in v2, so imu is the
    # only i2c device now)
    imu = cfg.get("imu", {})
    addr = imu.get("address", 0x68)
    if not (0x03 <= addr <= 0x77):
        errors.append(f"imu.address={hex(addr)} outside valid i2c range")

    # sanity on tunables that must be positive
    for path_, val in [
        ("camera.fps", cfg.get("camera", {}).get("fps", 15)),
        ("audio.sample_rate", cfg.get("audio", {}).get("sample_rate", 16000)),
        ("brain.tick_hz", cfg.get("brain", {}).get("tick_hz", 20)),
        ("imu.poll_hz", imu.get("poll_hz", 50)),
    ]:
        if val is None or val <= 0:
            errors.append(f"{path_}={val} must be > 0")

    # calibration knobs: must be positive; flag values likely to be typos
    cal = cfg.get("calibration", {}) or {}
    for key in ("speed_scale", "turn_scale", "duration_scale", "left_trim", "right_trim"):
        v = cal.get(key, 1.0)
        if v is None or v <= 0:
            errors.append(f"calibration.{key}={v} must be > 0")
        elif v > 3.0:
            warnings.append(f"calibration.{key}={v} is unusually high, check it")

    if errors:
        raise ConfigError("config validation failed:\n  - " + "\n  - ".join(errors))
    return warnings
