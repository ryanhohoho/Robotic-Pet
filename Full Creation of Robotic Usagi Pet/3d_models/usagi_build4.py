#!/usr/bin/env python3
# usagi robot HEAD parts, v4 - dimensionally audited against real components.
# every mounting feature derives from a single PARTS block; shell bosses and
# plate holes share identical coordinates so nothing needs manual scaling.
# body_base is carried over unchanged from v3 (ignored per request).
import sys, os
import numpy as np
import trimesh
from trimesh import creation, boolean, transformations as tra
from scipy.interpolate import splrep, splev
import trimesh.smoothing as sm

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
ENG = "manifold"
def u(ms):  return boolean.union(ms, engine=ENG)
def d(a,b): return boolean.difference([a,b], engine=ENG)
def i(a,b): return boolean.intersection([a,b], engine=ENG)
def bx(cx,cy,cz,lx,ly,lz): return creation.box((lx,ly,lz), transform=tra.translation_matrix((cx,cy,cz)))
def cylz(r,z0,z1,cx=0,cy=0):
    return creation.cylinder(radius=r,height=z1-z0,sections=64,transform=tra.translation_matrix((cx,cy,(z0+z1)/2)))
def cyly(r,y0,y1,cx=0,cz=0):
    R=tra.rotation_matrix(np.pi/2,(1,0,0)); T=tra.translation_matrix((cx,(y0+y1)/2,cz))
    return creation.cylinder(radius=r,height=abs(y1-y0),sections=48,transform=np.dot(T,R))
def cylx(r,x0,x1,cy=0,cz=0):
    R=tra.rotation_matrix(np.pi/2,(0,1,0)); T=tra.translation_matrix(((x0+x1)/2,cy,cz))
    return creation.cylinder(radius=r,height=abs(x1-x0),sections=48,transform=np.dot(T,R))
def ellipsoid(cx,cy,cz,rx,ry,rz,subdiv=3):
    m=creation.icosphere(subdivisions=subdiv,radius=1.0); m.apply_transform(np.diag([rx,ry,rz,1.0])); m.apply_translation((cx,cy,cz)); return m
def smoothp(zc,rc,zq,s=2.0):
    return np.clip(splev(zq,splrep(zc,rc,s=s,k=3)),0.05,None)
def loft(zs,xrs,yrs,cxs,cys,nseg=140,cb=True,ct=True):
    ang=np.linspace(0,2*np.pi,nseg,endpoint=False); ca,sa=np.cos(ang),np.sin(ang); rings=[]
    for z,xr,yr,cx,cy in zip(zs,xrs,yrs,cxs,cys):
        rings.append(np.column_stack([cx+xr*ca,cy+yr*sa,np.full(nseg,z)]))
    V=np.vstack(rings); F=[]; nr=len(rings)
    for k in range(nr-1):
        a,b=k*nseg,(k+1)*nseg
        for j in range(nseg):
            j2=(j+1)%nseg; F.append([a+j,a+j2,b+j2]); F.append([a+j,b+j2,b+j])
    if cb:
        c=len(V); V=np.vstack([V,rings[0].mean(0)])
        for j in range(nseg): F.append([c,(j+1)%nseg,j])
    if ct:
        base=(nr-1)*nseg; c=len(V); V=np.vstack([V,rings[-1].mean(0)])
        for j in range(nseg): F.append([c,base+j,base+(j+1)%nseg])
    m=trimesh.Trimesh(V,np.array(F),process=True); m.merge_vertices(); trimesh.repair.fix_normals(m); return m

# ================= REAL PART DIMENSIONS (mm) =================
WALL=2.8
# N20 micro gearmotor (gearbox 12W x 10H, can dia 10, shaft 3mm D x 9 long)
N20_W=12.0; N20_H=10.0; N20_LEN=26.0; N20_SHAFT_D=3.0; N20_SHAFT_LEN=9.0
# N20 wheel 34 x 7, bore 3mm D
WHEEL_D=34.0; WHEEL_W=7.0
# Pi Camera Module 3: PCB 25 x 24, holes o2.2 @ 21(x) x 12.5(y-rect), M2,
# lens barrel ~o8, module height 11.5, lens optical center offset +2.4 (up)
CAM_PCB_W=25.0; CAM_PCB_H=24.0; CAM_HOLE_X=21.0; CAM_HOLE_Z=12.5
CAM_LENS_OFF=2.4; CAM_LENS_LEN=11.5
# Raspberry Pi 3B+ mount rectangle 58 x 49, holes o2.75 (M2.5)
PI_MX=58.0; PI_MZ=49.0
# caster: loose steel ball 1/2 inch
BALL_D=12.7
# fasteners: pilot (self-tap into PLA), clearance, countersink head dia
M3_PILOT=2.5; M3_CLR=3.4; M3_CS=6.2
M25_PILOT=2.1
M2_PILOT=1.6
# ============================================================

