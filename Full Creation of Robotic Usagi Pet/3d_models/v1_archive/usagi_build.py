#!/usr/bin/env python3
# usagi robot printable parts generator
# coordinate system: Z0 = ground plane under the head unit, +Y = front (camera side)
# all dims mm. run with: python3 usagi_build.py <outdir>

import sys
import os
import cadquery as cq
from cadquery import exporters, Vector

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)

from OCP.ShapeFix import ShapeFix_Shape


def fix(wp):
    # occ booleans on the revolved splines sometimes come back invalid, heal them
    sf = ShapeFix_Shape(wp.val().wrapped)
    sf.Perform()
    return cq.Workplane("XY").add(cq.Shape.cast(sf.Shape()))


def box(cx, cy, cz, lx, ly, lz):
    # centered box helper
    return cq.Workplane("XY").box(lx, ly, lz).translate((cx, cy, cz))


def cyl(r, h, pnt, direction):
    # cylinder from a point along a direction
    return cq.Workplane("XY").add(
        cq.Solid.makeCylinder(r, h, Vector(*pnt), Vector(*direction))
    )


def cone(r1, r2, h, pnt, direction):
    return cq.Workplane("XY").add(
        cq.Solid.makeCone(r1, r2, h, Vector(*pnt), Vector(*direction))
    )


def sphere(r, pnt):
    return cq.Workplane("XY").add(cq.Solid.makeSphere(r, Vector(*pnt)))


def mirrored_x(wp_builder):
    # build a feature and its mirror across the YZ plane
    a = wp_builder(1)
    b = wp_builder(-1)
    return a.union(b)


# ---------------------------------------------------------------
# key shared parameters
WALL = 2.5
RIM_Z = 8.0            # shell bottom rim height above ground
AXLE_Z = 32.5          # wheel axle height (65mm wheel)
AXLE_Y = -10.0         # axle fore-aft position
PLATE_TOP = 23.25      # chassis plate top (motor lying flat, axle 9.25 above plate)
PLATE_BOT = PLATE_TOP - 3.0
BOSS_TOP = PLATE_BOT
BOSS_BOT = 14.0
DECK_BOT = 59.0
DECK_TOP = 62.0

# plate-to-shell screw points (M3)
PLATE_SCREWS = [(15.5, 58), (-15.5, 58), (8, -59), (-8, -59)]
# deck post positions
POSTS = [(35, 40), (-35, 40), (16.5, -58), (-16.5, -58)]

# ---------------------------------------------------------------
# HEAD SHELL
print("building head shell...")

outer = (
    cq.Workplane("XZ")
    .moveTo(0, RIM_Z)
    .lineTo(66, RIM_Z)
    .spline([(73, 30), (75, 60), (68, 95), (48, 118), (0, 136)], includeCurrent=True)
    .close()
    .revolve(360, (0, 0), (0, 1))
)

# manual offset inner solid instead of occ shell (shell() gave an invalid solid)
inner = (
    cq.Workplane("XZ")
    .moveTo(0, 4)
    .lineTo(63.5, 4)
    .spline([(70.5, 30), (72.5, 60), (65.5, 94), (46, 116.5), (0, 133.5)], includeCurrent=True)
    .close()
    .revolve(360, (0, 0), (0, 1))
)
# interior pads and bosses are subtracted from the cavity instead of
# unioned onto the shell — avoids tangent-face booleans that break occ
cavity = inner
cavity = cavity.cut(box(0, 65, 70, 30, 14, 24))         # camera pad, face plane y=58
cavity = cavity.cut(box(25, 62, 92, 34, 20, 34))        # eye pads, face plane y=52
cavity = cavity.cut(box(-25, 62, 92, 34, 20, 34))
# hatch screw tabs (recessed behind the panel, lower corners)
cavity = cavity.cut(box(24, -68, 36, 12, 4, 16))
cavity = cavity.cut(box(-24, -68, 36, 12, 4, 16))
# hatch top tuck-lip
cavity = cavity.cut(box(0, -65, 86, 40, 3, 12))
# chassis plate bosses (plate rests on top, screws down into pilots)
bh = (BOSS_TOP + BOSS_BOT) / 2
bt = BOSS_TOP - BOSS_BOT
cavity = cavity.cut(box(15.5, 62, bh, 12, 16, bt))
cavity = cavity.cut(box(-15.5, 62, bh, 12, 16, bt))
cavity = cavity.cut(box(8, -63, bh, 12, 16, bt))
cavity = cavity.cut(box(-8, -63, bh, 12, 16, bt))

