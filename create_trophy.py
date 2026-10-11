"""Editable solid thumbs-up trophy. Blender 4.3+, run: blender -b -P create_trophy.py.
Coordinates and STL are millimetres. Change HEIGHT_MM to scale the final trophy.
All editable construction parts are retained hidden in the .blend file.
"""
import bpy, bmesh, math, os, json
from mathutils import Vector
from math import sin, cos, pi
OUT=os.path.dirname(os.path.abspath(__file__))
HEIGHT_MM=200.0
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def activate(o):
 bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o

def mesh(name,vs,fs):
 m=bpy.data.meshes.new(name);m.from_pydata(vs,[],fs);m.update();o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);return o

def loft(name,rings):
 n=len(rings[0]);vs=[v for r in rings for v in r];fs=[]
 fs.append(tuple(reversed(range(n))))
 for j in range(len(rings)-1):
  for i in range(n):fs.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
 fs.append(tuple((len(rings)-1)*n+i for i in range(n)));return mesh(name,vs,fs)

def ell(name,loc,scale):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=32,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;activate(o);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return o

def tube(name,points,radii,depth=1):
 rings=[]
 for j,p in enumerate(points):
  tangent=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])
  tangent.normalize();u=Vector((0,1,0));v=tangent.cross(u).normalized()
  rings.append([Vector(p)+radii[j]*(u*cos(2*pi*i/40)*depth+v*sin(2*pi*i/40)) for i in range(40)])
 o=loft(name,rings);activate(o);mod=o.modifiers.new('Organic subdivision','SUBSURF');mod.levels=2;bpy.ops.object.modifier_apply(modifier=mod.name);return o

def sculpt_finger(name,points,radii):
 pts=[Vector(p) for p in points];samples=[];rs=[];depths=[]
 profile=[.6,1.18,.9,1.06,.96,.8,.6]
 def cat(a,b,c,d,t):return .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
 for j in range(len(pts)-1):
  for k in range(10):
   t=k/10;ids=[max(0,j-1),j,j+1,min(len(pts)-1,j+2)]
   samples.append(cat(*(pts[i] for i in ids),t))
   rs.append(max(.15,cat(*(radii[i] for i in ids),t)));depths.append(cat(*(profile[i] for i in ids),t))
 samples.append(pts[-1]);rs.append(.15);depths.append(.6);rings=[]
 for j,p in enumerate(samples):
  tangent=(samples[min(j+1,len(samples)-1)]-samples[max(0,j-1)]).normalized()
  u=(Vector((0,1,0))-tangent*tangent.y).normalized();v=tangent.cross(u).normalized()
  upper=2.0*math.exp(-((j-35)/15)**2) if name.startswith('Index') else 0.0
  rings.append([p+rs[j]*(u*cos(2*pi*i/48)*depths[j]+v*sin(2*pi*i/48))+v*upper*max(0,sin(2*pi*i/48)) for i in range(48)])
 return loft(name,rings)

# Anatomical landmarks traced from the approved front-view concept.
# Pixel coordinates are mapped to millimetres; the approved pedestal remains unchanged.
from mathutils.bvhtree import BVHTree
HAND_BASE=143.68345642
S=(200-HAND_BASE)/(292-22)
def P(px,py,y=0):return ((px-446.5)*S,y,HAND_BASE+(292-py)*S)
def E(name,px,py,rx,ry,rz,angle=0):
 o=ell(name,P(px,py),(rx,ry,rz));o.rotation_euler.y=angle;return o
# Anatomical palm as one continuous closed surface, following the approved heel outline.
# The thenar mound and curved valley are sculpted in this surface, not attached ellipsoids.
outline=[(473,122),(505,137),(531,157),(545,177),(536,218),(516,252),(499,274),(475,284),(432,286),(397,279),(370,262),(353,247),(343,230),(339,210),(352,181),(375,146),(411,115)]
path=[]
for j in range(len(outline)):
 a=Vector(outline[(j-1)%len(outline)]);b=Vector(outline[j]);c=Vector(outline[(j+1)%len(outline)]);d=Vector(outline[(j+2)%len(outline)])
 for k in range(16):
  t=k/16
  p=.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
  path.append(p)
