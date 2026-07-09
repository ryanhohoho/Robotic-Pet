# Usagi Robot — Architecture Plan

Target: Raspberry Pi 3 B+ (4-core A53, 1GB RAM). Everything below is sized
for that CPU budget. Python 3.11 on Raspberry Pi OS Bookworm.

## Core pattern: sensors publish, brain decides, actuators obey

One process, multiple threads, one `queue.Queue` of `Event` objects.

```
 camera thread ──┐
 audio thread  ──┼──> event queue ──> brain loop (main thread, 20Hz)
 imu thread    ──┘                        │
                                          ├──> drive (direct calls)
                                          └──> eyes.set_state() ──> eye thread (30fps)
```

Rules that keep it modular:

- Sensors never touch actuators. They only emit `Event`s.
- Behaviors never touch sensors. They only read events the brain hands them
  and call `drive` / `eyes`.
- Every hardware module has a hardware-free twin where the logic lives
  (`vision.py`, `animations.py`), so unit tests run on any machine.
- Each subsystem has a standalone bring-up script in `scripts/` that runs
  it alone on the Pi.

Threads over asyncio: every lib here (picamera2, sounddevice, luma, smbus2)
is blocking/callback based, threads fit naturally. GIL is fine since opencv
and numpy release it during heavy work.

## Subsystems

### 1. Motor control — `drive/motors.py`
Library: **gpiozero 2.x** (official RPi library).
TB6612FNG per side = IN1, IN2, PWM. Map each side to `gpiozero.Motor`,
STBY to a `DigitalOutputDevice`. PWM pins 12/13 are hardware-PWM capable.
API: `move(l, r)`, `forward`, `backward`, `turn`, `stop`, `close`.
Speeds clamped by `max_speed` in config. Failsafe: `atexit` + signal handler
pulls STBY low so a crash never leaves motors running.

### 2. Camera + stimuli — `senses/camera.py` + `senses/vision.py`
Libraries: **picamera2** (capture) + **opencv** (analysis).
Capture 640x480 @ 15fps. Analysis per frame on a downscaled gray copy:

- motion: frame differencing (cheap, every frame)
- face: haar cascade, every 5th frame only (expensive)
- obstacle: edge density in bottom strip of frame — heuristic since v1 has
  no rangefinder. Bump detection via IMU is the real backstop.

Emits `MOTION_DETECTED`, `FACE_DETECTED` (with x offset for look/follow),
`OBSTACLE_NEAR`.

### 3. Eyes — `face/eyes.py` + `face/animations.py`
Library: **luma.oled** (SSD1306). Two displays at 0x3C/0x3D on one bus
(one display needs its address jumper bridged; fall back to a TCA9548A mux
if both are fixed at 0x3C).
Renderer thread at 30fps draws whatever state is current — brain calls
`eyes.set_state("look", direction=-0.4)` and returns immediately.
States: `idle` (slow drift + auto-blink), `blink`, `look(direction)`,
`react(emotion)`. Animation math isolated in `animations.py`.

### 4. Microphone — `senses/audio.py`
Library: **sounddevice** (PortAudio callback stream), USB mic, 16kHz.
v1: rms loudness gate -> `LOUD_SOUND` event with level. Debounced so a
sustained noise fires once. Clap patterns / direction are later extensions
inside this module only.

### 5. IMU — `senses/imu.py`
Library: **smbus2** + small MPU6050 wrapper (raw regs, ~40 lines — the pypi
mpu6050 packages are stale, not worth the dependency).
Poll accel at 50Hz: spike > 1.8g -> `BUMP`, sustained low-g -> `PICKED_UP`,
steady 1g after -> `PUT_DOWN`.

### 6. Brain — `brain/state_machine.py` + `brain/behaviors/`
Library: **transitions** (well maintained, declarative FSM).

States and main transitions:

```
SLEEPING --(loud sound / manual start)--> IDLE
IDLE --(idle_timeout)--> EXPLORING
IDLE/EXPLORING --(LOUD_SOUND, FACE_DETECTED, BUMP)--> REACTING
REACTING --(routine finished)--> IDLE
any state --(PICKED_UP)--> HELD          # motors hard-stop, priority event
HELD --(PUT_DOWN)--> IDLE
```

Brain loop each tick (20Hz): drain event queue, priority events (PICKED_UP)
transition immediately, others go to the current behavior, then
`behavior.tick(dt)` runs. Behaviors are `enter()/tick()/exit()` objects:
`idle`, `explore` (wander + avoid), `react` (scripted routines keyed by
stimulus), `held`. Preprogrammed routines = react scripts as timed
keyframe lists (drive + eye commands), data not code, easy to add.

## Testing plan

1. `scripts/test_*.py` — each subsystem alone on the Pi, in bring-up order:
   eyes -> motors -> camera -> audio -> imu
2. `tests/` — pytest on dev machine for vision, animations, state machine
   (mocked drive/eyes), event handling
3. integration: brain + eyes only (motors unplugged), then add drive

## Deliberate v1 simplifications

- obstacle detection is vision-heuristic + bump recovery, no rangefinder
- no audio direction finding, no speech
- no battery monitoring (LOW_BATTERY event type reserved; a voltage divider
  + ADC is a possible v1.1 add since the Pi has no analog input)
- single process, no networking/remote control