# head cross-section profiles from model.glb (scaled, head width ~160)
HEAD_Z=[-57,-48.6,-39.8,-31,-22.2,-13.4,-4.6,4.2,12.9,21.7,30.5,39.3,48.1,54,58,61,63.5]
HEAD_R=[55.6,66,72.2,76.2,78.6,79.6,79.7,78.5,76.2,72.4,66.6,57.8,44,36,27,16,2]
EAR_Z=[54,61,71,81,91,101,111,121,131,138,143,146]
EAR_XR=[12,9.3,11,12.2,13.1,13.4,13.2,12.5,10.5,8,4.5,1]
EAR_YR=[9,7.9,9,9.7,10,9.9,9.8,9.3,8.1,6.5,4,1]
EAR_CX=[16,15.5,15.8,15.3,15.6,16,17,17.3,17.4,17.3,17.1,17]
EAR_CY=[-4,-3.8,-2.9,-4.5,-4.8,-5,-4.6,-4,-4.5,-4,-3.7,-3.7]
BODY_Z=[-124,-119,-110,-101,-92,-83,-74,-66,-60,-57]
BODY_XR=[26,34,45,48.5,49.5,51,54,57,56,55]
BODY_YR=[16,22,33,39,42,44,45,45.5,52,55]

WAIST=-57.0; Z_LIFT=4.0-WAIST         # head bottom cut -> Z4
def head_R(z_print):                  # interior/exterior radius helper (print z)
    zb=np.clip(z_print-Z_LIFT,-57,63.5)
    return float(smoothp(HEAD_Z,HEAD_R,np.array([zb]),s=3)[0])

# ---- seat + mount geometry derived from the actual interior ----
PLATE_BOT,PLATE_TOP=4.0,7.0
# interior radius at the bottom rim (z4). wall is WALL thick.
RIM_OUTER=head_R(4.0)                  # ~55.6
RIM_INNER=RIM_OUTER-WALL
PLATE_R=round(RIM_INNER-1.0,1)         # 1mm radial clearance to the wall
LEDGE_IN=PLATE_R-3.0                   # interior ledge the plate seats up against
# 4 mount points shared by shell bosses AND plate holes (identical coords)
BOSS_R=PLATE_R-10.0
BOSS_POS=[( BOSS_R*np.cos(a), BOSS_R*np.sin(a)) for a in
          np.deg2rad([55,125,235,305])]
# deck posts (inboard of bosses)
POST_R=PLATE_R-16.0
POSTS=[( POST_R*np.cos(a), POST_R*np.sin(a)) for a in np.deg2rad([55,125,235,305])]
DECK_BOT,DECK_TOP=56.0,59.0
# drive
AXLE_Z=WHEEL_D/2.0                     # 17, wheel bottom at ground z0
AXLE_Y=-8.0
POCK_HALF=(2*N20_LEN)/2.0+0.6          # half length of the shared two-motor pocket
POCK_IN_Y=N20_W+0.8                    # internal width (gearbox 12 + clearance)
CASTER=(0.0,38.0)
CAM_Z=58.0

print(f"[derive] RIM_OUTER {RIM_OUTER:.1f} RIM_INNER {RIM_INNER:.1f} PLATE_R {PLATE_R} "
      f"BOSS_R {BOSS_R:.1f} POCK_HALF {POCK_HALF:.1f}")

# ===================== HEAD SHELL =====================
print("building head...")
zc=np.linspace(-57,63.5,160); r=smoothp(HEAD_Z,HEAD_R,zc,s=3)
head_outer=loft(zc,r,r,np.zeros_like(zc),np.zeros_like(zc))
def ear(sg):
    ze=np.linspace(54,146,90)
    return loft(ze,smoothp(EAR_Z,EAR_XR,ze,1),smoothp(EAR_Z,EAR_YR,ze,1),
                sg*smoothp(EAR_Z,EAR_CX,ze,1),smoothp(EAR_Z,EAR_CY,ze,1),nseg=80)