head = outer.cut(cavity)
# ear stubs (stand proud of the shell)
head = head.union(cyl(8, 24, (24, 0, 124), (0, 0, 1)))
head = head.union(cyl(8, 24, (-24, 0, 124), (0, 0, 1)))
head = fix(head)

# camera mount pilot holes cut first, while the shape is still clean
# (M2 self-tap, cam module 3: 21 x 12.5 pattern, blind, start proud of pad face)
for dx in (10.5, -10.5):
    for dz in (6.25, -6.25):
        head = head.cut(cyl(0.9, 7.5, (dx, 56.5, 70 + dz), (0, 1, 0)))

# wheel arches: box + semicircular arch top
def arch(side):
    b = box(side * 66, AXLE_Y, 17, 48, 72, 38)  # X 42..90, Y -46..26, Z -2..36
    c = (
        cq.Workplane("YZ")
        .center(AXLE_Y, 36)
        .circle(36)
        .extrude(48 * side)
        .translate((side * 42, 0, 0))
    )
    return b.union(c)

head = head.cut(arch(1)).cut(arch(-1))

# eye windows + oled slide-in slots (module drops in from below, friction/glue)
for s in (1, -1):
    head = head.cut(box(s * 25, 65, 92, 24, 30, 12))          # window
    head = head.cut(box(s * 25, 55.7, 90, 27.8, 4.6, 32))     # pcb slot

# camera: lens bore + widened outer to avoid fov vignette
head = head.cut(cyl(5, 30, (0, 50, 70), (0, 1, 0)))
head = head.cut(cone(5, 10, 10, (0, 66, 70), (0, 1, 0)))
# mic grille (vertical holes through top)
for (mx, my) in [(0, 18), (7, 14), (-7, 14), (7, 22), (-7, 22)]:
    head = head.cut(cyl(1.5, 25, (mx, my, 118), (0, 0, 1)))

# ear stub cross holes for cloth ear zip ties
head = head.cut(cyl(1.6, 24, (24, -12, 142), (0, 1, 0)))
head = head.cut(cyl(1.6, 24, (-24, -12, 142), (0, 1, 0)))

# rear hatch opening (rounded rect, Z32..86, X +-35)
hatch_cut = (
    cq.Workplane("XZ")
    .center(0, 59)
    .sketch()
    .rect(70, 54)
    .vertices()
    .fillet(8)
    .finalize()
    .extrude(80)  # normal of XZ is -Y, so this goes rearward
)
head = head.cut(hatch_cut)

# pilot holes in hatch tabs (M3 self-tap)
head = head.cut(cyl(1.25, 16, (24, -74, 38), (0, 1, 0)))
head = head.cut(cyl(1.25, 16, (-24, -74, 38), (0, 1, 0)))

# pilot holes in plate bosses (M3 self-tap, drilled from top)
for (sx, sy) in PLATE_SCREWS:
    head = head.cut(cyl(1.25, 10, (sx, sy, 12), (0, 0, 1)))

# ---------------------------------------------------------------
# REAR HATCH panel (curved piece matching the opening, 0.5mm gap/side)
print("building hatch...")
hatch_small = (
    cq.Workplane("XZ")
    .center(0, 59)
    .sketch()
    .rect(69, 53)
    .vertices()
    .fillet(7.5)
    .finalize()
    .extrude(80)
)
hatch = fix(outer.cut(inner)).intersect(hatch_small)
# screw clearance holes aligned with tabs
hatch = hatch.cut(cyl(1.7, 20, (24, -78, 38), (0, 1, 0)))
hatch = hatch.cut(cyl(1.7, 20, (-24, -78, 38), (0, 1, 0)))
# power switch hole (12mm panel switch)
hatch = hatch.cut(cyl(6.25, 20, (-18, -78, 70), (0, 1, 0)))