rings=[];center=Vector((449,215))
for back in [False,True]:
 values=[.01]+[i/40 for i in range(1,41)] if not back else [i/40 for i in range(39,0,-1)]+[.01]
 for rr in values:
  ring=[]
  for pp in path:
   px,py=center+(pp-center)*rr;x,_,z=P(px,py)
   thickness=math.sqrt(max(0,1-rr*rr))
   if back:y=7.2*thickness+1.0
   else:
    # Broad thenar eminence remains on the thumb side toward the heel.
    # It is a true continuous volume, rather than a narrow crease illusion.
    mound_x=12.0+.14*(z-161.0)
    mound=10.0*math.exp(-((x-mound_x)/6.8)**2-((z-161.6)/15.5)**2)
    # There must be only one thenar boundary; the final sculpt below supplies it.
    valley=0.0
    hypothenar=4.0*math.exp(-((x+7)/8.5)**2-((z-152.5)/8)**2)
    y=1.0-7.2*thickness-(mound-valley+hypothenar)*thickness
   ring.append((x,y,z))
  rings.append(ring)
palm=loft('Continuous sculpted anatomical palm',rings)
wrings=[]
for z,rx,ry in [(140,11.6,6.0),(146,12.2,6.3),(153,12.5,6.5)]:
 wrings.append([(1.0+rx*cos(2*pi*i/48),3+ry*sin(2*pi*i/48),z) for i in range(48)])
hand=[palm,loft('Smooth tapering wrist',wrings)]
# Thick continuous backing underneath all four folded digits removes through-gaps.
back_outline=[(416,101),(437,112),(477,141),(459,178),(433,209),(406,237),(373,229),(347,212),(358,177),(380,140),(404,108)]
back_path=[]
for j in range(len(back_outline)):
 a=Vector(back_outline[(j-1)%len(back_outline)]);b=Vector(back_outline[j]);c=Vector(back_outline[(j+1)%len(back_outline)]);d=Vector(back_outline[(j+2)%len(back_outline)])
 for k in range(12):
  t=k/12;back_path.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
back_rings=[];bc=Vector((410,175))
for rear in [False,True]:
 values=[.01]+[i/28 for i in range(1,29)] if not rear else [i/28 for i in range(27,0,-1)]+[.01]
 for rr in values:
  ring=[]
  for pp in back_path:
   px,py=bc+(pp-bc)*rr;x,_,z=P(px,py);th=math.sqrt(max(0,1-rr*rr))
   web_fullness=-4.5*math.exp(-((x-10)/7)**2-((z-180)/7)**2)
   y=1+4*th if rear else 1-(9.7+.08*(x+7)+web_fullness)*th
   ring.append((x,y,z))
  back_rings.append(ring)
hand.append(loft('Solid closed folded-finger support',back_rings))
# The thumb web is integrated into the continuous finger backing.

# Each finger is a distinct bent sweep, broad at the knuckle and tapering toward its nail.
# Four digits only. The terminal phalanx curls back into the palm in depth.
fingers=[
 ('Index',[(409,91,-1),(418,94,-5.5),(435,109,-7),(454,123,-10),(474,139,-10),(484,149,-9),(490,158,-7)], [.15,4.7,4.8,4.05,3.95,3.05,.15]),
 ('Middle',[(378,124,-1),(389,126,-5.5),(408,141,-8),(432,158,-11),(454,174,-10),(462,182,-9),(467,190,-7)], [.15,5.0,4.7,3.95,3.85,2.95,.15]),
 ('Ring',[(357,160,-1),(369,164,-5.5),(390,181,-8),(409,192,-11),(429,204,-10),(436,212,-9),(441,220,-7)], [.15,4.75,4.4,3.8,3.7,2.8,.15]),
 ('Little',[(340,203,-1),(352,204,-5.5),(370,216,-8),(388,226,-10),(406,231,-9),(413,238,-8),(417,245,-6)], [.15,4.35,3.95,3.45,3.4,2.55,.15])]
for name,pts,rs in fingers:
 shaped=[]
 for j,(px,py,y) in enumerate(pts):
  weight=max(0,1-j/3)
  shaped.append(P(px-(2 if name in ['Index','Middle'] else 5)*weight,py-(1 if name in ['Index','Middle'] else 4)*weight,y))
 hand.append(sculpt_finger(name+' curled finger',shaped,rs))
