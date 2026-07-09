# Usagi Robot — Printable Parts (v4, dimensionally audited)

Head is a smooth analytic loft from `model.glb`; every mounting feature is derived from a single block of **real component dimensions** and checked by an automated fit audit (`FIT_AUDIT.txt`). Regenerate via `usagi_build4.py`. Previews: `verify4.png`. Older versions in `v3_archive/`, `v2_archive/`, `v1_archive/`.

**Do not scale any part.** Every hole and pocket is sized to the actual parts in `PARTS_AND_BUY_PLAN.md`. Scaling would break the fastener and component fits.

## v4 changes (fixes the scale/alignment problems)

- **Plate is now matched to the head.** The head's interior wall at the bottom opening is ~R56; the chassis plate was R47 (ø94) and floated undersized. It's now **R51.9 (ø104)**, derived directly from the measured interior radius with 1mm wall clearance, so it fills the bottom opening to scale.
- **Bosses and plate holes share identical coordinates.** Both the shell mounting bosses and the plate screw holes are generated from one `BOSS_POS` list at (±24, ±34.3). Verified on the exported meshes — they line up exactly. (Before, they were at different radii.)
- **A real seating ledge.** The shell has an internal ledge the plate pushes up against, so it seats at a defined height instead of on ad-hoc bridge bosses.
- **All hole sizes are correct for the specified fasteners:** M3 clearance ø3.4 + ø6.2 countersink (plate→shell), M3 pilot ø2.5 self-tap (bosses, hatch tabs), M2.5 pilot ø2.1 (deck→posts, Pi), M2 pilot ø1.6 (camera). No more "holes too big when scaled" — nothing gets scaled.
- **Camera mount rebuilt to Camera Module 3 spec:** 4 pilots in the true **21 × 12.5mm** pattern (M2), lens bore at the module's **+2.4mm optical-center offset**, PCB seat recess, on a solid pad merged flush into the face.
- **Pi mount corrected to the real 58 × 49mm hole rectangle** (M2.5) on the deck.
- **Caster reworked for a ½" (12.7mm) ball** per the parts plan (was sized for a 16mm ball): printed socket retains the ball from below (ø10.2 opening < ball) and positions its bottom exactly at the ground plane, same contact level as the wheels.
- **Motor pocket sized to the real N20** (gearbox 12 × 10mm, 26mm long): internal width 12.8mm, shared pocket 53.2mm for the pair, axle bore ø3.6 + open-top drop-in notch.

### Automated fit audit — all pass

The build script runs 12 checks every time and refuses to claim success otherwise. Current result (see `FIT_AUDIT.txt`): plate-vs-interior, boss/hole coincidence, wheel-within-plate, motor pair length, motor width, wheel ground contact, ground clearance, caster ball to ground, caster retention, camera holes on PCB, Pi mount on deck, caster clear of pocket — **ALL PASS**.

## Parts + print settings (Ender 3 S1 Pro, 0.2mm layers, PLA/PETG)

| Part | Size (mm) | Orientation | Supports | Infill | Notes |
|---|---|---|---|---|---|
| head_shell | 159 x 159 x 200 | flat bottom down | None (ears lean gently, crown domes). Brim on | 10%, 3 walls | tall ~13-14hr. Ears + crown solid = strong |
| body_base | 133 x 117 x 90 | feet/pad down | Tree supports under arms + neck-ring overhang | 8%, 3 walls | carried over from v3 (per request) |
| chassis_plate | 104 x 104 x 52 | flat down | None | 40%, 4 walls | pocket walls + posts print vertical |
| pi_deck | 72 x 92 x 7 | flat, bosses up | None | 30% | disc, Pi mounts on M2.5 bosses |
| rear_hatch | 54 x 24 x 50 | outer face up, tree supports | Yes, minimal | 20% | |
| caster_cup | 37 x 19 x 11 | socket opening DOWN | None | 40% | drop ball in from top before fitting |

Print chassis_plate + caster_cup first with your actual motors, wheels, and ball to confirm the snug fits before the long shell print.

## Hardware (matches PARTS_AND_BUY_PLAN.md)

- 2x N20 6V micro gearmotor (100-200 rpm), gearbox 12×10mm, 3mm D-shaft. Pocket fits body length up to ~26mm.
- 2x N20 wheel 34×7mm, 3mm D-shaft ([Cytron](https://www.cytron.io/p-mini-wheel-34x7mm-for-n20-gear-motor), [Voltaat](https://www.voltaat.com/products/n20-micro-metal-gearmotor-wheel))
- 1x ½" (12.7mm) steel ball for the caster ([Pololu ½" ball](https://www.pololu.com/product/953)); a 12.7mm ball caster unit also works if you skip the printed cup
- TB6612FNG driver, Pi Camera Module 3, USB mic, MPU6050, 2S LiPo, UBEC 5V/3A, 12mm panel switch
- Screws: M3×8 self-tap (plate→shell ×4 countersunk from below, deck→posts ×4, hatch tabs ×2, caster cup→plate ×2), M2.5×6 (Pi ×4, MPU ×2), M2×5 (camera ×4)

## Layout (Z from ground, assembled)

Plate bottom = robot bottom at z0 (floats 4mm on the wheels). Plate deck z4-7 → both N20s in the shared pocket, axles at z17 → 2S battery flat on the pocket top → pi_deck at z56-59 on four posts, Pi ports facing the rear hatch → camera bolts to the face pad at z58, mic grille hidden behind the ears. Caster ball at the front, wheels at the sides, forming a stable triangle.

## Assembly

1. Flash SD first. 2. Drop the ball into the caster cup, screw the cup under the plate front (2× M3). 3. Both N20s drop into the shared pocket from above (shafts out through the end-wall bores/notches), press wheels on. 4. Battery flat on the pocket, velcro through the slots. 5. Pi + MPU on the deck (M2.5), deck onto the four posts (M3). 6. Camera onto the face pad (M2), route CSI + mic + power inside (battery → hatch switch → TB6612 VM + UBEC → Pi 5V). 7. Raise the plate into the head until it meets the ledge, 4× M3 up from below into the aligned bosses. 8. Hatch: tuck the top under the lip, 2× M3 into the tabs.

## Editing / fine-tuning later

- chassis_plate, pi_deck, caster_cup ship as STEP (clean B-rep solids) — edit directly in Fusion 360, FreeCAD, Onshape, SolidWorks.
- head_shell, body_base, rear_hatch are STL meshes (organic lofts) — edit in Blender / Meshmixer / Fusion Mesh workspace.
- Cleanest path for dimensional tweaks: change a value in `usagi_build4.py` (all real part dims are named constants at the top) and re-run; the fit audit re-checks everything automatically.

## Notes

- Ground clearance ~4mm, hard floors only.
- Confidence: geometry/alignment verified programmatically (100% within the model). Real-world fit ~95%, pending your specific N20 length and ball diameter — print the plate + cup first as a test.
