#!/usr/bin/env python3
# usagi robot printable parts, v2 — anime-accurate shapes from model.glb
# head + body come from the reference mesh, functional parts from cadquery,
# combined with manifold mesh booleans.
# coords: Z0 = ground under head unit, +Y = face direction. dims mm.
# drive: 2x N20 micro gearmotor + 34x7mm wheels, fully concealed, flat bottom.

import sys, os
import numpy as np
import trimesh
from trimesh import creation, boolean, transformations as tra

GLB = "/sessions/modest-relaxed-fermi/mnt/uploads/model.glb"
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)

ENG = "manifold"


def u(meshes):
    return boolean.union(meshes, engine=ENG)


def d(a, b):
    return boolean.difference([a, b], engine=ENG)


def i(a, b):
    return boolean.intersection([a, b], engine=ENG)


def bx(cx, cy, cz, lx, ly, lz):
    T = tra.translation_matrix((cx, cy, cz))
    return creation.box((lx, ly, lz), transform=T)


def cylz(r, z0, z1, cx=0, cy=0):
    T = tra.translation_matrix((cx, cy, (z0 + z1) / 2))
    return creation.cylinder(radius=r, height=z1 - z0, sections=48, transform=T)


def cyly(r, y0, y1, cx=0, cz=0):
    R = tra.rotation_matrix(np.pi / 2, (1, 0, 0))
    T = tra.translation_matrix((cx, (y0 + y1) / 2, cz))
    return creation.cylinder(radius=r, height=abs(y1 - y0), sections=48, transform=np.dot(T, R))


def rrect_y(w, h, rad, cx, cz, y0, y1):
    # rounded rectangle prism along y (w across x, h across z)
    parts = [
        bx(cx, (y0 + y1) / 2, cz, w - 2 * rad, y1 - y0, h),
        bx(cx, (y0 + y1) / 2, cz, w, y1 - y0, h - 2 * rad),
    ]
    for sx in (1, -1):
        for sz in (1, -1):
            parts.append(cyly(rad, y0, y1, cx + sx * (w / 2 - rad), cz + sz * (h / 2 - rad)))
    return u(parts)


def slice_keep_above(m, z, cap=True):
    # boolean halfspace clip — more robust than slice_plane capping
    return i(m, bx(0, 0, z + 300, 900, 900, 600))


def slice_keep_below(m, z, cap=True):
    return i(m, bx(0, 0, z - 300, 900, 900, 600))


# ---------------------------------------------------------------
# load reference, orient z-up with face toward +y
scene = trimesh.load(GLB)
ref = scene.to_mesh()
M = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
ref.apply_transform(M)
ref.apply_transform(tra.rotation_matrix(np.pi, (0, 0, 1)))  # face was -y, flip to +y

# measure head width (widest x extent in the head band) and the neck waist
def xw_at(m, z):
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        return 0
    v = s.vertices
    return v[:, 0].max() - v[:, 0].min()

zs = np.linspace(-0.2, 0.1, 16)
head_w = max(xw_at(ref, z) for z in zs)
zs = np.linspace(-0.50, -0.36, 15)
z_waist = min(zs, key=lambda z: xw_at(ref, z))
S = 160.0 / head_w
print(f"glb head width {head_w:.3f} -> scale {S:.2f}, waist at z={z_waist:.3f}")

ref.apply_scale(S)
zw = z_waist * S

# the glb is 89 open surface patches, not a solid — voxel-remesh to a
# guaranteed watertight volume, then smooth the marching cubes steps away
print("voxel remeshing reference...")
vg = ref.voxelized(pitch=1.0).fill()
solid = vg.marching_cubes
solid.apply_transform(vg.transform)
import trimesh.smoothing as smooth
smooth.filter_taubin(solid, lamb=0.5, nu=-0.53, iterations=14)
solid.merge_vertices()
assert solid.is_volume
ref = solid