# Thumb: broad first phalanx, narrowed joint, outward curve and rounded angled fingertip.
# Cross-sections traced from the approved thumb silhouette, avoiding attached tip bulbs.
thumb_sections=[(218, 480, 526, 6.5), (180, 489, 541, 6.2), (150, 496, 545, 5.1), (120, 491, 547, 4.2), (110, 493, 550, 4.1), (100, 498, 553, 4.0), (94, 500.88, 554.84, 4.0), (92, 502.0, 555.79, 4.007), (90, 503.22, 557.0, 4.014), (88, 504.37, 558.21, 4.021), (86, 505.63, 559.25, 4.028), (84, 506.74, 560.25, 4.034), (82, 507.79, 561.25, 4.041), (80, 509.0, 562.26, 4.048), (78, 510.21, 563.4, 4.055), (76, 511.2, 564.89, 4.062), (74, 511.88, 566.36, 4.069), (72, 512.36, 567.89, 4.076), (70, 512.89, 569.37, 4.083), (68, 513.36, 571.04, 4.09), (66, 513.89, 572.99, 4.097), (64, 514.4, 574.85, 4.12), (62, 515.26, 576.37, 4.16), (60, 516.25, 578.04, 4.2), (58, 517.25, 580.0, 4.24), (56, 518.26, 582.0, 4.28), (54, 519.37, 583.96, 4.32), (52, 520.67, 585.62, 4.36), (50, 522.0, 586.99, 4.4), (48, 523.37, 588.21, 4.44), (46, 525.0, 589.2, 4.48), (44, 526.63, 589.84, 4.427), (42, 528.15, 589.99, 4.28), (40, 530.02, 589.95, 4.133), (38, 532.16, 589.59, 3.987), (36, 534.68, 588.73, 3.84), (34, 537.37, 587.63, 3.693), (32, 540.27, 586.36, 3.547), (30, 543.41, 585.17, 3.4), (28, 547.06, 583.41, 2.7), (26, 551.23, 580.5, 2.0), (24, 556.45, 576.28, 1.3), (22, 561.09, 572.33, 0.6), (21, 568, 568.2, 0.1)]
tr=[]
for j in range(len(thumb_sections)-1):
 a=Vector(thumb_sections[max(0,j-1)]);b=Vector(thumb_sections[j]);c=Vector(thumb_sections[j+1]);d=Vector(thumb_sections[min(len(thumb_sections)-1,j+2)])
 for k in range(10):
  t=k/10;q=.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
  py,l,r,depth=q;cx,_,z=P((l+r)/2,py);rx=(r-l)*S/2
  tr.append([(cx+rx*cos(2*pi*i/64),.3+depth*sin(2*pi*i/64),z) for i in range(64)])
py,l,r,depth=thumb_sections[-1];cx,_,z=P((l+r)/2,py);rx=(r-l)*S/2
tr.append([(cx+rx*cos(2*pi*i/64),.3+depth*sin(2*pi*i/64),z) for i in range(64)])
hand.append(loft('Continuously curved reference-profile thumb',tr))
sources=bpy.data.collections.new('EDITABLE CONSTRUCTION (hidden)');bpy.context.scene.collection.children.link(sources)
def backup(o):
 c=o.copy();c.data=o.data.copy();sources.objects.link(c);c.hide_render=True;c.hide_set(True);return c
