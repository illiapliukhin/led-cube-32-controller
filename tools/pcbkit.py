"""Small helper kit on top of pcbnew: footprints, arc-filleted routing, simple 2-layer A* router."""
import math, heapq, pcbnew
FPLIB='/workspace/.kicad10/AppDir/share/kicad/footprints/'
MM=1e6
def V(x,y): return pcbnew.VECTOR2I(int(round(x*MM)),int(round(y*MM)))
class Board:
    def __init__(s):
        s.b=pcbnew.BOARD(); s.nets={}
    def net(s,name):
        if name not in s.nets:
            n=pcbnew.NETINFO_ITEM(s.b,name); s.b.Add(n); s.nets[name]=n
        return s.nets[name]
    def fp(s,lib,name,ref,val,x,y,rot=0,fields=None):
        import os
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'../lib/cube.pretty') if lib=='cube' else FPLIB+lib+'.pretty'
        f=pcbnew.FootprintLoad(path,name)
        f.SetFPID(pcbnew.LIB_ID(lib,name))
        f.SetReference(ref); f.SetValue(val); s.b.Add(f)
        f.SetPosition(V(x,y)); f.SetOrientationDegrees(rot)
        for k,v in (fields or {}).items():
            f.SetField(k,v)
        return f
    def pad(s,f,num): 
        for p in f.Pads():
            if p.GetNumber()==str(num): return p
        raise KeyError(num)
    def setnet(s,f,num,net):
        s.pad(f,num).SetNet(s.net(net))
    def padxy(s,f,num):
        p=s.pad(f,num).GetPosition(); return (p.x/MM,p.y/MM)
    def seg(s,a,b,w,layer,net):
        t=pcbnew.PCB_TRACK(s.b); t.SetStart(V(*a)); t.SetEnd(V(*b)); t.SetWidth(int(w*MM)); t.SetLayer(layer); t.SetNet(s.net(net)); s.b.Add(t); return t
    def arc(s,a,m,b,w,layer,net):
        t=pcbnew.PCB_ARC(s.b); t.SetStart(V(*a)); t.SetMid(V(*m)); t.SetEnd(V(*b)); t.SetWidth(int(w*MM)); t.SetLayer(layer); t.SetNet(s.net(net)); s.b.Add(t); return t
    def via(s,x,y,net,d=0.6,drill=0.3):
        v=pcbnew.PCB_VIA(s.b); v.SetPosition(V(x,y)); v.SetWidth(int(d*MM)); v.SetDrill(int(drill*MM)); v.SetNet(s.net(net)); s.b.Add(v); return v
    def path(s,pts,w,layer,net,r=1.0):
        """polyline with circular fillets of radius r (auto-reduced) at every corner"""
        pts=[p for i,p in enumerate(pts) if i==0 or (abs(p[0]-pts[i-1][0])>1e-6 or abs(p[1]-pts[i-1][1])>1e-6)]
        if len(pts)<2: return
        cur=pts[0]
        for i in range(1,len(pts)-1):
            p0,p1,p2=pts[i-1],pts[i],pts[i+1]
            d1=(p1[0]-p0[0],p1[1]-p0[1]); d2=(p2[0]-p1[0],p2[1]-p1[1])
            l1=math.hypot(*d1); l2=math.hypot(*d2)
            u1=(d1[0]/l1,d1[1]/l1); u2=(d2[0]/l2,d2[1]/l2)
            cr=u1[0]*u2[1]-u1[1]*u2[0]; dot=u1[0]*u2[0]+u1[1]*u2[1]
            if abs(cr)<1e-9: continue
            th=math.acos(max(-1,min(1,dot))); t=math.tan(th/2)
            rr=min(r, 0.45*l1/t if i-1>0 else 0.95*l1/t, 0.45*l2/t if i+1<len(pts)-1 else 0.95*l2/t)
            dd=rr*t
            a=(p1[0]-u1[0]*dd,p1[1]-u1[1]*dd); b=(p1[0]+u2[0]*dd,p1[1]+u2[1]*dd)
            if math.hypot(a[0]-cur[0],a[1]-cur[1])>1e-4: s.seg(cur,a,w,layer,net)
            # centre
            n1=(-u1[1],u1[0]) if cr>0 else (u1[1],-u1[0])
            c=(a[0]+n1[0]*rr,a[1]+n1[1]*rr)
            bis=((a[0]+b[0])/2-c[0],(a[1]+b[1])/2-c[1]); bl=math.hypot(*bis)
            m=(c[0]+bis[0]/bl*rr,c[1]+bis[1]/bl*rr)
            if dd>1e-3: s.arc(a,m,b,w,layer,net)
            cur=b
        s.seg(cur,pts[-1],w,layer,net)
    def save(s,fn):
        s.b.Save(fn)

