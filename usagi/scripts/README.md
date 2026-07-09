# hardware bring-up scripts

Standalone scripts, run one at a time on the Pi to verify each subsystem
before any integration. Planned:

- `test_motors.py` — spin each wheel both directions, ramp speed, stop
- `test_eyes.py` — init both OLEDs, draw test pattern, cycle animations
- `test_camera.py` — capture frames, save a jpg, print fps
- `test_audio.py` — print live rms level from the mic
- `test_imu.py` — stream accel values, print BUMP/PICKUP detections

Written after architecture approval, alongside each module.