for o in hand:backup(o)
bpy.ops.object.select_all(action='DESELECT')
for o in hand:o.select_set(True)
bpy.context.view_layer.objects.active=hand[0];bpy.ops.object.join();h=bpy.context.object;h.name='Solid anatomically sculpted hand'
activate(h);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
r=h.modifiers.new('Solid hand union without cavities','REMESH');r.mode='VOXEL';r.voxel_size=.17;r.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=r.name)
smo=h.modifiers.new('Organic blending','SMOOTH');smo.factor=.8;smo.iterations=16;bpy.ops.object.modifier_apply(modifier=smo.name)
# Close submillimetre tunnels in the hand volume only; preserve the faceted pedestal.
import numpy as np, subprocess
bm=bmesh.new();bm.from_mesh(h.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(h.data);bm.free()
volume_path=os.path.join(OUT,'hand_volume_work.npz')
np.savez(volume_path,vertices=np.array([v.co[:] for v in h.data.vertices]),faces=np.array([p.vertices[:] for p in h.data.polygons]))
env=os.environ.copy()
if env.get('TROPHY_PYTHONPATH'):env['PYTHONPATH']=env['TROPHY_PYTHONPATH']
subprocess.run([os.environ.get('TROPHY_PYTHON','python3'),os.path.join(OUT,'close_hand_volume.py'),volume_path],check=True,env=env)
d=np.load(volume_path);old=h.data;new=bpy.data.meshes.new('Closed hand volume');new.from_pydata(d['vertices'].tolist(),[],d['faces'].tolist());new.update();h.data=new;bpy.data.meshes.remove(old);os.remove(volume_path)
soft=h.modifiers.new('Volume micro relaxation','SMOOTH');soft.factor=.8;soft.iterations=24;bpy.ops.object.modifier_apply(modifier=soft.name)
# Orient the reconstructed hand before any front-facing sculpt masks.
bm=bmesh.new();bm.from_mesh(h.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
assert bm.calc_volume(signed=True)>0, 'Hand volume orientation failed'
bm.normal_update();bm.to_mesh(h.data);bm.free();h.data.update()
# Carve shallow surface details by ray-projecting curves onto the actual hand surface.
# Surface cuts never form interior cavities, finger holes, or free-floating nail objects.
bpy.context.view_layer.update()
bvh=BVHTree.FromObject(h,bpy.context.evaluated_depsgraph_get())
nail_specs=[('Index',478,145,3.3,2.8),('Middle',454,175,3.2,2.7),('Ring',431,205,3.1,2.6),('Little',406,231,2.85,2.4)]
cached_normals=[v.normal.copy() for v in h.data.vertices]
def detail_smoothstep(a,b,x):
 t=max(0.0,min(1.0,(x-a)/(b-a)))
 return t*t*(3.0-2.0*t)
# Each plate is a prescribed low-curvature dome, rather than a displacement
# that inherits the fingertip's full convexity. A sampled rim plane sets its
# orientation and depth, preventing a thick tangent-plane button at the edge.
for name,px,py,major,minor in nail_specs:
 cx,_,cz=P(px,py)
 hit,normal,idx,dist=bvh.ray_cast(Vector((cx,-90,cz)),Vector((0,1,0)),180)
 if hit is None:continue
 samples=[];heights=[]
 for i in range(48):
  a=2*pi*i/48
  u=major*math.copysign(abs(cos(a))**.65,cos(a))
  w=minor*(.96-.10*u/major)*math.copysign(abs(sin(a))**.65,sin(a))
  dx=.63*u+.777*w;dz=-.777*u+.63*w
  p,n,_,_=bvh.ray_cast(Vector((cx+dx,-90,cz+dz)),Vector((0,1,0)),180)
  if p is not None and abs(p.y-hit.y)<3.8:
   samples.append((dx,dz,1));heights.append(p.y)
 if len(samples)>=12:
  sx,sz,rim_c=np.linalg.lstsq(np.asarray(samples),np.asarray(heights),rcond=None)[0]
 else:
  n=(normal*.4+Vector((0,-.6,0))).normalized()
  sx=-n.x/n.y;sz=-n.z/n.y;rim_c=hit.y+.8
 # A 40% rim-plane contribution limits the edge projection; full center
 # tangent placement would make the edge unnecessarily thick.
 base_c=.60*hit.y+.40*rim_c-.10
 changed_vertices=0
 for vert,vnormal in zip(h.data.vertices,cached_normals):
  v=vert.co
  if vnormal.y>-.05 or abs(v.y-hit.y)>4.0:continue
  dx=v.x-cx;dz=v.z-cz
  u=.63*dx-.777*dz;vv=.777*dx+.63*dz
  nail_width=minor*(.96-.10*max(-1,min(1,u/major)))
  rr=((abs(u)/major)**(2/.65)+(abs(vv)/nail_width)**(2/.65))**(.65/2)
  if rr>1.32:continue
  skin=v.y
  target=base_c+sx*dx+sz*dz-.48*max(0,1-rr*rr)
  # All interior plate vertices reach the same designed surface. Only the
  # narrow bevel outside rr=.88 blends back to the original skin.
  projection_scale=.5+.5*(1-detail_smoothstep(.65,.9,rr))
  target=skin+(target-skin)*projection_scale
  blend=1-detail_smoothstep(.88,1.045,rr)
  recess=.14*math.exp(-((rr-1.045)/.060)**2)
  v.y=skin+(target-skin)*blend+recess
  changed_vertices+=1
 assert changed_vertices>100, "Nail surface mask missed the visible fingertip"
 print("Sculpted nail",name,changed_vertices,flush=True)
h.data.update();bpy.context.view_layer.update();bvh=BVHTree.FromObject(h,bpy.context.evaluated_depsgraph_get())
def groove(name,coords,radius=.18,closed=False):
 # A sculpted height displacement preserves watertight topology; no cutting booleans.
 from mathutils.kdtree import KDTree
 points=[]
 for x,z in coords:
  hit,normal,idx,dist=bvh.ray_cast(Vector((x,-90,z)),Vector((0,1,0)),180)
  if hit is not None:points.append(hit)
 if len(points)<4:return
 kd=KDTree(len(points))
 for i,p in enumerate(points):kd.insert(p,i)
 kd.balance();pad=.8
 xmin=min(p.x for p in points)-pad;xmax=max(p.x for p in points)+pad
 zmin=min(p.z for p in points)-pad;zmax=max(p.z for p in points)+pad
 width=max(.20,radius*1.3);depth=radius*.75
 for v in h.data.vertices:
  if xmin<v.co.x<xmax and zmin<v.co.z<zmax:
   _,_,dist=kd.find(v.co)
   if dist<width*3:v.co.y+=depth*math.exp(-(dist/width)**2)
 h.data.update()
# Nail outer recess and bevel are integrated in the conformal relief above.
# Natural thumb joint fold and thenar/palm crease, shallower than nail edges.
def trace_px(name,pts,radius):
 # Smooth interpolation of traced 2D landmarks via Bezier evaluated points.
 coords=[]
 for j in range(len(pts)-1):
  for i in range(24):
   t=i/24;x=pts[j][0]*(1-t)+pts[j+1][0]*t;y=pts[j][1]*(1-t)+pts[j+1][1]*t
   xx,_,zz=P(x,y);coords.append((xx,zz))
 groove(name,coords,radius)
trace_px('Index phalanx crease',[(451,110),(447,113),(444,118),(440,123),(436,127)],.18)
trace_px('Middle phalanx crease',[(427,140),(423,143),(420,148),(416,153),(412,157)],.17)
trace_px('Ring phalanx crease',[(405,177),(401,180),(398,184),(394,189),(390,192)],.17)
# The distal thumb has a continuous shallow nail plate, not a linear incision.
# A small conformal dome follows the curved side surface with one thin recess.
cx,_,cz=P(578,43)
for vert in h.data.vertices:
 v=vert.co
 if vert.normal.y>-.08:continue
 dx=v.x-cx;dz=v.z-cz
 u=.42*dx+.9075*dz;w=.9075*dx-.42*dz
 rr=math.sqrt((u/3.15)**2+(w/1.05)**2)
 if rr>1.3:continue
 # Smoothly vanishing dome and a single sub-millimetre cuticle boundary.
 dome=.14*max(0,1-rr*rr)**2
 boundary=.075*math.exp(-((rr-1.0)/.095)**2)
 v.y+=boundary-dome
h.data.update()
trace_px('Thumb joint skin fold',[(516,80),(522,84),(530,87),(538,90),(544,91)],.16)
# Curved palm fold is already sculpted into the continuous palm surface.
# Apply baked numeric sculpt displacements. No reference image is required.
# Vertex ordering is checked because these offsets belong to this construction.
sculpt=np.load(os.path.join(OUT,'sculpt_displacements.npz'))
assert len(h.data.vertices)==int(sculpt['vertex_count']), 'Sculpt construction changed; regenerate the displacement map before applying it'
for index,delta in zip(sculpt['indices'],sculpt['displacements']):
 h.data.vertices[int(index)].co.y-=float(delta)
h.data.update()

# One continuous thenar boundary. The actual broad convex mound was formed
# in the palm surface above; this shallow, asymmetric saddle defines its left
# edge without cutting across its crest or leaving a narrow raised ribbon.
from mathutils.kdtree import KDTree
fold_px=[(487,160),(477,176),(470,194),(470,210),(475,228),(475,240),(469,253),(455,267),(435,278)]
fold=[]
for j in range(len(fold_px)-1):
 a=Vector(fold_px[max(0,j-1)]);b=Vector(fold_px[j]);c=Vector(fold_px[j+1]);d=Vector(fold_px[min(len(fold_px)-1,j+2)])
 for k in range(24):
  t=k/24;q=.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
  x,_,z=P(q.x,q.y);fold.append(Vector((x,0,z)))
x,_,z=P(*fold_px[-1]);fold.append(Vector((x,0,z)))
kd=KDTree(len(fold))
for i,q in enumerate(fold):kd.insert(q,i)
kd.balance();cached_normals=[v.normal.copy() for v in h.data.vertices]
for v,n in zip(h.data.vertices,cached_normals):
 if n.y>-.12:continue
 q,idx,dist=kd.find(Vector((v.co.x,0,v.co.z)))
 if dist>4.8:continue
 # The left bank spreads softly into the palm. The mound-facing right bank
 # is tighter, giving a crescent transition rather than a symmetric gutter.
 tangent=fold[min(idx+2,len(fold)-1)]-fold[max(0,idx-2)]
 side=(v.co.x-q.x)*(-tangent.z)+(v.co.z-q.z)*tangent.x
 signed=dist if side>=0 else -dist
 width=1.00 if signed>=0 else 1.65
 fade=sin(pi*idx/(len(fold)-1))**.6
 facing=detail_smoothstep(.12,.62,-n.y)
 v.co.y+=.95*math.exp(-(dist/width)**2)*fade*facing
h.data.update()
for p in h.data.polygons:p.use_smooth=True
# Base: sloping square frustum with actual multi-segment rounded edge fillets.
rings=[]
for z,w,d in [(0,31,25),(37,20,16)]:rings.append([(-w,-d,z),(w,-d,z),(w,d,z),(-w,d,z)])
base=loft('Rounded sloping base',rings);activate(base)
b=base.modifiers.new('Rounded fillets R3.0 mm, 12 segments','BEVEL');b.width=3;b.segments=12;b.affect='EDGES';b.profile=.5;bpy.ops.object.modifier_apply(modifier=b.name)
for p in base.data.polygons:p.use_smooth=True
# Six-sided tapered column: regular hexagons, six uninterrupted planar side faces.
def hexring(z,r):
 return [(r*cos(2*pi*i/6),r*sin(2*pi*i/6),z) for i in range(6)]
shaft=loft('Hexagonal taper column - SIX side faces',[hexring(41,8.7),hexring(142,16.2)])
# Alternating low poly jewel collar: staggered rings create explicit diamond facets.
N=16;vs=[]
for z,rx,ry,phase in [(35.7,15.5,12.8,0),(38.4,17,14,0),(41,17.1,14.1,pi/N),(44.0,14.5,12,0)]:
 for i in range(N):
  a=2*pi*i/N+phase;vs.append((rx*cos(a),ry*sin(a),z))
fs=[tuple(reversed(range(N)))]
for j in range(3):
 for i in range(N):
  a=j*N+i;b=j*N+(i+1)%N;c=(j+1)*N+(i+1)%N;d=(j+1)*N+i
  fs.extend([(a,b,d),(b,c,d)])
fs.append(tuple(3*N+i for i in range(N)))
collar=mesh('Diamond faceted collar',vs,fs)
for o in [base,shaft,collar]:
 for v in o.data.vertices:v.co*=1.0118553269
 backup(o)
# Match exact approved hand height while retaining pedestal unchanged.
handtop=max((h.matrix_world@v.co).z for v in h.data.vertices)
for v in h.data.vertices:
 world=h.matrix_world@v.co
 world.z=HAND_BASE+(world.z-HAND_BASE)*(200-HAND_BASE)/(handtop-HAND_BASE)
 v.co=h.matrix_world.inverted()@world
# Resolve sub-millimetre sculpt overlaps and retain a single robust closed surface.
activate(h);clean=h.modifiers.new('Final hand surface consolidation','REMESH');clean.mode='VOXEL';clean.voxel_size=.14;clean.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=clean.name)
soft=h.modifiers.new('Micro surface relaxation','SMOOTH');soft.factor=.2;soft.iterations=2;bpy.ops.object.modifier_apply(modifier=soft.name)
handtop=max(v.co.z for v in h.data.vertices)
for v in h.data.vertices:v.co.z=HAND_BASE+(v.co.z-HAND_BASE)*(200-HAND_BASE)/(handtop-HAND_BASE)
for p in h.data.polygons:p.use_smooth=True

# Exact booleans retain planar facets and rounded base rather than voxelizing the whole object.
activate(base)
for o in [collar,shaft,h]:
 m=base.modifiers.new('Solid union '+o.name,'BOOLEAN');m.operation='UNION';m.solver='EXACT';m.object=o;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(o,do_unlink=True)
base.name='Trophy PRINT - one closed solid'
# Uniform 200 mm finished size with a truly coplanar base at Z=0.
zmin=min(v.co.z for v in base.data.vertices);zmax=max(v.co.z for v in base.data.vertices);sf=HEIGHT_MM/200.0
for v in base.data.vertices:v.co.x*=sf;v.co.y*=sf;v.co.z=(v.co.z-zmin)*sf
# Robust topology cleanup: remove coincident boolean slivers and any minute enclosed islands.
bm=bmesh.new();bm.from_mesh(base.data)
bmesh.ops.triangulate(bm,faces=list(bm.faces))
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.00001)
unseen=set(bm.faces);groups=[]
while unseen:
 seed=unseen.pop();group={seed};stack=[seed]
 while stack:
  f=stack.pop()
  for e in f.edges:
   if len(e.link_faces)==2:
    for g in e.link_faces:
     if g in unseen:unseen.remove(g);group.add(g);stack.append(g)
 groups.append(group)