# ---------------------------------------------------------------
# CHASSIS PLATE
print("building chassis plate...")
plate = cyl(64, 3.0, (0, 0, PLATE_BOT), (0, 0, 1))
# wheel zone side cuts
plate = plate.cut(box(54, -9, PLATE_BOT + 1.5, 22, 70, 5))
plate = plate.cut(box(-54, -9, PLATE_BOT + 1.5, 22, 70, 5))

RIB_TOP = 44.0
rib_h = RIB_TOP - PLATE_TOP
rib_cz = (RIB_TOP + PLATE_TOP) / 2
for s in (1, -1):
    # motor channel ribs: inner X 14.5..17.5, outer X 40..43
    for (ya, yb) in [(-62, -45), (-30, -2)]:
        ly = yb - ya
        cy = (ya + yb) / 2
        plate = plate.union(box(s * 16, cy, rib_cz, 3, ly, rib_h))
        plate = plate.union(box(s * 41.5, cy, rib_cz, 3, ly, rib_h))
    # motor front end stop
    plate = plate.union(box(s * 28.75, 2.5, PLATE_TOP + 5.35, 22.5, 3, 10.7))
    # deck posts
    plate = plate.union(box(s * 35, 40, (PLATE_TOP + DECK_BOT) / 2, 6, 6, DECK_BOT - PLATE_TOP))
    plate = plate.union(box(s * 16.5, -58, (PLATE_TOP + DECK_BOT) / 2, 6, 6, DECK_BOT - PLATE_TOP))
    # post pilot holes (M3 self-tap)
    plate = plate.cut(cyl(1.25, 9, (s * 35, 40, DECK_BOT - 9), (0, 0, 1)))
    plate = plate.cut(cyl(1.25, 9, (s * 16.5, -58, DECK_BOT - 9), (0, 0, 1)))
    # TT motor bolt slots (M3, slotted for gearbox hole variance)
    for ys in (-10.5, -28):
        plate = plate.cut(box(s * 28.75, ys, PLATE_BOT + 1.5, 3.4, 12, 8))
    # battery strap slots
    for ys in (-37, 25):
        plate = plate.cut(box(s * 14.75, ys, PLATE_BOT + 1.5, 3.2, 10, 40))
# shell screw clearance holes
for (sx, sy) in PLATE_SCREWS:
    plate = plate.cut(cyl(1.7, 8, (sx, sy, PLATE_BOT - 1), (0, 0, 1)))
# caster mount holes (M3 through, nut on top)
plate = plate.cut(cyl(1.7, 8, (15, 45, PLATE_BOT - 1), (0, 0, 1)))
plate = plate.cut(cyl(1.7, 8, (-15, 45, PLATE_BOT - 1), (0, 0, 1)))
# zip anchor holes
for (zx, zy) in [(32, 33), (-32, 33), (5, -60), (-5, -60)]:
    plate = plate.cut(cyl(2, 8, (zx, zy, PLATE_BOT - 1), (0, 0, 1)))

# ---------------------------------------------------------------
# PI DECK
print("building pi deck...")
deck = box(0, -9, (DECK_BOT + DECK_TOP) / 2, 76, 110, 3)
deck = deck.intersect(cyl(68, 20, (0, 0, 50), (0, 0, 1)))
# post screw clearance
for (px, py) in POSTS:
    deck = deck.cut(cyl(1.7, 8, (px, py, DECK_BOT - 1), (0, 0, 1)))
# pi standoff bosses (58 x 49 pattern, ports face rear hatch), M2.5 self-tap
for bx in (24.5, -24.5):
    for by in (-39, 19):
        deck = deck.union(cyl(3, 4, (bx, by, DECK_TOP), (0, 0, 1)))
        deck = deck.cut(cyl(1.1, 12, (bx, by, DECK_BOT - 1), (0, 0, 1)))
# mpu6050 pilot holes on rear strip (M2.5 self-tap, 15mm spacing)
for mx in (17.5, 32.5):
    deck = deck.cut(cyl(1.1, 8, (mx, -52, DECK_BOT - 1), (0, 0, 1)))