# ---------------------------------------------------------------
# key layout constants
PLATE_R = 47.0               # interior min radius at plate level is 48.3
PLATE_BOT, PLATE_TOP = 4.0, 7.0
AXLE_Z = 17.0                # 34mm wheel
AXLE_L, AXLE_R = -2.0, -18.0 # staggered n20 axles (left / right)
DECK_BOT, DECK_TOP = 56.0, 59.0
PLATE_SCREWS = [(24, 34), (-24, 34), (18, -40), (-18, -40)]
POSTS = [(28, 33), (-28, 33), (21, -38), (-21, -38)]
CASTER = (0.0, 34.0)         # 16mm ball, center
CAM_Z = 62.0

# ---------------------------------------------------------------
# HEAD SHELL
print("building head shell...")
head_ref = ref.copy()
head_ref.apply_translation((0, 0, 4.0 - zw))      # waist plane -> Z4
outer = slice_keep_above(head_ref, 4.0)

# inner cavity: uniform-ish scaled copy about the ball center, ears stay solid
ball_top = 4.0 + (0.40 * S - zw)                  # ear-base height
bc = np.array([0, 0, (4.0 + ball_top) / 2])
inner_full = head_ref.copy()
inner_full.apply_translation(-bc)
inner_full.apply_scale(1 - 5.6 / 160.0)           # ~2.8mm wall
inner_full.apply_translation(bc)
inner = slice_keep_below(slice_keep_above(inner_full, 0.0), ball_top - 12)

shell = d(outer, inner)

# interior adds, trimmed to the outer surface so nothing pokes through
adds = [
    bx(0, 70, CAM_Z, 26, 20, 24),                 # camera pad, face plane y=60
    bx(18, -72, 36, 12, 20, 16),                  # hatch tab, lower corners
    bx(-18, -72, 36, 12, 20, 16),
    bx(0, -68, 83, 36, 7, 10),                    # hatch top tuck-lip
]
for (sx, sy) in PLATE_SCREWS:
    th = np.arctan2(sy, sx)
    T = np.dot(tra.translation_matrix((np.cos(th) * 48, np.sin(th) * 48, 10)),
               tra.rotation_matrix(th, (0, 0, 1)))
    adds.append(creation.box((20, 12, 6), transform=T))  # boss pad r42..62
adds_m = i(u(adds), outer)
shell = u([shell, adds_m])

# hatch opening, rounded rect 56 x 50 centered z55
hatch_cut = rrect_y(56, 50, 8, 0, 55, -95, -56)
shell = d(shell, hatch_cut)

# camera: bore + stepped counterbore (avoids fov vignette), pilots
shell = d(shell, cyly(5, 55, 90, 0, CAM_Z))
shell = d(shell, cyly(9, 73, 90, 0, CAM_Z))
for dx in (10.5, -10.5):
    for dz in (6.25, -6.25):
        shell = d(shell, cyly(1.25, 58.5, 68, dx, CAM_Z + dz))

# mic grille behind the ears
for (mx, my) in [(0, -25), (7, -29), (-7, -29), (7, -21), (-7, -21)]:
    shell = d(shell, cylz(1.5, 95, 140, mx, my))

# hatch tab pilots (m3 self-tap)
for sx in (18, -18):
    shell = d(shell, cyly(1.25, -85, -60, sx, 38))

# plate boss pilots (m3 self-tap, from below)
for (sx, sy) in PLATE_SCREWS:
    shell = d(shell, cylz(1.25, 2, 13, sx, sy))

# ---------------------------------------------------------------
# REAR HATCH (matching curved panel, 1mm smaller per side)
print("building hatch...")
panel_zone = rrect_y(54, 48, 7, 0, 55, -95, -56)
hatch = i(d(outer, inner), panel_zone)
hatch = d(hatch, cyly(6.25, -95, -55, -14, 68))    # 12mm switch hole
for sx in (18, -18):
    hatch = d(hatch, cyly(1.7, -95, -55, sx, 38))  # screw clearance

# ---------------------------------------------------------------
# BODY BASE (solid, print with low infill)
print("building body base...")
body = ref.copy()
body.apply_translation((0, 0, -ref.bounds[0][2]))  # feet bottom -> Z0
Hb = zw - ref.bounds[0][2]                          # waist height in body coords
body = slice_keep_below(body, Hb)                   # remove head
body = slice_keep_above(body, 2.5)                  # flat feet
# elliptical foot support pad (60 x 44 x 3)
pad = creation.cylinder(radius=1.0, height=3.0, sections=64)
pad.apply_transform(np.diag([30.0, 22.0, 1.0, 1.0]))
pad.apply_translation((0, 2, 1.5))
# neck retaining ring (head parks inside)
ring = d(cylz(58.5, Hb - 10, Hb + 8), cylz(54.5, Hb - 12, Hb + 10))
body = u([body, pad, ring])

