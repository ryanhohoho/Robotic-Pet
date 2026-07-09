# Usagi Robot — Updated Parts & Buy Plan (July 2026)

Reflects the v2/v3 hardware pivot: concealed N20 wheels under a flat base,
front ball caster, and OLED eyes eliminated (painted static face).

---

## Part 1 — Exact replacement text for the Project Instructions

Replace the **Current design**, **Hardware**, and **Target size** sections
of the project brief with the text below. Everything else in the brief
(Goal, Printer, Budget, Behavior goals, Design history, User background)
stays as-is. A short addition to **Design history** is given at the end.

### > Current design (locked in, no need to revisit)
```
- Head unit: mobile robot, Usagi head shape. Differential drive with 2
  small wheels concealed under a flat base bottom, plus 1 front ball
  caster for stability. Wheels poke through slots in the base; no wheels
  visible from the side.
- Body base: cosmetic display unit, no electronics. Head parks into a
  neck ring on top of the body when powered off.
- Head and body are separate single-piece prints, shaped to match the
  anime reference (smooth lofted geometry). Ears added manually.
- Camera fixed forward-facing in the face, no rotating/stabilized
  mechanism.
- Face: painted on, fully static. NO eye displays, NO OLEDs, no moving
  eyes. Facial expression in software is conveyed through movement only.
- Ears: static, cloth or printed, no servos in v1.
```

### > Hardware
```
- SBC: Raspberry Pi 3 Model B+ (2017), board 85x56x17mm
- Camera: Raspberry Pi Camera Module 3, standard, CSI connector
- Drive motors: 2x N20 micro metal gearmotor (6V), body ~12x10mm.
  Wheels: 2x N20 wheel, 34x7mm, 3mm D-shaft. Small enough to conceal
  fully under the flat base. (TT motors dropped: too long to fit across
  the narrow sphere bottom.)
- Front caster: 1x small ball caster/roller for the third contact point.
- Motor driver: TB6612FNG breakout (drives the N20s unchanged).
- Eyes: NONE. Face is painted; no I2C displays, no multiplexer.
- Mic: USB microphone module (avoids I2S devicetree config hassle).
- IMU: MPU6050, optional, for bump/pickup detection.
- Battery: 2S LiPo, 1300-2200mAh.
- Power: UBEC 5V/3A for the Pi, kept on a separate rail from motors.
  Note: 2S (7.4V nominal) feeds the TB6612 motor rail directly; 6V N20s
  run slightly over-volt, so the software keeps a max_speed cap.
```

### > Target size
```
Head unit approx 5-6in diameter. Body base sized to look proportionate
with the head parked in the neck ring, approx 8-10in overall display
height. Head and body print as separate single pieces. The flat base
bottom doubles as the chassis plate: motors, caster, Pi and battery all
mount to it and unscrew from below. Ground clearance is ~4mm, so hard
floors only.
```

### > Append to Design history (context only)
```
v2/v3 pivot (July 2026): switched from side-mounted TT-motor wheels to
concealed N20 micro-gearmotor wheels under a flat base; added front ball
caster; rebuilt head/body as smooth lofted solids matching the anime
reference; eliminated OLED eyes in favor of a painted static face.
```

### Software note tied to this pivot
Removing the OLEDs means the `eyes` subsystem in the software has no
output device. Swap `face/eyes.py` for a **NullEyes** driver (same
`set_state/start/stop` interface, drives no hardware) and drop the
`luma.oled` dependency. The brain and state machine are otherwise
unchanged. Motor code (`gpiozero` + TB6612) works with the N20s as-is;
only tune `max_speed` and behavior cruise speeds for the smaller wheels.

---

## Part 2 — Full buy plan (you have only the printer + Pi 3 B+)

Assumes you own **nothing else** — no SD card, no wires, no charger, no
filament. Grouped by function. Prices are typical July 2026 USD; buy the
cheap-source column to stay well inside the $150-220 budget.

### Essential BOM

