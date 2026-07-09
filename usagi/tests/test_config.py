import pytest

from usagi.config import ConfigError, validate


def _good():
    return {
        "motors": {
            "left": {"in1": 17, "in2": 27, "pwm": 12},
            "right": {"in1": 23, "in2": 24, "pwm": 13},
            "standby": 25,
            "max_speed": 0.8,
        },
        "imu": {"address": 0x68, "poll_hz": 50},
        "camera": {"fps": 15},
        "audio": {"sample_rate": 16000},
        "brain": {"tick_hz": 20},
        "calibration": {"speed_scale": 1.0, "turn_scale": 1.0,
                        "duration_scale": 1.0, "left_trim": 1.0, "right_trim": 1.0},
    }


def test_valid_config_has_no_warnings():
    assert validate(_good()) == []


def test_duplicate_pin_is_error():
    cfg = _good()
    cfg["motors"]["right"]["in1"] = 17   # collides with left.in1
    with pytest.raises(ConfigError) as e:
        validate(cfg)
    assert "17" in str(e.value)


def test_non_hardware_pwm_pin_warns_not_errors():
    cfg = _good()
    cfg["motors"]["left"]["pwm"] = 5     # valid pin, not hw-pwm
    warns = validate(cfg)
    assert any("hardware-PWM" in w for w in warns)


def test_bad_max_speed_is_error():
    cfg = _good()
    cfg["motors"]["max_speed"] = 1.5
    with pytest.raises(ConfigError):
        validate(cfg)


def test_zero_calibration_is_error():
    cfg = _good()
    cfg["calibration"]["speed_scale"] = 0
    with pytest.raises(ConfigError):
        validate(cfg)


def test_high_calibration_warns():
    cfg = _good()
    cfg["calibration"]["turn_scale"] = 5
    assert any("unusually high" in w for w in validate(cfg))


def test_bad_i2c_address_is_error():
    cfg = _good()
    cfg["imu"]["address"] = 0x99
    with pytest.raises(ConfigError):
        validate(cfg)