# ---------------------------------------------------------------
# CADQUERY PARTS (plate, deck, caster cup)
print("building chassis plate / deck / caster cup...")
import cadquery as cq
from cadquery import exporters, Vector
from OCP.ShapeFix import ShapeFix_Shape


def fixq(wp):
    sf = ShapeFix_Shape(wp.val().wrapped)
    sf.Perform()
    return cq.Workplane("XY").add(cq.Shape.cast(sf.Shape()))


def qbox(cx, cy, cz, lx, ly, lz):
    return cq.Workplane("XY").box(lx, ly, lz).translate((cx, cy, cz))


def qcyl(r, h, pnt, dirv):
    return cq.Workplane("XY").add(cq.Solid.makeCylinder(r, h, Vector(*pnt), Vector(*dirv)))


# chassis plate: flat bottom disc with wheel slots
plate = qcyl(PLATE_R, 3.0, (0, 0, PLATE_BOT), (0, 0, 1))
# wheel slots (staggered axles)
plate = plate.cut(qbox(-31.5, AXLE_L, PLATE_BOT + 1.5, 11, 38, 8))
plate = plate.cut(qbox(31.5, AXLE_R, PLATE_BOT + 1.5, 11, 38, 8))
# caster ball hole
plate = plate.cut(qcyl(7.0, 8, (CASTER[0], CASTER[1], PLATE_BOT - 1), (0, 0, 1)))

# n20 motor cradles: floor, side walls with snap lips, end walls with shaft hole
def cradle(p, x0, x1, yc, axle_y):
    # channel floor
    p = p.union(qbox((x0 + x1) / 2, yc, 9.5, x1 - x0, 12, 5))
    for sy in (1, -1):
        wall_y = yc + sy * 7.75
        p = p.union(qbox((x0 + x1) / 2, wall_y, 14.75, x1 - x0, 3.5, 15.5))
        # snap lip
        p = p.union(qbox((x0 + x1) / 2, yc + sy * 5.6, 21.9, x1 - x0, 0.8, 1.2))
    return p

# left motor: body x -26..0, axle y -2; right motor: body x 0..26, axle y -18
plate = cradle(plate, -26, 0, AXLE_L, AXLE_L)
plate = cradle(plate, 0, 26, AXLE_R, AXLE_R)
# end walls with shaft holes (also axial stops)
plate = plate.union(qbox(-26.75, AXLE_L, 14.75, 1.5, 15.5, 15.5))
plate = plate.cut(qcyl(2.6, 4, (-28, AXLE_L, AXLE_Z), (1, 0, 0)))
plate = plate.union(qbox(0.75, AXLE_L, 14.75, 1.5, 15.5, 15.5))
plate = plate.union(qbox(26.75, AXLE_R, 14.75, 1.5, 15.5, 15.5))
plate = plate.cut(qcyl(2.6, 4, (24, AXLE_R, AXLE_Z), (1, 0, 0)))
plate = plate.union(qbox(-0.75, AXLE_R, 14.75, 1.5, 15.5, 15.5))
# deck posts
for (px, py) in POSTS:
    plate = plate.union(qbox(px, py, (PLATE_TOP + DECK_BOT) / 2, 6, 6, DECK_BOT - PLATE_TOP))
    plate = plate.cut(qcyl(1.25, 9, (px, py, DECK_BOT - 9), (0, 0, 1)))
# shell screw holes, countersunk from below
for (sx, sy) in PLATE_SCREWS:
    plate = plate.cut(qcyl(1.7, 8, (sx, sy, PLATE_BOT - 1), (0, 0, 1)))
    plate = plate.cut(qcyl(3.25, 1.9, (sx, sy, PLATE_BOT - 0.1), (0, 0, 1)))
# battery strap slots
for (bxp, byp) in [(19.5, 20), (-19.5, 20), (19.5, -29), (-19.5, -29)]:
    plate = plate.cut(qbox(bxp, byp, PLATE_BOT + 1.5, 3.2, 10, 8))
