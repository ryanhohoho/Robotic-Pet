#!/usr/bin/env python3
# usagi robot printable parts, v3 - smooth lofted head+body from model.glb
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
def ellipsoid(cx,cy,cz,rx,ry,rz,subdiv=3):
    m=creation.icosphere(subdivisions=subdiv,radius=1.0); m.apply_transform(np.diag([rx,ry,rz,1.0])); m.apply_translation((cx,cy,cz)); return m
def smooth_profile(zc,rc,zq,s=2.0):
    tck=splrep(zc,rc,s=s,k=3); return np.clip(splev(zq,tck),0.05,None)
def loft(zs,xrs,yrs,cxs,cys,nseg=140,cap_bottom=True,cap_top=True):
    ang=np.linspace(0,2*np.pi,nseg,endpoint=False); ca,sa=np.cos(ang),np.sin(ang); rings=[]
    for z,xr,yr,cx,cy in zip(zs,xrs,yrs,cxs,cys):
        rings.append(np.column_stack([cx+xr*ca,cy+yr*sa,np.full(nseg,z)]))
    V=np.vstack(rings); F=[]; nr=len(rings)
    for k in range(nr-1):
        a,b=k*nseg,(k+1)*nseg
        for j in range(nseg):
            j2=(j+1)%nseg; F.append([a+j,a+j2,b+j2]); F.append([a+j,b+j2,b+j])
    if cap_bottom:
        c=len(V); V=np.vstack([V,rings[0].mean(0)])
        for j in range(nseg): F.append([c,(j+1)%nseg,j])
    if cap_top:
        base=(nr-1)*nseg; c=len(V); V=np.vstack([V,rings[-1].mean(0)])
        for j in range(nseg): F.append([c,base+j,base+(j+1)%nseg])
    m=trimesh.Trimesh(V,np.array(F),process=True); m.merge_vertices(); trimesh.repair.fix_normals(m); return m

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

PLATE_R=47.0; PLATE_BOT,PLATE_TOP=4.0,7.0; AXLE_Z=17.0; AXLE_Y=-6.0
DECK_BOT,DECK_TOP=56.0,59.0
PLATE_SCREWS=[(24,34),(-24,34),(18,-40),(-18,-40)]
POSTS=[(28,33),(-28,33),(21,-38),(-21,-38)]
CASTER=(0.0,40.0); CAM_Z=62.0; WAIST=-57.0; Z_LIFT=4.0-WAIST

print("building smooth head...")
zc=np.linspace(-57,63.5,160); xr=smooth_profile(HEAD_Z,HEAD_R,zc,s=3)
head_outer=loft(zc,xr,xr,np.zeros_like(zc),np.zeros_like(zc))
def ear(sign):
    ze=np.linspace(54,146,90)
    return loft(ze,smooth_profile(EAR_Z,EAR_XR,ze,1),smooth_profile(EAR_Z,EAR_YR,ze,1),
                sign*smooth_profile(EAR_Z,EAR_CX,ze,1),smooth_profile(EAR_Z,EAR_CY,ze,1),nseg=80)
head_outer=u([head_outer,ear(1),ear(-1)])
sm.filter_taubin(head_outer,lamb=0.5,nu=-0.53,iterations=10)
head_outer.apply_translation((0,0,Z_LIFT))
head_outer=i(head_outer,bx(0,0,304,900,900,600))
zi=np.linspace(-59,50,150); xri=smooth_profile(HEAD_Z,HEAD_R,np.clip(zi,-57,54),s=3)-2.8
inner=loft(zi+Z_LIFT,xri,xri,np.zeros_like(zi),np.zeros_like(zi))
shell=d(head_outer,inner)
adds=[bx(0,70,CAM_Z,26,20,24),bx(18,-72,36,12,20,16),bx(-18,-72,36,12,20,16),bx(0,-68,83,36,7,10)]
for (sx,sy) in PLATE_SCREWS:
    th=np.arctan2(sy,sx)
    T=np.dot(tra.translation_matrix((np.cos(th)*48,np.sin(th)*48,10)),tra.rotation_matrix(th,(0,0,1)))
    adds.append(creation.box((20,12,6),transform=T))
