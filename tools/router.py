"""2-layer grid A* router with separate track/via keepout grids and arc-filleted output."""
import math, heapq, pcbnew
from pcbkit import MM
import sys; sys.path.insert(0,"/workspace/.py311site")
try:
    import numpy as np
except ImportError:
    np=None
class Router:
    def __init__(s,bd,x0,y0,x1,y1,step=0.25,w=0.2,clr=0.15,via_d=0.5,via_drill=0.3,edge=0.5):
        s.bd=bd; s.x0,s.y0,s.step=x0,y0,step; s.nx=int((x1-x0)/step)+1; s.ny=int((y1-y0)/step)+1
        s.w=w; s.clr=clr; s.vd=via_d; s.vdr=via_drill
        s.rt=w/2+clr+0.02; s.rv=via_d/2+clr+0.02
        # occupancy: -1 free, -2 multi/blocked, else net code
        s.T=[np.full((s.ny,s.nx),-1,dtype=np.int32) for _ in range(2)]
        s.Vg=np.full((s.ny,s.nx),-1,dtype=np.int32)
        s.codes={}; s.names=[]
        e=int(math.ceil(edge/step))
        for g in s.T+[s.Vg]:
            g[:e,:]=-2; g[-e:,:]=-2; g[:,:e]=-2; g[:,-e:]=-2
    def code(s,net):
        if net not in s.codes: s.codes[net]=len(s.names); s.names.append(net)
        return s.codes[net]
    def _mark(s,g,mask,c):
        sub=g[mask]; sub=np.where((sub==-1)|(sub==c),c,-2); g[mask]=sub
    def _region(s,xa,ya,xb,yb):
        ia=max(0,int(math.floor((xa-s.x0)/s.step))); ib=min(s.nx-1,int(math.ceil((xb-s.x0)/s.step)))
        ja=max(0,int(math.floor((ya-s.y0)/s.step))); jb=min(s.ny-1,int(math.ceil((yb-s.y0)/s.step)))
        return ia,ib,ja,jb
    def block_shape(s,layers,poly_fn,bbox,net,via_only=False):
        """poly_fn(X,Y,r)->bool mask of points within distance r of shape"""
        c=s.code(net) if net is not None else -3
        for r,grids in ((s.rt,[s.T[l] for l in layers]),(s.rv,[s.Vg])):
            if via_only and r==s.rt: continue
            ia,ib,ja,jb=s._region(bbox[0]-r,bbox[1]-r,bbox[2]+r,bbox[3]+r)
            if ia>ib or ja>jb: continue
            X=s.x0+np.arange(ia,ib+1)*s.step; Y=s.y0+np.arange(ja,jb+1)*s.step
            XX,YY=np.meshgrid(X,Y); m=poly_fn(XX,YY,r)
            for g in grids:
                sub=g[ja:jb+1,ia:ib+1]
                if c==-3: sub[m]=-2
                else:
                    v=sub[m]; sub[m]=np.where((v==-1)|(v==c),c,-2)
    def _geo(s,net,item,layers):
        if net is None: return
        if not hasattr(s,'geom'): s.geom={}
        s.geom.setdefault(net,[]).append((item,tuple(layers)))
    def nearest(s,net,x,y,layer):
        best=None
        for it,ls in getattr(s,'geom',{}).get(net,[]):
            if layer not in ls: continue
            if it[0]=='seg':
                (ax,ay),(bx,by),hw=it[1],it[2],it[3]; dx,dy=bx-ax,by-ay; L2=dx*dx+dy*dy or 1e-12
                t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/L2)); px,py=ax+t*dx,ay+t*dy
            elif it[0]=='circ': px,py=it[1],it[2]
            else:
                xa,ya,xb,yb=it[1:]; px=min(max(x,xa),xb); py=min(max(y,ya),yb)
                # move to rect centre line to guarantee overlap
                cx_,cy_=(xa+xb)/2,(ya+yb)/2; px=px+0.5*(cx_-px); py=py+0.5*(cy_-py)
            d=(px-x)**2+(py-y)**2
            if best is None or d<best[0]: best=(d,(px,py))
        return best
    def block_seg(s,layers,a,b,hw,net):
        s._geo(net,('seg',a,b,hw),layers)
        ax,ay=a; bx,by=b; dx,dy=bx-ax,by-ay; L2=dx*dx+dy*dy or 1e-12
        def fn(X,Y,r):
            t=np.clip(((X-ax)*dx+(Y-ay)*dy)/L2,0,1); px=ax+t*dx-X; py=ay+t*dy-Y
            return px*px+py*py<=(r+hw)**2
        s.block_shape(layers,fn,(min(ax,bx)-hw,min(ay,by)-hw,max(ax,bx)+hw,max(ay,by)+hw),net)
    def block_circle(s,layers,x,y,rad,net):
        s._geo(net,('circ',x,y,rad),layers)
        s.block_shape(layers,lambda X,Y,r:(X-x)**2+(Y-y)**2<=(r+rad)**2,(x-rad,y-rad,x+rad,y+rad),net)
    def block_rect(s,layers,xa,ya,xb,yb,net):
        s._geo(net,('rect',xa,ya,xb,yb),layers)
        def fn(X,Y,r):
            dx=np.maximum(np.maximum(xa-X,X-xb),0); dy=np.maximum(np.maximum(ya-Y,Y-yb),0); return dx*dx+dy*dy<=r*r
        s.block_shape(layers,fn,(xa,ya,xb,yb),net)
    def load_board(s):
        b=s.bd.b
        for t in b.GetTracks():
            n=t.GetNetname()
            if t.GetClass()=='PCB_VIA':
                p=t.GetPosition(); s.block_circle([0,1],p.x/MM,p.y/MM,t.GetWidth(pcbnew.F_Cu)/2/MM,n)
            else:
                l=0 if t.GetLayer()==pcbnew.F_Cu else 1; a=t.GetStart(); e=t.GetEnd()
                s.block_seg([l],(a.x/MM,a.y/MM),(e.x/MM,e.y/MM),t.GetWidth()/2/MM,n)
        for f in b.GetFootprints():
            for p in f.Pads():
                n=p.GetNetname() or None
                bb=p.GetBoundingBox(); att=p.GetAttribute()
                if att in (pcbnew.PAD_ATTRIB_PTH,pcbnew.PAD_ATTRIB_NPTH): ls=[0,1]
                else: ls=[0] if p.IsOnLayer(pcbnew.F_Cu) else [1]
                if att==pcbnew.PAD_ATTRIB_NPTH: n=None
                s.block_rect(ls,bb.GetX()/MM,bb.GetY()/MM,bb.GetRight()/MM,bb.GetBottom()/MM,n if n else None)
    def ij(s,x,y): return int(round((x-s.x0)/s.step)),int(round((y-s.y0)/s.step))
    def xy(s,i,j): return (s.x0+i*s.step,s.y0+j*s.step)
    def route(s,net,src,dst_pts=None,to_net=False,via_cost=30,maxit=2_000_000,bbox_margin=None):
        c=s.code(net)
        T0,T1,Vg=s.T[0],s.T[1],s.Vg
        goals=set()
        for x,y,l in (dst_pts or []):
            i,j=s.ij(x,y); goals.add((i,j,l))
        if to_net:
            for l in (0,1):
                js,is_=np.nonzero(s.T[l]==c)
                # only cells that are actual copper of the net: approximate with cells marked c (inflated) -> fine as goal
                for j,i in zip(js[::1],is_[::1]): goals.add((int(i),int(j),l))
        starts=[]
        for x,y,l in src:
            i,j=s.ij(x,y); starts.append((i,j,l))
        goals-=set(starts)
        if not goals: return None
        if to_net and dst_pts is None:
            pass
        gl=list(goals)
        if len(gl)>4000: 
            import random; random.seed(1); hs=random.sample(gl,4000)
        else: hs=gl
        hx=np.array([g[0] for g in hs]); hy=np.array([g[1] for g in hs])
        def H(i,j): return int(np.min(np.abs(hx-i)+np.abs(hy-j)))
        hcache={}
        def h(i,j):
            k=(i>>2,j>>2)
            if k not in hcache: hcache[k]=max(0,H(i,j)-6)
            return hcache[k]
        openh=[]; came={}; cost={}
        for st in starts:
            k=st+(-1,); cost[k]=0; heapq.heappush(openh,(h(st[0],st[1]),0,k))
        D=((1,0),(-1,0),(0,1),(0,-1)); end=None; it=0
        nx,ny=s.nx,s.ny
        while openh and it<maxit:
            it+=1; f,cc,k=heapq.heappop(openh)
            if cc>cost.get(k,1e18): continue
            i,j,l,d=k
            if (i,j,l) in goals: end=k; break
            g=T0 if l==0 else T1
            for di,(a,b2) in enumerate(D):
                ni,nj=i+a,j+b2
                if 0<=ni<nx and 0<=nj<ny:
                    v=g[nj,ni]
                    if v==-1 or v==c:
                        nc=cc+1+(0 if d in(-1,di) else 2)
                        nk=(ni,nj,l,di)
                        if nc<cost.get(nk,1e18):
                            cost[nk]=nc; came[nk]=k; heapq.heappush(openh,(nc+h(ni,nj),nc,nk))
            ol=1-l; og=T1 if l==0 else T0; vv=Vg[j,i]; ov=og[j,i]
            if (vv==-1 or vv==c) and (ov==-1 or ov==c):
                nk=(i,j,ol,-1); nc=cc+via_cost
                if nc<cost.get(nk,1e18): cost[nk]=nc; came[nk]=k; heapq.heappush(openh,(nc+h(i,j),nc,nk))
        if end is None: return None
        seq=[end]
        while seq[-1] in came: seq.append(came[seq[-1]])
        seq.reverse()
        segs=[]; vias=[]; curl=seq[0][2]; pts=[s.xy(seq[0][0],seq[0][1])]
        for k in seq[1:]:
            p=s.xy(k[0],k[1])
            if k[2]!=curl: segs.append((curl,pts)); vias.append(p); curl=k[2]; pts=[p]
            else: pts.append(p)
        segs.append((curl,pts))
        out=[]
        for l,pp in segs:
            q=[pp[0]]
            for idx in range(1,len(pp)-1):
                a,b,cpt=q[-1],pp[idx],pp[idx+1]
                if abs((b[0]-a[0])*(cpt[1]-b[1])-(b[1]-a[1])*(cpt[0]-b[0]))>1e-9: q.append(b)
            q.append(pp[-1]); out.append((l,q))
        return out,vias,end
    def commit(s,net,res,w=None,first=None,last=None,r=0.5):
        w=w or s.w; segs,vias,_=res
        L=[pcbnew.F_Cu,pcbnew.B_Cu]
        for n,(l,pts) in enumerate(segs):
            pts=list(pts)
            if n==0 and first is not None: pts=[first]+pts
            if n==len(segs)-1 and last is not None: pts=pts+[last]
            s.bd.path(pts,w,L[l],net,r)
            for a,b in zip(pts,pts[1:]): s.block_seg([l],a,b,w/2,net)
        for x,y in vias:
            s.bd.via(x,y,net,s.vd,s.vdr); s.block_circle([0,1],x,y,s.vd/2,net)
    def connect(s,net,src,dst=None,to_net=False,w=None,**kw):
        """src/dst: list of (x,y,layer). Adds exact stub from first src point / to dst point."""
        res=s.route(net,src,dst,to_net,**kw)
        if res is None: return False
        segs,vias,end=res
        # determine exact endpoints
        sp=segs[0][1][0]; first=min(src,key=lambda p:(p[0]-sp[0])**2+(p[1]-sp[1])**2)[:2]
        last=None
        if dst:
            ep=segs[-1][1][-1]; cand=min(dst,key=lambda p:(p[0]-ep[0])**2+(p[1]-ep[1])**2)
            if (cand[0]-ep[0])**2+(cand[1]-ep[1])**2<0.25: last=cand[:2]
        elif to_net:
            ep=segs[-1][1][-1]; lay=segs[-1][0]
            nb=s.nearest(net,ep[0],ep[1],lay)
            if nb and nb[0]<1.0 and nb[0]>1e-6: last=nb[1]
        s.commit(net,res,w,first,last)
        return True