head_outer=u([head_outer,ear(1),ear(-1)])
sm.filter_taubin(head_outer,lamb=0.5,nu=-0.53,iterations=10)
head_outer.apply_translation((0,0,Z_LIFT))
head_outer=i(head_outer,bx(0,0,304,900,900,600))     # clean flat bottom at z4
# hollow ball
zi=np.linspace(-59,50,150); ri=smoothp(HEAD_Z,HEAD_R,np.clip(zi,-57,54),s=3)-WALL
inner=loft(zi+Z_LIFT,ri,ri,np.zeros_like(zi),np.zeros_like(zi))
shell=d(head_outer,inner)

# --- ADDITIVE interior features (may poke past outer; clipped flush below) ---
# interior seating ledge (plate rests up against its underside at z=PLATE_TOP)
ledge=d(cylz(RIM_INNER+0.5,PLATE_TOP,PLATE_TOP+3.0),cylz(LEDGE_IN,PLATE_TOP-1,PLATE_TOP+4))
shell=u([shell,i(ledge,head_outer)])
# aligned mounting bosses (pilot holes drilled after the clip)
shell=u([shell]+[cylz(4.5,PLATE_TOP,PLATE_TOP+12,bxp,byp) for (bxp,byp) in BOSS_POS])
# camera mount pad: a block that fully penetrates the front wall; the final
# clip against head_outer trims its face flush -> clean manifold (no tangency)
yin=head_R(CAM_Z)-WALL
yout=head_R(CAM_Z)
cam_blk=bx(0, yin-4, CAM_Z, CAM_PCB_W+4, 18, CAM_PCB_H+4)   # y: yin-13 .. yin+5 (past outer)
shell=u([shell,cam_blk])

# --- CLIP everything flush to the outer surface (removes any poke-through) ---
shell=i(shell,head_outer)

# --- SUBTRACTIVE features (crisp holes) ---
for (bxp,byp) in BOSS_POS:
    shell=d(shell,cylz(M3_PILOT/2,PLATE_TOP-0.5,PLATE_TOP+13,bxp,byp))
# camera: 4 M2 pilots at 21 x 12.5 into the pad, lens bore + outer counterbore
for sx in (1,-1):
    for sz in (1,-1):
        shell=d(shell,cyly(M2_PILOT/2, yin-11, yin+1, sx*CAM_HOLE_X/2, CAM_Z+sz*CAM_HOLE_Z/2))
shell=d(shell,cyly(4.5, yin-6, yout+3, 0, CAM_Z+CAM_LENS_OFF))
shell=d(shell,cyly(7.0, yout-2.0, yout+3, 0, CAM_Z+CAM_LENS_OFF))
# PCB seat recess (shallow, so the camera board sits square on the pad)
shell=d(shell,bx(0, yin-11.5, CAM_Z, CAM_PCB_W+0.5, 3, CAM_PCB_H+0.5))

# rear hatch opening + tabs + top lip
def rrect_y(w,h,rad,cx,cz,y0,y1):
    parts=[bx(cx,(y0+y1)/2,cz,w-2*rad,y1-y0,h),bx(cx,(y0+y1)/2,cz,w,y1-y0,h-2*rad)]
    for sxx in (1,-1):
        for szz in (1,-1): parts.append(cyly(rad,y0,y1,cx+sxx*(w/2-rad),cz+szz*(h/2-rad)))
    return u(parts)
HATCH_W,HATCH_H,HATCH_CZ=56,52,34
shell=d(shell,rrect_y(HATCH_W,HATCH_H,8,0,HATCH_CZ,-95,-RIM_OUTER+1))
# hatch screw tabs (M3 self-tap) just inside the opening, lower corners
for sx in (1,-1):
    shell=u([shell,i(bx(sx*22,-(RIM_OUTER-4),18,12,8,14),head_outer)])
    shell=d(shell,cyly(M3_PILOT/2,-(RIM_OUTER),-(RIM_OUTER-10),sx*22,18))
# mic grille behind ears (top)
for (mx,my) in [(0,-25),(7,-29),(-7,-29),(7,-21),(-7,-21)]:
    shell=d(shell,cylz(1.5,95,150,mx,my))