class Grid:
    """2-layer occupancy grid; A* with via cost; returns orthogonal polylines."""
    def __init__(s,x0,y0,x1,y1,step=0.2):
        s.x0,s.y0,s.step=x0,y0,step; s.nx=int((x1-x0)/step)+1; s.ny=int((y1-y0)/step)+1
        s.occ=[[ [None]*s.nx for _ in range(s.ny)] for _ in range(2)]
    def ij(s,x,y): return int(round((x-s.x0)/s.step)),int(round((y-s.y0)/s.step))
    def xy(s,i,j): return (s.x0+i*s.step,s.y0+j*s.step)
    def block_rect(s,layer,xa,ya,xb,yb,net):
        ia,ja=s.ij(xa,ya); ib,jb=s.ij(xb,yb)
        for j in range(max(0,min(ja,jb)),min(s.ny,max(ja,jb)+1)):
            row=s.occ[layer][j]
            for i in range(max(0,min(ia,ib)),min(s.nx,max(ia,ib)+1)):
                if row[i] is None or row[i]!=net: row[i]= '#' if (row[i] not in (None,net)) else net
    def block_circle(s,layer,x,y,r,net):
        ia,ja=s.ij(x-r,y-r); ib,jb=s.ij(x+r,y+r)
        for j in range(max(0,ja),min(s.ny,jb+1)):
            for i in range(max(0,ia),min(s.nx,ib+1)):
                px,py=s.xy(i,j)
                if (px-x)**2+(py-y)**2<=r*r:
                    v=s.occ[layer][j][i]; s.occ[layer][j][i]= net if v in (None,net) else '#'
    def block_seg(s,layer,a,b,r,net):
        n=int(math.hypot(b[0]-a[0],b[1]-a[1])/(s.step/2))+1
        for k in range(n+1):
            t=k/n; s.block_circle(layer,a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,r,net)
    def free(s,l,i,j,net):
        if not(0<=i<s.nx and 0<=j<s.ny): return False
        v=s.occ[l][j][i]; return v is None or v==net
    def route(s,src,dst,net,layers=(0,1),via_cost=40,maxit=600000):
        """src/dst: list of (x,y,layer) ; returns list of (layer, [pts]) segments and via points"""
        starts=[(s.ij(x,y),l) for x,y,l in src]; goals={(s.ij(x,y),l) for x,y,l in dst}
        gx=sum(g[0][0] for g in goals)/len(goals); gy=sum(g[0][1] for g in goals)/len(goals)
        openh=[]; came={}; cost={}
        for (i,j),l in starts:
            k=(i,j,l,-1); cost[k]=0; heapq.heappush(openh,(0,k))
        it=0; end=None
        D=[(1,0),(-1,0),(0,1),(0,-1)]
        while openh and it<maxit:
            it+=1; _,k=heapq.heappop(openh); i,j,l,d=k
            if ((i,j),l) in goals: end=k; break
            c=cost[k]
            nb=[]
            for di,(a,b2) in enumerate(D):
                ni,nj=i+a,j+b2
                if s.free(l,ni,nj,net): nb.append(((ni,nj,l,di),c+1+(0 if d in(-1,di) else 3)))
            ol=1-l
            if ol in layers and s.free(ol,i,j,net) and s.viaok(i,j,net):
                nb.append(((i,j,ol,-1),c+via_cost))
            for nk,nc in nb:
                if nc<cost.get(nk,1e18):
                    cost[nk]=nc; came[nk]=k
                    h=abs(nk[0]-gx)+abs(nk[1]-gy)
                    heapq.heappush(openh,(nc+h,nk))
        if end is None: return None
        seq=[end]
        while seq[-1] in came: seq.append(came[seq[-1]])
        seq.reverse()
        out=[]; vias=[]; curl=seq[0][2]; pts=[s.xy(seq[0][0],seq[0][1])]
        for k in seq[1:]:
            p=s.xy(k[0],k[1])
            if k[2]!=curl:
                out.append((curl,pts)); vias.append(p); curl=k[2]; pts=[p]
            else: pts.append(p)
        out.append((curl,pts))
        # simplify collinear
        res=[]
        for l,pp in out:
            q=[pp[0]]
            for idx in range(1,len(pp)-1):
                a,b,c=q[-1],pp[idx],pp[idx+1]
                if abs((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]))>1e-9: q.append(b)
            q.append(pp[-1]); res.append((l,q))
        return res,vias
    viamask=None
    def viaok(s,i,j,net):
        if s.viamask is None: return True
        v=s.viamask[j][i] if (0<=i<s.nx and 0<=j<s.ny) else '#'
        return v is None or v==net
