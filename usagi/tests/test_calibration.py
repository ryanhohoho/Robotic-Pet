from usagi.drive.calibration import CalibratedDrive, Calibration


def test_identity_calibration_passes_through():
    cal = Calibration()
    assert cal.wheels(0.5, 0.5) == (0.5, 0.5)
    assert cal.wheels(0.8, -0.8) == (0.8, -0.8)
    assert cal.duration(1.0) == 1.0


def test_speed_scale_only_affects_forward():
    cal = Calibration(speed_scale=0.5)
    # pure forward halves
    assert cal.wheels(1.0, 1.0) == (0.5, 0.5)
    # pure spin (common=0) is untouched by speed_scale
    assert cal.wheels(1.0, -1.0) == (1.0, -1.0)


def test_turn_scale_narrows_turns_without_touching_speed():
    cal = Calibration(turn_scale=0.5)
    # forward component preserved, differential halved
    l, r = cal.wheels(1.0, 0.0)   # common=0.5, diff=0.5
    assert l == 0.75 and r == 0.25
    # pure forward unaffected
    assert cal.wheels(0.6, 0.6) == (0.6, 0.6)


def test_trim_corrects_one_wheel():
    cal = Calibration(left_trim=0.9)
    l, r = cal.wheels(1.0, 1.0)
    assert abs(l - 0.9) < 1e-9 and abs(r - 1.0) < 1e-9


def test_duration_scale():
    assert Calibration(duration_scale=2.0).duration(0.5) == 1.0


def test_from_cfg_reads_block():
    cal = Calibration.from_cfg({"calibration": {"speed_scale": 0.7, "turn_scale": 1.3}})
    assert cal.speed_scale == 0.7 and cal.turn_scale == 1.3
    assert cal.left_trim == 1.0   # default fills in


def test_calibrated_drive_applies_and_stop_is_true_stop():
    class Rec:
        def __init__(self): self.last = None
        def move(self, l, r): self.last = (l, r)
        def close(self): pass

    inner = Rec()
    d = CalibratedDrive(inner, Calibration(speed_scale=0.5))
    d.forward(1.0)
    assert inner.last == (0.5, 0.5)
    d.stop()                       # stop bypasses scaling
    assert inner.last == (0.0, 0.0)