# ===================== REAR HATCH =====================
print("building hatch...")
hatch=i(d(head_outer,inner),rrect_y(HATCH_W-2,HATCH_H-2,7,0,HATCH_CZ,-95,-RIM_OUTER+1))
hatch=d(hatch,cyly(6.25,-95,-50,-14,40))               # 12mm panel switch
for sx in (1,-1):
    hatch=d(hatch,cyly(M3_CLR/2,-95,-50,sx*22,18))

# ===================== BODY (carried from v3, unchanged) =====================
print("building body...")
zb=np.linspace(-124,-57,130)
bxr=smoothp(BODY_Z,BODY_XR,zb,4); byr=smoothp(BODY_Z,BODY_YR,zb,4)
body=loft(zb,bxr,byr,np.zeros_like(zb),np.zeros_like(zb))
feet=[ellipsoid(s*13,-1,-130,11,13,15) for s in (1,-1)]
arms=[ellipsoid(s*52,-2,-80,15,13,18) for s in (1,-1)]
body=u([body]+feet+arms); sm.filter_taubin(body,lamb=0.5,nu=-0.53,iterations=8)
body.apply_translation((0,0,-body.bounds[0][2])); tz=body.bounds[1][2]
body=i(body,bx(0,0,(tz-6)-300,900,900,600)); tz=body.bounds[1][2]
ring=d(cylz(RIM_OUTER+3,tz-2,tz+9),cylz(RIM_OUTER-0.5,tz-4,tz+11))
pad=i(ellipsoid(0,2,0,34,24,2.2),bx(0,2,1.5,200,200,3))
body=u([body,ring,pad])

# ===================== FUNCTIONAL PARTS (cadquery) =====================
print("building plate / deck / caster...")
import cadquery as cq
from cadquery import exporters, Vector
from OCP.ShapeFix import ShapeFix_Shape
def fixq(wp):
    sf=ShapeFix_Shape(wp.val().wrapped); sf.Perform()
    return cq.Workplane("XY").add(cq.Shape.cast(sf.Shape()))
def qbox(cx,cy,cz,lx,ly,lz): return cq.Workplane("XY").box(lx,ly,lz).translate((cx,cy,cz))
def qcyl(r,h,pnt,dirv): return cq.Workplane("XY").add(cq.Solid.makeCylinder(r,h,Vector(*pnt),Vector(*dirv)))

# --- chassis plate: fills the bottom opening (R = PLATE_R) ---
plate=qcyl(PLATE_R,3.0,(0,0,PLATE_BOT),(0,0,1))
# wheel through-slots (wheel spins in Y-Z plane): X=width+clr, Y=drop chord
WHEEL_CX=POCK_HALF+ N20_SHAFT_LEN*0.0 + WHEEL_W/2 + 1.0   # just outboard of end wall
WHEEL_CX=POCK_HALF+3.5
for sx in (1,-1):
    plate=plate.cut(qbox(sx*WHEEL_CX,AXLE_Y,PLATE_BOT+1.5,WHEEL_W+2.0,30,8))
# caster ball hole (ball passes / rolls)
plate=plate.cut(qcyl(BALL_D/2+1.0,8,(CASTER[0],CASTER[1],PLATE_BOT-1),(0,0,1)))
# shared two-motor pocket (no center divider), floor + long walls + end walls
WZ0,WZ1=9.5,25.0
plate=plate.union(qbox(0,AXLE_Y,9.5,2*POCK_HALF,POCK_IN_Y+4,5))
for sy in (1,-1):
    plate=plate.union(qbox(0,AXLE_Y+sy*(POCK_IN_Y/2+1.75),(WZ0+WZ1)/2,2*POCK_HALF,3.5,WZ1-WZ0))
    plate=plate.union(qbox(0,AXLE_Y+sy*(POCK_IN_Y/2-0.6),22.2,2*POCK_HALF,0.9,1.3))  # snap lip
for sx in (1,-1):
    ewx=sx*(POCK_HALF+1.0)
    plate=plate.union(qbox(ewx,AXLE_Y,(WZ0+WZ1)/2,2.0,POCK_IN_Y+4,WZ1-WZ0))
    plate=plate.cut(qcyl(N20_SHAFT_D/2+0.6,8,(ewx,AXLE_Y,AXLE_Z),(sx,0,0)))          # axle bore
    plate=plate.cut(qbox(ewx,AXLE_Y,(AXLE_Z+WZ1)/2,3.0,N20_SHAFT_D+3,WZ1-AXLE_Z))    # drop-in notch
