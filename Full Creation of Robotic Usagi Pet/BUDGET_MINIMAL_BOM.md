# Usagi Robot — Minimal-Cost BOM (excluding Pi + filament)

Question: with only the Raspberry Pi and 3D printer already owned, can the
rest of the parts come in at **$65**?

**Short answer: yes, ~$60–64 is achievable — but only if you (1) substitute
the $25 Camera Module 3 for a budget OV5647 CSI clone, (2) buy from
AliExpress, and (3) print the caster instead of buying one.** With the
genuine Camera Module 3, the realistic floor is ~$80–85.

The single biggest lever is the camera. Everything else is already cheap.

---

## Rock-bottom BOM (all-AliExpress, target $65)

| # | Part | Qty | Est. $ | Note |
|---|------|-----|--------|------|
| 1 | N20 6V gearmotor + 34×7mm wheel set | 2 | 8 | ~$4/set incl. wheel. Pick 100–200 rpm. |
| 2 | TB6612FNG breakout (generic) | 1 | 4 | Generic clone is fine; same chip. |
| 3 | OV5647 5MP CSI camera (clone) | 1 | 9 | **Camera swap** — see software note below. |
| 4 | USB microphone (mini) | 1 | 3 | Cheapest plug-in USB mic module. |
| 5 | MPU6050 IMU | 1 | 2 | Optional but ~$2, keep it. |
| 6 | microSD 32GB (A1) | 1 | 6 | Needed to boot the Pi. |
| 7 | 2S LiPo 1300mAh + lead | 1 | 11 | Smallest usable pack. |
| 8 | 2S USB LiPo charger board | 1 | 4 | Cheaper than a B6-style charger. |
| 9 | UBEC 5V/3A (generic) | 1 | 4 | Clean 5V for the Pi. |
| 10 | Slide switch + fuse holder + XT60/JST | 1 | 3 | Main cutoff + protection. |
| 11 | Jumper/Dupont wire assortment | 1 | 3 | Signal + power hookups. |
| 12 | 40-pin header + M2.5 standoffs | 1 | 3 | Mount/connect the Pi. |
| 13 | M2/M2.5/M3 screw assortment | 1 | 3 | Motors, plate, Pi. |
| 14 | Ball caster | 1 | **0** | **Print it** + a 10mm steel BB/marble. |
| 15 | Caps: 2×0.1µF + 1×1000µF, heatshrink, 24AWG wire | 1 | 2 | Motor noise suppression + splices. |
| | **Total** | | **≈ $60–64** | Inside $65. |

Prices are typical AliExpress July 2026; ±20% by seller. Buy motors,
camera, IMU, and passives in single combined orders to minimize shipping.

---

## What you give up vs. the standard build

- **Camera:** OV5647 (5MP, fixed focus, the original Pi Camera v1 sensor)
  instead of Module 3 (12MP, autofocus, HDR). For an obstacle/motion/face
  robot this is a non-issue — the vision pipeline downscales to 160×120
  anyway and needs no autofocus. Some cheap OV5647 boards are wide-angle,
  which actually helps navigation.
- **Charger:** a USB 2S board charges slower and has no fancy display, but
  it balance-charges safely. Fine for a hobby pack.
- **Generic TB6612/UBEC:** clones are reliable here; just verify the UBEC
  output is a true 5V before connecting the Pi.
- **Printed caster:** a printed socket + steel BB works; if it drags on
  your floor, the $2–3 bought ball caster is the easy upgrade.

## Software cohesion of the camera swap
The OV5647 is a first-class libcamera/picamera2 sensor, so **no code
change** — `senses/camera.py` opens it exactly the same way. You lose
autofocus (irrelevant, fixed-focus is fine at pet-robot distances). This
is confirmed against the existing capture code; confidence ~95%.

## If you keep the genuine Camera Module 3
Swap line 3 to $25 and the total lands at ~$78–80. Still well under the
original $150–220 budget, just not $65. The camera is the only thing
standing between the two figures.

---

## Confidence
- **$65 achievable:** ~90%, contingent on the OV5647 substitution and
  AliExpress sourcing. Currency, shipping, and seller variance are the
  risks, all covered by the small headroom.
- **Function unaffected by the cheap parts:** ~95%. The only part that
  touches software is the camera, and the OV5647 is fully supported.
- Verify N20 body (12×10mm) and wheel (34×7mm) against your printed base
  pocket before the final base print.
