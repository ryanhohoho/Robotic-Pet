# Usagi Robot — software

Autonomous wheeled Usagi head unit on a Raspberry Pi 3 B+.
See `ARCHITECTURE.md` for the design plan.

## Setup (on the Pi, Raspberry Pi OS Bookworm)

One-shot: `bash scripts/setup_pi.sh` (installs system libs, enables I2C +
camera, builds the venv, installs deps, validates config). Or manually:

```bash
sudo apt install python3-picamera2 python3-opencv libportaudio2
sudo raspi-config   # enable I2C and camera
python3 -m venv --system-site-packages .venv   # system-site needed for picamera2
source .venv/bin/activate
pip install -r requirements.txt
python -m usagi.main
```

Autostart on boot: copy `scripts/usagi.service` to
`/etc/systemd/system/` and `sudo systemctl enable --now usagi`.

## Develop and tune without hardware

```bash
python -m usagi.sim                 # run the real brain on any computer
python -m usagi.sim --timeline face_hello --speed 4
python scripts/power_budget.py --mah 1500   # battery runtime estimate
pytest tests/                       # 37 hardware-free unit tests
```

The sim runs the real state machine, behaviors and calibration with faked
motors/sensors, printing state changes, motor commands and expressions.

## Calibration (tune once, correct on hardware)

Routines are authored with relative values. The `calibration` block in
`config.yaml` scales all movement and timing globally, so if a routine is
right in sim but turns are wide / speed is off / it drifts on the real
robot, fix it there without rewriting routines:

```yaml
calibration:
  speed_scale: 1.0     # all forward speeds
  turn_scale: 1.0      # turn sharpness (lower = wider turns tightened)
  duration_scale: 1.0  # routine step timing
  left_trim: 1.0       # per-wheel drift correction
  right_trim: 1.0
```

## Bring-up on the Pi

```bash
python scripts/selftest.py          # one-shot pass/fail for all subsystems
# or per-subsystem: test_motors.py, test_eyes-less, test_camera.py, test_audio.py, test_imu.py
```

## Layout

```
usagi/
  main.py              entry point, wiring
  sim.py               simulation runner (no hardware)
  config.py            yaml load + validate (pin collisions, ranges)
  events.py            shared event types
  drive/motors.py      TB6612FNG differential drive (gpiozero)
  drive/calibration.py global tuning knobs + CalibratedDrive wrapper
  senses/camera.py     picamera2 capture thread
  senses/vision.py     frame analysis (opencv, no hardware)
  senses/audio.py      usb mic loudness events (sounddevice)
  senses/imu.py        mpu6050 bump/pickup (smbus2)
  face/eyes.py         NullEyes stub (OLEDs removed in v2, face is painted)
  brain/               state machine + behaviors (transitions)
scripts/
  setup_pi.sh          one-shot Pi setup
  usagi.service        systemd autostart unit
  selftest.py          unified hardware pass/fail check
  power_budget.py      battery runtime estimate
  test_*.py            per-subsystem bring-up
tests/                 pytest for hardware-free modules (37 tests)
```