shell=u([shell,i(u(adds),head_outer)])
def rrect_y(w,h,rad,cx,cz,y0,y1):
    parts=[bx(cx,(y0+y1)/2,cz,w-2*rad,y1-y0,h),bx(cx,(y0+y1)/2,cz,w,y1-y0,h-2*rad)]
    for sx in (1,-1):
        for sz in (1,-1): parts.append(cyly(rad,y0,y1,cx+sx*(w/2-rad),cz+sz*(h/2-rad)))
    return u(parts)
shell=d(shell,rrect_y(56,50,8,0,55,-95,-56))
shell=d(shell,cyly(5,55,90,0,CAM_Z)); shell=d(shell,cyly(9,73,90,0,CAM_Z))
for dx in (10.5,-10.5):
    for dz in (6.25,-6.25): shell=d(shell,cyly(1.25,58.5,68,dx,CAM_Z+dz))
for (mx,my) in [(0,-25),(7,-29),(-7,-29),(7,-21),(-7,-21)]: shell=d(shell,cylz(1.5,95,145,mx,my))
for sx in (18,-18): shell=d(shell,cyly(1.25,-85,-60,sx,38))
for (sx,sy) in PLATE_SCREWS: shell=d(shell,cylz(1.25,2,13,sx,sy))

print("building hatch...")
hatch=i(d(head_outer,inner),rrect_y(54,48,7,0,55,-95,-56))
hatch=d(hatch,cyly(6.25,-95,-55,-14,68))
for sx in (18,-18): hatch=d(hatch,cyly(1.7,-95,-55,sx,38))

print("building smooth body...")
zb=np.linspace(-124,-57,130)
bxr=smooth_profile(BODY_Z,BODY_XR,zb,s=4); byr=smooth_profile(BODY_Z,BODY_YR,zb,s=4)
body=loft(zb,bxr,byr,np.zeros_like(zb),np.zeros_like(zb))
feet=[ellipsoid(s*13,-1,-130,11,13,15) for s in (1,-1)]
arms=[ellipsoid(s*52,-2,-80,15,13,18) for s in (1,-1)]
body=u([body]+feet+arms)
sm.filter_taubin(body,lamb=0.5,nu=-0.53,iterations=8)
body.apply_translation((0,0,-body.bounds[0][2]))
top_z=body.bounds[1][2]
body=i(body,bx(0,0,(top_z-6)-300,900,900,600))
top_z=body.bounds[1][2]
ring=d(cylz(58.5,top_z-2,top_z+9),cylz(55,top_z-4,top_z+11))
pad=i(ellipsoid(0,2,0,34,24,2.2),bx(0,2,1.5,200,200,3))
body=u([body,ring,pad])

print("building plate / deck / caster cup...")
import cadquery as cq
from cadquery import exporters, Vector
from OCP.ShapeFix import ShapeFix_Shape
def fixq(wp):
    sf=ShapeFix_Shape(wp.val().wrapped); sf.Perform()
    return cq.Workplane("XY").add(cq.Shape.cast(sf.Shape()))
def qbox(cx,cy,cz,lx,ly,lz): return cq.Workplane("XY").box(lx,ly,lz).translate((cx,cy,cz))
def qcyl(r,h,pnt,dirv): return cq.Workplane("XY").add(cq.Solid.makeCylinder(r,h,Vector(*pnt),Vector(*dirv)))

plate=qcyl(PLATE_R,3.0,(0,0,PLATE_BOT),(0,0,1))
for sx in (1,-1): plate=plate.cut(qbox(sx*31,AXLE_Y,PLATE_BOT+1.5,9,30,8))
plate=plate.cut(qcyl(7.0,8,(CASTER[0],CASTER[1],PLATE_BOT-1),(0,0,1)))
POCK_X=25.5; WALL_Z0,WALL_Z1=9.5,25.0
plate=plate.union(qbox(0,AXLE_Y,9.5,2*POCK_X,13,5))
for sy in (1,-1):
    plate=plate.union(qbox(0,AXLE_Y+sy*7.75,(WALL_Z0+WALL_Z1)/2,2*POCK_X,3.5,WALL_Z1-WALL_Z0))
    plate=plate.union(qbox(0,AXLE_Y+sy*5.4,22.2,2*POCK_X,0.9,1.3))