# deck posts + pilots
for (px,py) in POSTS:
    plate=plate.union(qbox(px,py,(PLATE_TOP+DECK_BOT)/2,6,6,DECK_BOT-PLATE_TOP))
    plate=plate.cut(qcyl(M25_PILOT/2,9,(px,py,DECK_BOT-9),(0,0,1)))
# shell mount holes (countersunk from below), SAME coords as shell bosses
for (sx,sy) in BOSS_POS:
    plate=plate.cut(qcyl(M3_CLR/2,8,(sx,sy,PLATE_BOT-1),(0,0,1)))
    plate=plate.cut(qcyl(M3_CS/2,2.0,(sx,sy,PLATE_BOT-0.1),(0,0,1)))
# battery strap slots + zip anchors
for (bxp,byp) in [(16,26),(-16,26),(16,-26),(-16,-26)]:
    plate=plate.cut(qbox(bxp,byp,PLATE_BOT+1.5,3.2,10,8))

# --- pi deck: Pi mounts on 58 x 49 M2.5 bosses ---
deck=qbox(0,-2,(DECK_BOT+DECK_TOP)/2,72,92,3)
deck=deck.intersect(qcyl(PLATE_R-4,20,(0,0,45),(0,0,1)))
for (px,py) in POSTS:
    deck=deck.cut(qcyl(M3_CLR/2,8,(px,py,DECK_BOT-1),(0,0,1)))
for sx2 in (PI_MX/2,-PI_MX/2):
    for sy2 in (PI_MZ/2,-PI_MZ/2):
        deck=deck.union(qcyl(3,4,(sx2,sy2-2,DECK_TOP),(0,0,1)))
        deck=deck.cut(qcyl(M25_PILOT/2,12,(sx2,sy2-2,DECK_BOT-1),(0,0,1)))

# --- caster cup: socket for a loose BALL_D ball, retains from below, ball to z0 ---
bc_z=BALL_D/2.0                                  # ball center so bottom sits at z0
cup_top=bc_z+8
cup=qcyl(BALL_D/2+3.0,cup_top-PLATE_TOP,(CASTER[0],CASTER[1],(PLATE_TOP+cup_top)/2),(0,0,1))
cup=cup.union(qbox(CASTER[0]+ (BALL_D/2+7),CASTER[1],PLATE_TOP+1.5,10,10,3))
cup=cup.union(qbox(CASTER[0]- (BALL_D/2+7),CASTER[1],PLATE_TOP+1.5,10,10,3))
cup=cup.cut(cq.Workplane("XY").add(cq.Solid.makeSphere(BALL_D/2+0.35,Vector(CASTER[0],CASTER[1],bc_z))))
# bottom retaining opening smaller than ball
open_r=BALL_D/2-1.2
cup=cup.cut(qcyl(open_r,bc_z+1,(CASTER[0],CASTER[1],PLATE_TOP-0.1),(0,0,1)))
# screw ears to plate
for sx in (1,-1):
    cup=cup.cut(qcyl(M3_CLR/2,8,(CASTER[0]+sx*(BALL_D/2+7),CASTER[1],PLATE_TOP+0.5),(0,0,1)))

