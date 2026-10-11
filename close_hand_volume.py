import os,sys,numpy as np,trimesh
from scipy.ndimage import binary_closing,binary_fill_holes,gaussian_filter
from skimage.measure import marching_cubes
from skimage.morphology import ball
p=sys.argv[1];d=np.load(p);m=trimesh.Trimesh(d['vertices'],d['faces'],process=True)
pitch=.17
v=m.voxelized(pitch).fill(); origin=v.transform[:3,3]-pitch*6
a=np.pad(v.matrix,6)
a=np.logical_and(np.maximum.accumulate(a,axis=1),np.maximum.accumulate(a[:,::-1,:],axis=1)[:,::-1,:])
for radius in [1,2,3,4,5,6]:
 b=binary_fill_holes(binary_closing(a,structure=ball(radius)))
 verts,faces,_,_=marching_cubes(gaussian_filter(b.astype(np.float32),1.2),.5,spacing=(pitch,)*3)
 n=trimesh.Trimesh(verts+origin,faces,process=True);n.fix_normals()
 parts=n.split();n=max(parts,key=lambda x:x.volume)
 print('Volume closing radius',radius,'Euler',n.euler_number,flush=True)
 if n.euler_number==2 and n.is_watertight:break
else:raise RuntimeError('Could not eliminate through holes')
# Verify winding from raw coordinates rather than cached mesh properties.
tri=n.vertices[n.faces]
signed=float(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6.0)
if signed<0:n.invert()
np.savez(p,vertices=n.vertices,faces=n.faces)