for sx in (1,-1):
    plate=plate.union(qbox(sx*(POCK_X+0.75),AXLE_Y,(WALL_Z0+WALL_Z1)/2,2.0,15.5,WALL_Z1-WALL_Z0))
    # axle bore through the end wall (shaft passes here to the wheel outside)
    plate=plate.cut(qcyl(3.0,8,(sx*(POCK_X+0.75),AXLE_Y,AXLE_Z),(sx,0,0)))
    # open-top drop-in notch: motor + shaft lower in from above, seat at axle
    plate=plate.cut(qbox(sx*(POCK_X+0.75),AXLE_Y,(AXLE_Z+WALL_Z1)/2,3.0,6.0,WALL_Z1-AXLE_Z))
for (px,py) in POSTS:
    plate=plate.union(qbox(px,py,(PLATE_TOP+DECK_BOT)/2,6,6,DECK_BOT-PLATE_TOP))
    plate=plate.cut(qcyl(1.25,9,(px,py,DECK_BOT-9),(0,0,1)))
for (sx,sy) in PLATE_SCREWS:
    plate=plate.cut(qcyl(1.7,8,(sx,sy,PLATE_BOT-1),(0,0,1)))
    plate=plate.cut(qcyl(3.25,1.9,(sx,sy,PLATE_BOT-0.1),(0,0,1)))
for (bxp,byp) in [(19.5,26),(-19.5,26),(19.5,-30),(-19.5,-30)]:
    plate=plate.cut(qbox(bxp,byp,PLATE_BOT+1.5,3.2,10,8))
for (zx,zy) in [(36,8),(-36,8),(10,-42),(-10,-42)]:
    plate=plate.cut(qcyl(2.0,8,(zx,zy,PLATE_BOT-1),(0,0,1)))

deck=qbox(0,-2,(DECK_BOT+DECK_TOP)/2,76,92,3)
for (px,py) in POSTS: deck=deck.cut(qcyl(1.7,8,(px,py,DECK_BOT-1),(0,0,1)))
for bxp in (24.5,-24.5):
    for byp in (-33,25):
        deck=deck.union(qcyl(3,4,(bxp,byp,DECK_TOP),(0,0,1)))
        deck=deck.cut(qcyl(1.1,12,(bxp,byp,DECK_BOT-1),(0,0,1)))
for mx in (10,-5): deck=deck.cut(qcyl(1.1,8,(mx,-42,DECK_BOT-1),(0,0,1)))

cup=qbox(CASTER[0],CASTER[1],(PLATE_TOP+18)/2,22,22,18-PLATE_TOP)
cup=cup.union(qbox(15,CASTER[1],PLATE_TOP+1.5,8,10,3)); cup=cup.union(qbox(-15,CASTER[1],PLATE_TOP+1.5,8,10,3))
cup=cup.cut(cq.Workplane("XY").add(cq.Solid.makeSphere(8.3,Vector(CASTER[0],CASTER[1],8.0))))
cup=cup.cut(qcyl(8.3,4,(CASTER[0],CASTER[1],4),(0,0,1)))
cup=cup.cut(qcyl(1.7,8,(15,CASTER[1],5),(0,0,1))); cup=cup.cut(qcyl(1.7,8,(-15,CASTER[1],5),(0,0,1)))

def fin_mesh(m,name):
    mm=m.copy(); mm.apply_translation((0,0,-mm.bounds[0][2])); mm.merge_vertices()
    if not mm.is_watertight:
        import pymeshfix
        vc,fc=pymeshfix.clean_from_arrays(np.asarray(mm.vertices),np.asarray(mm.faces))
        m2=trimesh.Trimesh(vc,fc)
        if m2.is_watertight and abs(m2.volume-mm.volume)<0.05*abs(mm.volume): mm=m2
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
print("done")