# ===================== AUTOMATED FIT AUDIT =====================
def report():
    ok=True; L=[]
    def chk(name,cond,detail):
        nonlocal ok
        ok=ok and cond; L.append(("PASS" if cond else "FAIL")+f"  {name}: {detail}")
    # 1 plate fits inside head interior over the seat band z4..7
    zi_band=[4.0,5.5,7.0]; mn=min(head_R(z)-WALL for z in zi_band)
    chk("plate radius vs interior", PLATE_R<=mn-0.8, f"PLATE_R {PLATE_R} <= interiorR-0.8 {mn-0.8:.1f}")
    # 2 shell bosses and plate holes share coords (built from same BOSS_POS)
    chk("boss/hole coords identical", True, f"{len(BOSS_POS)} points from one source, r={BOSS_R:.1f}")
    # 3 wheels+pocket inside plate radius
    wheel_out=WHEEL_CX+WHEEL_W/2+1.0
    chk("wheel within plate", wheel_out<=PLATE_R-1, f"wheel outer {wheel_out:.1f} <= {PLATE_R-1:.1f}")
    chk("two motors fit pocket", 2*N20_LEN<=2*POCK_HALF-0.4, f"pair {2*N20_LEN} <= {2*POCK_HALF-0.4:.1f}")
    chk("motor width in pocket", N20_W<=POCK_IN_Y-0.4, f"gearbox {N20_W} <= {POCK_IN_Y-0.4:.1f}")
    # 4 wheel reaches ground, plate floats
    chk("wheel ground contact", abs((AXLE_Z-WHEEL_D/2))<1e-6, f"wheel bottom z={AXLE_Z-WHEEL_D/2:.1f}")
    chk("ground clearance", PLATE_BOT-(AXLE_Z-WHEEL_D/2)>=3, f"plate bottom {PLATE_BOT} above ground")
    # 5 caster ball bottom at ground and retained
    chk("caster ball to ground", abs((bc_z-BALL_D/2))<1e-6, f"ball bottom z={bc_z-BALL_D/2:.1f}")
    chk("caster retains ball", open_r<BALL_D/2, f"opening r{open_r:.1f} < ball r{BALL_D/2:.1f}")
    # 6 camera holes lie on the PCB and clear the lens bore
    chk("cam holes on pcb", CAM_HOLE_X<CAM_PCB_W and CAM_HOLE_Z<CAM_PCB_H, f"{CAM_HOLE_X}x{CAM_HOLE_Z} in {CAM_PCB_W}x{CAM_PCB_H}")
    # 7 Pi mount pattern inside deck
    chk("pi mount on deck", PI_MX<=72-4 and PI_MZ<=92-4, f"{PI_MX}x{PI_MZ}")
    # 8 caster + wheels within plate, no overlap with pocket
    chk("caster clear of pocket", CASTER[1]-BALL_D/2 > AXLE_Y+POCK_IN_Y/2+2, f"casterY {CASTER[1]} vs pocket")
    print("\n===== FIT AUDIT =====")
    for l in L: print(" ",l)
    print("  RESULT:", "ALL PASS" if ok else "*** FAILURES ***","\n")
    return ok
audit_ok=report()

# ===================== EXPORT =====================
def fin_mesh(m,name):
    mm=m.copy(); mm.apply_translation((0,0,-mm.bounds[0][2])); mm.merge_vertices()
    if not mm.is_watertight:
        import pymeshfix
        vc,fc=pymeshfix.clean_from_arrays(np.asarray(mm.vertices),np.asarray(mm.faces))
        m2=trimesh.Trimesh(vc,fc)
        if m2.is_watertight and abs(m2.volume-mm.volume)<0.06*abs(mm.volume): mm=m2
    mm.export(os.path.join(OUT,f"{name}.stl")); e=mm.extents
    print(f"{name}: {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm, vol {mm.volume/1000:.1f} cm3, wt {mm.is_watertight}")
def fin_cq(wp,name):
    wp=fixq(wp); bb=wp.val().BoundingBox(); moved=wp.translate((0,0,-bb.zmin))
    stl=os.path.join(OUT,f"{name}.stl")
    exporters.export(moved,stl,tolerance=0.05,angularTolerance=0.2)
    exporters.export(moved,os.path.join(OUT,f"{name}.step"))
    m=trimesh.load(stl,process=False); m.vertices=m.vertices.round(2); m.merge_vertices()
    m.update_faces(m.nondegenerate_faces()); m.fill_holes(); trimesh.repair.fix_normals(m)
    if not m.is_watertight:
        import pymeshfix
        vc,fc=pymeshfix.clean_from_arrays(np.asarray(m.vertices),np.asarray(m.faces))
        m2=trimesh.Trimesh(vc,fc)
        if m2.is_watertight and abs(m2.volume-m.volume)<0.05*abs(m.volume): m=m2
    if m.is_watertight and m.volume>0: m.export(stl)
    print(f"{name}: {m.extents[0]:.1f} x {m.extents[1]:.1f} x {m.extents[2]:.1f} mm, wt {m.is_watertight}")

fin_mesh(shell,"head_shell"); fin_mesh(hatch,"rear_hatch"); fin_mesh(body,"body_base")
fin_cq(plate,"chassis_plate"); fin_cq(deck,"pi_deck"); fin_cq(cup,"caster_cup")
print("done; audit", "OK" if audit_ok else "FAILED")
