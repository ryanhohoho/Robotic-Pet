#!/usr/bin/env python3
"""one-shot hardware self-test for bring-up day.

checks each subsystem in sequence and prints a pass/fail report, instead of
running the five separate test_*.py scripts by hand. non-destructive: it
pulses the motors only briefly. prop the wheels up before running.

run from repo root on the pi:  python scripts/selftest.py
add --no-motors to skip the motor pulse (e.g. still on the bench)."""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from usagi import config

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"
results: list[tuple[str, str, str]] = []


def test_config(cfg):
    warns = config.validate(cfg)
    return True, (f"{len(warns)} warning(s)" if warns else "valid, no warnings")


def test_i2c_imu(cfg):
    from smbus2 import SMBus
    addr = cfg.get("imu", {}).get("address", 0x68)
    with SMBus(cfg.get("imu", {}).get("bus", 1)) as bus:
        bus.read_byte(addr)
    return True, f"IMU responds at {hex(addr)}"


def test_camera(cfg):
    from picamera2 import Picamera2
    cam = Picamera2()
    c = cfg["camera"]
    cam.configure(cam.create_still_configuration(
        main={"size": (c.get("width", 640), c.get("height", 480)), "format": "RGB888"}))
    cam.start()
    time.sleep(0.5)
    frame = cam.capture_array("main")
    cam.stop()
    cam.close()
    return frame is not None and frame.size > 0, f"captured {frame.shape}"


def test_mic(cfg):
    import numpy as np
    import sounddevice as sd
    a = cfg["audio"]
    rec = sd.rec(int(0.3 * a["sample_rate"]), samplerate=a["sample_rate"],
                 channels=1, dtype="float32")
    sd.wait()
    level = float(np.sqrt(np.mean(np.square(rec))))
    return level >= 0, f"captured audio, rms={level:.5f}"


def test_motors(cfg):
    from usagi.drive.motors import Drive
    d = Drive(cfg)
    try:
        for l, r in [(0.4, 0), (0, 0.4), (0, 0)]:
            d.move(l, r)
            time.sleep(0.4)
    finally:
        d.close()
    return True, "pulsed each wheel (verify both moved)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-motors", action="store_true")
    args = ap.parse_args()

    cfg = config.load()

    checks = [
        ("config", lambda: test_config(cfg)),
        ("IMU (I2C)", lambda: test_i2c_imu(cfg)),
        ("camera (CSI)", lambda: test_camera(cfg)),
        ("microphone (USB)", lambda: test_mic(cfg)),
    ]
    if not args.no_motors:
        checks.append(("motors (TB6612)", lambda: test_motors(cfg)))
    else:
        results.append(("motors (TB6612)", SKIP, "--no-motors"))

    print("usagi self-test\n" + "=" * 46)
    for name, fn in checks:
        print(f"[..] {name}", flush=True)
        try:
            ok, detail = fn()
            status = PASS if ok else FAIL
        except Exception as e:  # noqa: BLE001
            status, detail = FAIL, f"{type(e).__name__}: {e}"
        results.append((name, status, detail))
        print(f"\r[{status}] {name} — {detail}")

    print("=" * 46)
    n_fail = sum(1 for _, s, _ in results if s == FAIL)
    for name, status, detail in results:
        print(f"  {status:4}  {name}")
    print("=" * 46)
    print("all systems go" if n_fail == 0 else f"{n_fail} subsystem(s) need attention")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