| # | Part | Qty | Est. $ | Purpose / notes |
|---|------|-----|--------|-----------------|
| 1 | N20 6V micro gearmotor + 34x7mm wheel set | 2 | 12 | Drive. Pick **100-200 rpm** (slow enough to control on 34mm wheels). Sets often bundle motor+wheel+bracket. |
| 2 | Ball caster / roller (metal, ~10-13mm) | 1 | 3 | Third contact point at the front. |
| 3 | TB6612FNG motor driver breakout | 1 | 10 | Drives both N20s. SparkFun or generic. |
| 4 | Raspberry Pi Camera Module 3 (standard) | 1 | 25 | Vision. Ships with a 15-pin cable that fits the Pi 3 B+. |
| 5 | USB microphone module (mini) | 1 | 8 | Sound response. Plug-and-play, no I2S config. |
| 6 | MPU6050 IMU module | 1 | 5 | Bump/pickup detection. Optional but cheap; software supports it. |
| 7 | microSD card 32GB (A1, Class 10) | 1 | 8 | Pi OS boot drive. |
| 8 | 2S LiPo battery, 1500mAh, with XT60/JST lead | 1 | 16 | Main power. |
| 9 | 2S LiPo balance charger | 1 | 15 | Required to charge safely. A basic B3/B6-style charger is fine. |
| 10 | UBEC 5V/3A (switching regulator) | 1 | 8 | Clean 5V for the Pi, separate rail from motors. |
| 11 | Battery connector pigtail + inline slide switch | 1 | 6 | Main power cutoff and clean battery hookup. |
| 12 | Jumper wire assortment (M-F, F-F, M-M) | 1 | 7 | Signal + power hookups. |
| 13 | 40-pin header + M2.5 standoffs/spacers | 1 | 8 | Mount and connect the Pi. |
| 14 | Screw assortment M2 / M2.5 / M3 | 1 | 8 | Motors, caster, Pi, base plate. |
| 15 | Heat-shrink + hookup wire (22-24 AWG) | 1 | 6 | Motor leads, power splices (you solder). |
| 16 | PLA filament, 1kg | 1 | 20 | Head, body, base, mounts. One roll covers the build. |
| | **Essential subtotal** | | **≈ $165** | Inside budget, leaves headroom. |

### Recommended extras (optional, ~$25)

| Part | Est. $ | Why |
|------|--------|-----|
| 2S LiPo voltage alarm/checker | 5 | Beeps before you over-discharge the pack. |
| LiPo-safe charging bag | 6 | Fire safety while charging. |
| Small breadboard | 5 | Bench-test TB6612 + motors before final wiring. |
| Spare PLA roll (second color) | 20 | Paint-free two-tone, or reprints. |
| Multimeter (if you don't own one) | 12 | Verify the 5V rail and check continuity. |

### Buy-order and sourcing strategy

Order in **two waves** so nothing blocks you:

1. **Wave 1 (drive + power core):** items 1, 2, 3, 8, 9, 10, 11, 12, 15.
   These let you bench-test the N20 + TB6612 + battery path against the
   `scripts/test_motors.py` bring-up script and tune speeds. Longest
   shipping is usually the LiPo/charger, so order these first.
2. **Wave 2 (compute peripherals):** items 4, 5, 6, 7, 13, 14, 16. The
   camera, mic, IMU and SD card plug into the Pi you already have.

**Where to buy:**
- Motors, wheels, caster, MPU6050, jumpers, screws: AliExpress (cheapest,
  slow) or Amazon (fast, ~30% more).
- TB6612FNG, UBEC: SparkFun / Pololu / Adafruit for reliable parts.
- Camera Module 3: official resellers (PiShop, PiHut, CanaKit) at $25.
- LiPo + charger: a hobby/RC shop (HobbyKing, local) — buy them together.

**Safety flags:** LiPo needs a balance charger (item 9) and should be
charged in a bag; never charge unattended. Keep the motor rail (battery
direct to TB6612 VM) separate from the Pi rail (through the UBEC) as the
brief specifies — motor noise can brown-out the Pi otherwise.

### Confidence
- Part fit vs. software: ~95% (motor/driver/camera/mic/IMU all supported
  as-is; only the OLED→NullEyes swap is required).
- N20 cradle and wheel dimensions: verify your actual motors (12x10mm
  body, 34x7mm wheel) against the printed base before printing the final
  plate — the 3D chat flagged ~90% on cradle dims.
- Prices: ±20% by vendor/region; the essential subtotal has budget slack.