keep=max(groups,key=len)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f not in keep],context='FACES')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(base.data);bm.free()
# Recalculate outward normals.
activate(base);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
mat=bpy.data.materials.new('Warm ivory');mat.diffuse_color=(.77,.71,.60,1);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.77,.71,.60,1);bs.inputs['Roughness'].default_value=.26;base.data.materials.append(mat)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.001
activate(base);bpy.ops.wm.stl_export(filepath=os.path.join(OUT,'thumbs_up_trophy_200mm.stl'),export_selected_objects=True,apply_modifiers=True)
# Studio scene used only for previews; construction sources hidden.
bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,-.02));floor=bpy.context.object;floor.name='Preview ground (not exported)';fm=bpy.data.materials.new('Studio gray');fm.diffuse_color=(.36,.39,.43,1);floor.data.materials.append(fm)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=int(os.environ.get('TROPHY_SAMPLES','512'));scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.015;scene.cycles.adaptive_min_samples=64;scene.cycles.use_denoising=False
scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.35,.38,.43,1);scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.15
wn=scene.world.node_tree;camera_bg=wn.nodes.new('ShaderNodeBackground');camera_bg.inputs['Color'].default_value=(.35,.38,.43,1);camera_bg.inputs['Strength'].default_value=.6
lp=wn.nodes.new('ShaderNodeLightPath');mix=wn.nodes.new('ShaderNodeMixShader');wn.links.new(lp.outputs['Is Camera Ray'],mix.inputs[0]);wn.links.new(wn.nodes.get('Background').outputs[0],mix.inputs[1]);wn.links.new(camera_bg.outputs[0],mix.inputs[2]);wn.links.new(mix.outputs[0],wn.nodes.get('World Output').inputs['Surface'])
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Key',(-130,-170,300),650000,110),('Fill',(140,-90,220),65000,130),('Rim',(20,130,260),450000,120)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;aim(o,(0,0,110))
bpy.ops.object.camera_add(location=(190,-550,180));cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=236;aim(cam,(0,0,101))
scene.render.resolution_x=1000;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
activate(base)
# Open the native file with an immediately useful camera view and embedded source.
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_perspective='CAMERA'
   area.spaces.active.overlay.show_overlays=False
bpy.data.texts.load(os.path.abspath(__file__))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'thumbs_up_trophy_editable.blend'),compress=True)
if not os.environ.get('TROPHY_SKIP_HAND_PREVIEWS'):
 cam.location=(0,-550,172);aim(cam,(3,0,172));cam.data.ortho_scale=70
 scene.render.resolution_x=1100;scene.render.resolution_y=1100
 scene.render.filepath=os.path.join(OUT,'hand_front_detail.png');bpy.ops.render.render(write_still=True)
 cam.location=(190,-550,212);aim(cam,(3,0,172));cam.data.ortho_scale=70;scene.render.resolution_x=1100;scene.render.resolution_y=1100
 scene.render.filepath=os.path.join(OUT,'hand_perspective_detail.png');bpy.ops.render.render(write_still=True)
cam.data.ortho_scale=236;scene.render.resolution_x=1000;scene.render.resolution_y=1200
for name,loc in [('perspective',(190,-550,180)),('front',(0,-550,135))]:
 cam.location=loc;aim(cam,(0,0,101));scene.render.filepath=os.path.join(OUT,'trophy_'+name+'.png');bpy.ops.render.render(write_still=True)
print('TROPHY_BUILD_COMPLETE')