# zip anchor holes
for (zx, zy) in [(34, 20), (-34, 20), (10, -42), (-10, -42)]:
    plate = plate.cut(qcyl(2.0, 8, (zx, zy, PLATE_BOT - 1), (0, 0, 1)))

# pi deck 76 x 92, posts + pi bosses
deck = qbox(0, -2, (DECK_BOT + DECK_TOP) / 2, 76, 92, 3)
for (px, py) in POSTS:
    deck = deck.cut(qcyl(1.7, 8, (px, py, DECK_BOT - 1), (0, 0, 1)))
for bxp in (24.5, -24.5):
    for byp in (-33, 25):
        deck = deck.union(qcyl(3, 4, (bxp, byp, DECK_TOP), (0, 0, 1)))
        deck = deck.cut(qcyl(1.1, 12, (bxp, byp, DECK_BOT - 1), (0, 0, 1)))
# mpu6050 pilots on rear strip
for mx in (10, -5):
    deck = deck.cut(qcyl(1.1, 8, (mx, -42, DECK_BOT - 1), (0, 0, 1)))

# caster cup: spherical seat over the 16mm ball, screws onto plate top
cup = qbox(CASTER[0], CASTER[1], (PLATE_TOP + 18) / 2, 22, 22, 18 - PLATE_TOP)
cup = cup.union(qbox(15, CASTER[1], PLATE_TOP + 1.5, 8, 10, 3))
cup = cup.union(qbox(-15, CASTER[1], PLATE_TOP + 1.5, 8, 10, 3))
cup = cup.cut(cq.Workplane("XY").add(
    cq.Solid.makeSphere(8.3, Vector(CASTER[0], CASTER[1], 8.0))))
cup = cup.cut(qcyl(8.3, 4, (CASTER[0], CASTER[1], 4), (0, 0, 1)))  # entry from below
cup = cup.cut(qcyl(1.7, 8, (15, CASTER[1], 5), (0, 0, 1)))
cup = cup.cut(qcyl(1.7, 8, (-15, CASTER[1], 5), (0, 0, 1)))

# ---------------------------------------------------------------
# EXPORT
def finalize_mesh(m, name):
    mm = m.copy()
    mm.apply_translation((0, 0, -mm.bounds[0][2]))
    mm.merge_vertices()
    if not mm.is_watertight:
        import pymeshfix
        vc, fc = pymeshfix.clean_from_arrays(np.asarray(mm.vertices), np.asarray(mm.faces))
        m2 = trimesh.Trimesh(vc, fc)
        if m2.is_watertight and abs(m2.volume - mm.volume) < 0.05 * abs(mm.volume):
            mm = m2
    path = os.path.join(OUT, f"{name}.stl")
    mm.export(path)
    e = mm.extents
    print(f"{name}: {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm, vol {mm.volume/1000:.1f} cm3, watertight {mm.is_watertight}")


def finalize_cq(wp, name):
    wp = fixq(wp)
    bb = wp.val().BoundingBox()
    moved = wp.translate((0, 0, -bb.zmin))
    stl = os.path.join(OUT, f"{name}.stl")
    exporters.export(moved, stl, tolerance=0.05, angularTolerance=0.2)
    exporters.export(moved, os.path.join(OUT, f"{name}.step"))
    m = trimesh.load(stl, process=False)
    m.vertices = m.vertices.round(2)
    m.merge_vertices()
    m.update_faces(m.nondegenerate_faces())
    m.fill_holes()
    trimesh.repair.fix_normals(m)
    if m.is_watertight and m.volume > 0:
        m.export(stl)
    else:
        m = trimesh.load(stl)
    print(f"{name}: {m.extents[0]:.1f} x {m.extents[1]:.1f} x {m.extents[2]:.1f} mm, watertight {m.is_watertight}")


finalize_mesh(shell, "head_shell")
finalize_mesh(hatch, "rear_hatch")
finalize_mesh(body, "body_base")
finalize_cq(plate, "chassis_plate")
finalize_cq(deck, "pi_deck")
finalize_cq(cup, "caster_cup")
print("done")
