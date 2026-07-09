# Robotic Usagi Pet — Build & Assembly Instructions

Companion to `wiring_schematic.svg` and the software repo in
`Coding_Projects/Robotic Pet/usagi`. v2 hardware: N20 differential drive,
front ball caster, painted static face (no OLEDs), Raspberry Pi 3 B+.

Work through the phases in order. Each phase ends with a checkpoint you can
verify before moving on, so a fault is caught early instead of after final
assembly.

---

## 0. Before you start

Tools: soldering iron + solder, wire cutters/strippers, small Phillips
driver, multimeter, hot glue or threadlocker, and a LiPo-safe charging bag.

Safety, read once: a 2S LiPo stores real energy. Never short the leads,
never charge unattended, never puncture a cell. Wire the fuse and main
switch exactly as drawn before the battery ever touches the electronics.

Print all parts first (see `3d_models/README.md` for orientations and
settings). Do a tolerance test print of the caster mount and a motor
cradle before committing to the full base.

---

## 1. Flash and prep the Raspberry Pi

1. Flash Raspberry Pi OS (Bookworm, 64-bit Lite is enough) to the microSD
   with Raspberry Pi Imager. In the imager's settings, preconfigure
   hostname, your Wi-Fi, and enable SSH so you never need a monitor.
2. Boot the Pi on a bench 5V supply (not the battery yet).
3. Enable the interfaces:
   ```
   sudo raspi-config      # Interface Options -> enable I2C and Camera
   sudo apt update && sudo apt full-upgrade -y
   sudo apt install -y python3-picamera2 python3-opencv libportaudio2 git
   ```
4. Pull the software and set up the venv:
   ```
   git clone <your repo>  usagi    # or copy the folder over
   cd usagi
   python3 -m venv --system-site-packages .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

**Checkpoint:** `python -c "import cv2, picamera2, transitions"` returns no
error.

---

## 2. Bench-wire the drive (off the robot)

Do this on the desk with the base unpopulated, so you can probe freely.

1. Solder short leads to both N20 motors. Solder a 0.1µF ceramic cap
   across each motor's terminals (kills brush noise) and a 470–1000µF
   electrolytic across the TB6612 VM/GND pads.
2. Wire per `wiring_schematic.svg`:
   - Pi 3V3 (pin 1) → TB6612 **VCC**
   - Pi GND → TB6612 GND (and to the common star ground)
   - Signals: GPIO17→AIN1, GPIO27→AIN2, GPIO12→PWMA, GPIO23→BIN1,
     GPIO24→BIN2, GPIO13→PWMB, GPIO25→STBY
   - Motors: AO1/AO2 → left N20, BO1/BO2 → right N20
   - Leave **VM** disconnected for now.
3. Power the Pi from the bench supply. Connect VM to a current-limited
   bench supply at 7.4V if you have one; otherwise the battery through the
   fuse and switch.
4. Prop the base so wheels spin free, then:
   ```
   python scripts/test_motors.py
   ```

**Checkpoint:** each wheel turns both directions, ramps smoothly, and the
spin test rotates the pair in opposite directions. If a wheel runs
backwards, swap that motor's two output wires (or flip `in1`/`in2` in
`config.yaml`).

---

## 3. Add the sensors

1. **Camera:** power the Pi down, seat the CSI ribbon (contacts toward the
   board per the connector), boot, then:
   ```
   python scripts/test_camera.py
   ```
   Check `/tmp/usagi_frame.jpg` for focus and orientation. If the image is
   upside down, set the transform in `senses/camera.py` (or rotate the
   module in its mount).
2. **USB mic:** plug into any Pi USB port, then:
   ```
   python scripts/test_audio.py
   ```
   Watch the live dB meter; clap and confirm a `LOUD_SOUND` event fires.
   Tune `audio.loudness_threshold_db` in `config.yaml` to your room.
3. **IMU (optional):** wire SDA→GPIO2, SCL→GPIO3, VCC→3V3, GND→GND.
   Confirm `i2cdetect -y 1` shows `68`, then:
   ```
   python scripts/test_imu.py
   ```
   Tap it (BUMP), lift it (PICKED_UP), set it down (PUT_DOWN). Tune the
   `imu.*_threshold_g` values if it over/under-triggers.

**Checkpoint:** all four bring-up scripts report sane events.

---

## 4. Power system integration

1. Build the power chain exactly as drawn: **battery + → fuse → main
   switch → VBATT node**. From the node, one branch to the UBEC input,
   one branch to TB6612 **VM**.
2. UBEC output 5V → Pi 5V (pin 2) and UBEC GND → Pi GND (pin 6). Confirm
   the UBEC output reads 5.0–5.2V on the multimeter *before* connecting
   the Pi.
3. Tie all grounds to a single star point at the battery negative
   (battery, UBEC, TB6612, Pi). This prevents motor current from shifting
   the Pi's ground reference and browning it out.
4. Verify the motor rail is battery-direct (≈7.4V at VM) and the Pi rail
   is the regulated 5V — they must not be cross-connected except at ground.

**Checkpoint:** with motors running under load, the Pi does not reboot and
`vcgencmd get_throttled` stays `0x0` (no undervoltage flag).

---

## 5. Mechanical assembly

1. Seat both N20s in the shared motor pocket of the base, wheels poking
   through the slots. Check ~4mm ground clearance and that both wheels
   touch a flat surface evenly.
2. Fit the front ball caster; confirm the base sits level on three points.
3. Mount the Pi on standoffs, the TB6612 and UBEC where the wiring reaches
   without strain, and the battery in its channel (secured, not floating).
4. Route the camera ribbon up into the face; mount the mic where it is not
   blocked by the shell.
5. Everything fastens from below so the base plate lifts off for service.
6. Seat the head onto the body neck ring. Paint the face last.

**Checkpoint:** base sits level, nothing rattles, the head parks cleanly.

---

## 6. First autonomous run and tuning

1. Set the software to run:
   ```
   python -m usagi.main
   ```
2. It boots into `sleeping`. A loud sound wakes it to `idle`; after the
   idle timeout it starts `exploring`.
3. Tune in `config.yaml`, re-running as needed:
   - `motors.max_speed` — start low (0.4) so it can't drive off a table.
   - `vision.obstacle_edge_density` — raise if it dodges phantom
     obstacles, lower if it bumps things.
   - `imu.bump_threshold_g`, `audio.loudness_threshold_db` — per earlier
     bring-up.
4. Optional: install a systemd service so it starts on boot.

**Final checkpoint:** on a hard floor, the robot wanders, backs away from
obstacles/bumps, reacts to sound and faces, and freezes with worried
"expression" (motion pause) when picked up.

---

## Notes on the painted face (v2 change)

The OLED eyes were removed. In software, the `eyes` subsystem is now a
`NullEyes` stub: it still records the expression the behavior requested
(useful for logs and future outputs) but drives no hardware. Reactions are
therefore expressed through **movement**. If you later add an expressive
output (an RGB LED, a small speaker), implement it behind the same
`NullEyes` interface and no behavior code needs to change.