# ---------------------------------------------------------------
# CASTER MOUNT (16mm / 5/8in steel ball, drop in from top, plate retains it)
print("building caster mount...")
CC = (0, 45)
caster = box(CC[0], CC[1], (3 + PLATE_BOT) / 2, 26, 26, PLATE_BOT - 3)
caster = caster.union(box(17, 45, PLATE_BOT - 1.5, 8, 10, 3))
caster = caster.union(box(-17, 45, PLATE_BOT - 1.5, 8, 10, 3))
caster = caster.cut(cyl(8.3, 20, (CC[0], CC[1], 8), (0, 0, 1)))   # top-open bore
caster = caster.cut(sphere(8.3, (CC[0], CC[1], 8)))               # ball seat
caster = caster.cut(cyl(1.7, 8, (15, 45, 16), (0, 0, 1)))
caster = caster.cut(cyl(1.7, 8, (-15, 45, 16), (0, 0, 1)))

# ---------------------------------------------------------------
# BODY BASE (cosmetic stand; head parks over the top plug, plate rests at Z110)
print("building body base...")
base_solid = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(78, 0)
    .spline([(80, 30), (74, 60), (60, 85), (48, 100), (0, 114)], includeCurrent=True)
    .close()
    .revolve(360, (0, 0), (0, 1))
)
# flatten the top so the chassis plate has a seat
base_solid = base_solid.cut(box(0, 0, 125, 200, 200, 30))
# wheel grooves
base_solid = base_solid.cut(box(61.5, -10, 103, 37, 68, 34))
base_solid = base_solid.cut(box(-61.5, -10, 103, 37, 68, 34))
# caster relief
base_solid = base_solid.cut(box(0, 45, 102, 32, 34, 32))
# hollow it (3mm wall, open bottom) via manual offset inner solid
base_inner = (
    cq.Workplane("XZ")
    .moveTo(0, -2)
    .lineTo(75, -2)
    .spline([(77, 30), (71, 60), (57, 84), (42, 94), (0, 104)], includeCurrent=True)
    .close()
    .revolve(360, (0, 0), (0, 1))
)
base = base_solid.cut(base_inner)

# ---------------------------------------------------------------
# EXPORT
parts = {
    "head_shell": head,
    "rear_hatch": hatch,
    "chassis_plate": plate,
    "pi_deck": deck,
    "caster_mount": caster,
    "body_base": base,
}

for name, wp in parts.items():
    wp = fix(wp)
    solid = wp.val()
    if not solid.isValid() or solid.Volume() <= 0:
        print(f"WARNING: {name} invalid or non-positive volume")
    bb = solid.BoundingBox()
    # drop each part onto Z0 for slicing convenience
    moved = wp.translate((0, 0, -bb.zmin))
    stl = os.path.join(OUT, f"{name}.stl")
    step = os.path.join(OUT, f"{name}.step")
    exporters.export(moved, stl, tolerance=0.05, angularTolerance=0.2)
    exporters.export(moved, step)
    # snap revolve-seam vertices and verify watertightness
    import trimesh
    m = trimesh.load(stl, process=False)
    m.vertices = m.vertices.round(2)
    m.merge_vertices()
    m.update_faces(m.nondegenerate_faces())
    m.fill_holes()
    trimesh.repair.fix_normals(m)
    if not m.is_watertight:
        # last resort: pymeshfix
        import pymeshfix
        import numpy as np
        vc, fc = pymeshfix.clean_from_arrays(np.asarray(m.vertices), np.asarray(m.faces))
        import trimesh as tm
        m2 = tm.Trimesh(vc, fc)
        if m2.is_watertight and abs(m2.volume - m.volume) < 0.05 * abs(m.volume):
            m = m2
    if m.is_watertight and m.volume > 0:
        m.export(stl)
    bb2 = moved.val().BoundingBox()
    print(
        f"{name}: {bb2.xlen:.1f} x {bb2.ylen:.1f} x {bb2.zlen:.1f} mm, "
        f"vol {moved.val().Volume()/1000:.1f} cm3, watertight {m.is_watertight}"
    )

print("done")
