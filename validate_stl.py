"""Independent STL reload check. Requires Python numpy and trimesh."""
import trimesh, numpy as np, json, os, hashlib
root=os.path.dirname(os.path.abspath(__file__))
m=trimesh.load(os.path.join(root,'thumbs_up_trophy_200mm.stl'),force='mesh')
counts=np.bincount(m.edges_unique_inverse)
components=m.split(only_watertight=False)
# A manifold triangle surface has one cyclic face fan at every vertex.
f=m.faces
links=np.concatenate([f,f[:,[1,2,0]],f[:,[2,0,1]]])
links=links[np.argsort(links[:,0],kind='stable')]
breaks=np.r_[0,np.flatnonzero(np.diff(links[:,0]))+1,len(links)]
bad_vertex_links=0
for a,b in zip(breaks[:-1],breaks[1:]):
 group=links[a:b];nxt={int(row[1]):int(row[2]) for row in group}
 start=int(group[0,1]);cur=start;seen=set()
 while cur not in seen and cur in nxt:
  seen.add(cur);cur=nxt[cur]
 if len(nxt)!=len(group) or len(seen)!=len(group) or cur!=start:bad_vertex_links+=1
# Verify six planar shaft faces and six-edge mesh sections.
from scipy.spatial import ConvexHull
section_counts=[]
for z in [50.,75.,100.,120.,135.]:
 seg=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,z])
 pts=np.unique(np.round(seg[:,:,:2].reshape(-1,2),5),axis=0)
 q=pts[ConvexHull(pts).vertices]
 while len(q)>6:
  score=[]
  for i,b in enumerate(q):
   a=q[i-1];c=q[(i+1)%len(q)];v=b-a;w=c-b
   score.append(abs(v[0]*w[1]-v[1]*w[0])/max(np.linalg.norm(c-a),1e-9))
  j=int(np.argmin(score))
  if score[j]>.0001:break
  q=np.delete(q,j,axis=0)
 section_counts.append(len(q))
shaft_mask=(m.triangles[:,:,2].min(axis=1)<135)&(m.triangles[:,:,2].max(axis=1)>50)
shaft_planes=len(np.unique(np.round(m.face_normals[shaft_mask],5),axis=0))
result={
 'shaft_section_edge_counts':section_counts,'shaft_planar_side_count':shaft_planes,
 'file':'thumbs_up_trophy_200mm.stl','units':'millimetres',
 'sha256':hashlib.sha256(open(os.path.join(root,'thumbs_up_trophy_200mm.stl'),'rb').read()).hexdigest(),
 'finite_vertex_coordinates':bool(np.isfinite(m.vertices).all()),
 'watertight':bool(m.is_watertight),'winding_consistent':bool(m.is_winding_consistent),
 'positive_volume':bool(m.volume>0),'volume_mm3':float(m.volume),
 'bounds_mm':m.bounds.tolist(),'dimensions_mm':m.extents.tolist(),
 'connected_surface_components':len(components),
 'euler_characteristic':int(m.euler_number),
 'through_hole_handles':int((2-m.euler_number)//2) if len(components)==1 and m.is_watertight else None,
 'internal_shells':max(0,len(components)-1),
 'nonmanifold_or_boundary_edges':int((counts!=2).sum()),
 'nonmanifold_vertex_links':int(bad_vertex_links),
 'degenerate_triangles':int((m.area_faces<1e-10).sum()),
 'triangle_count':len(m.faces),'vertex_count':len(m.vertices),
 'base_minimum_z_mm':float(m.bounds[0,2]),
 'coplanar_base_area_mm2':float(m.area_faces[np.all(np.abs(m.triangles[:,:,2])<1e-5,axis=1)].sum()),
 'physical_test_print_performed':False,
 'limitations':'Geometric topology checks only; not a slicer simulation, self-intersection certification, or physical print test.'
}
result['pass']=bool(shaft_planes==6 and all(n==6 for n in section_counts) and result['watertight'] and result['winding_consistent'] and result['positive_volume'] and len(components)==1 and result['nonmanifold_or_boundary_edges']==0 and result['degenerate_triangles']==0 and result['base_minimum_z_mm']==0 and result['euler_characteristic']==2 and result['nonmanifold_vertex_links']==0 and result['finite_vertex_coordinates'] and abs(result['dimensions_mm'][2]-200)<.01 and result['coplanar_base_area_mm2']>0)
open(os.path.join(root,'validation.json'),'w').write(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
assert result['pass'], 'Mesh validation failed'
