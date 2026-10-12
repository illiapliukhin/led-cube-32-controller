#!/usr/bin/env python3
"""Branch board v1 PCB generator. SOURCE OF TRUTH = branch_v1.kicad_sch: every footprint, value, LCSC field and
pad net is read from the schematic netlist; this script only places and routes.
250 x 100 mm, 2-layer: logic top-left, 16 strand columns along the bottom (13.5 mm pitch), 12 V power stage on the right.
Run: ../../kpy.sh $PWD/branch_gen.py"""
import sys, os, math, json, time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,'../../tools'))
import pcbnew
from pcbkit import Board, V, MM
from router import Router
import netlist
F,B=pcbnew.F_Cu,pcbnew.B_Cu
comps,pin2net=netlist.read(os.path.join(HERE,'branch_v1.kicad_sch'))
bd=Board(); b=bd.b
W=250.0; H=100.0
ds=b.GetDesignSettings()
ds.m_MinClearance=int(0.127*MM); ds.m_TrackMinWidth=int(0.15*MM); ds.m_ViasMinSize=int(0.45*MM); ds.m_MinThroughDrill=int(0.2*MM)
ds.m_CopperEdgeClearance=int(0.3*MM); ds.m_HoleToHoleMin=int(0.25*MM); ds.SetBoardThickness(int(1.6*MM))
nc=ds.m_NetSettings.GetDefaultNetclass(); nc.SetClearance(int(0.15*MM)); nc.SetTrackWidth(int(0.2*MM)); nc.SetViaDiameter(int(0.5*MM)); nc.SetViaDrill(int(0.3*MM))
def eline(a,c):
    s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(int(0.1*MM)); b.Add(s)
def earc(a,m,c):
    s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetArcGeometry(V(*a),V(*m),V(*c)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(int(0.1*MM)); b.Add(s)
R=4.0; k_=R*(1-1/math.sqrt(2))
eline((R,0),(W-R,0)); earc((W-R,0),(W-k_,k_),(W,R)); eline((W,R),(W,H-R)); earc((W,H-R),(W-k_,H-k_),(W-R,H))
eline((W-R,H),(R,H)); earc((R,H),(k_,H-k_),(0,H-R)); eline((0,H-R),(0,R)); earc((0,R),(k_,k_),(R,0))
def N(n): return '/'+n
FP={}
def place(ref,x,y,rot=0,flip=False):
    c=comps[ref]; lib,name=c['footprint'].split(':')
    f=bd.fp(lib,name,ref,c['value'],x,y,rot,{k:v for k,v in c['fields'].items() if k in ('LCSC','MPN')})
    if flip: f.Flip(f.GetPosition(),False)
    for p in f.Pads():
        n=pin2net.get((ref,p.GetNumber()))
        if n: p.SetNet(bd.net(n))
    FP[ref]=f; return f
def P2(ref,n): return bd.padxy(FP[ref],n)
# ---------------- placement ----------------
place('J1',8,9.5,90); place('J2',66,9.5,90)
for i,x in enumerate((18,34,50)): place('U%d'%(i+1),x,24,270)
place('U4',96,26,0); place('U5',112,22,0)
for k in range(6):
    place('RID%d'%k,124+5*k,14,90); place('JP%d'%k,124+5*k,22,90)
DRV={'U8':(62,30),'U6':(62,44),'U9':(166,30),'U7':(166,44)}
for r,(x,y) in DRV.items(): place(r,x,y,270)
# decoupling: C1..C3 -> U1..U3, C4 U4, C5 U5, C6..C9 -> U6..U9
for i,u in enumerate(['U1','U2','U3','U4','U5','U6','U7','U8','U9']):
    ux,uy=FP[u].GetPosition().x/MM,FP[u].GetPosition().y/MM
    off={'U4':(0,-8.6),'U5':(0,-3.0)}.get(u,(5.6,0))
    place('C%d'%(i+1),ux+off[0],uy+off[1],0)
XC=[12+13.5*i for i in range(16)]
def SOT_ori(ref,x,y):
    for rot in (0,90,180,270):
        f=place(ref,x,y,rot); p1=P2(ref,1); p4=P2(ref,4); p6=P2(ref,6)
        if p6[1]<p1[1]-0.5 and p6[0]<p4[0]: return f
        b.Remove(f)
    raise RuntimeError(ref)
for i,x in enumerate(XC):
    place('J%d'%(10+i),x,93,0)
    place('RD%d'%i,x+2.5,78,90); place('RC%d'%i,x+5,78,90)
    SOT_ori('UE%d'%i,x+3.75,85)
    place('F%d'%(10+i),x-1.5,82.5,90)
for k,i in zip(range(10,16),(1,4,6,9,12,14)): place('C%d'%k,XC[i]+9.2,71.5,90)
# power stage (x 222..250)
place('J30',234.5,6.5,0); place('D30',228,15,90); place('U30',238,17,0)
place('R30',243,13,0); place('R31',243,15,0); place('R40',243,19,0); place('R32',243,21,0)
place('R33',233,21,90); place('C30',238,22,0); place('C31',247.5,17,90); place('R34',247.5,22,90)
place('C32',232,12,90)
place('U31',235,32,0)
place('C33',230.5,32,90); place('C34',239.5,32,90); place('C35',226,26,90)
place('C36',231.3,28,0); place('C37',237.6,27.2,0); place('C38',241.5,27.5,90)
place('R35',244,24.5,0); place('R36',244,26.5,0); place('R37',246.8,29.5,90); place('R38',248.8,29.5,90); place('R39',244,34,90)
place('L30',235,43,0)
for k,y in zip(range(40,46),(50,53.5,57,60.5,64,67.5)): place('C%d'%k,244,y,0)
for i,(x,y) in enumerate([(4,40),(W-4,80),(4,H-4),(W-4,H-4)]):
    h=bd.fp('MountingHole','MountingHole_3.2mm_M3','H%d'%(i+1),'M3',x,y); h.SetBoardOnly(True); h.SetExcludedFromBOM(True); h.SetExcludedFromPosFiles(True)
for i,(x,y) in enumerate([(118,3),(4,60),(220,96.5)]):
    h=bd.fp('Fiducial','Fiducial_1mm_Mask2mm','FID%d'%(i+1),'FID',x,y); h.SetBoardOnly(True); h.SetExcludedFromBOM(True)
missing=set(comps)-set(FP); assert not missing, missing
print('placed',len(FP))
# ---------------- structured routing ----------------
VD,VDR=0.5,0.3
def path(pts,net,w=0.2,layer=F,r=0.6): bd.path(pts,w,layer,net,r)
def pn(ref,n): return bd.pad(FP[ref],n).GetNetname()
def fan(u,cols,layer,y0,via_first=False):
    """staircase fan-out from B-row pins (11..18) of a TSSOP rotated 270 (B row down) to column x list"""
    items=[]
    for k in range(8):
        bx,by=P2(u,18-k); items.append((bx,by,cols[k],pn(u,18-k)))
    R_=sorted([t for t in items if t[2]>=t[0]],key=lambda t:t[0]); L_=sorted([t for t in items if t[2]<t[0]],key=lambda t:-t[0])
    ends=[]
    for grp in (R_,L_):
        n=len(grp)
        for i,(bx,by,tx,net) in enumerate(grp):
            rank=n-1-i; yl=y0+0.6*rank
            if via_first:
                vy=by+(1.2 if (18-[t[3] for t in items].index(net))%2==0 else 2.3)
                path([(bx,by),(bx,vy)],net); bd.via(bx,vy,net,VD,VDR)
                path([(bx,vy),(bx,yl),(tx,yl)],net,0.2,layer)
            else: path([(bx,by),(bx,yl),(tx,yl)],net,0.2,layer)
            ends.append((tx,yl,net))
    return ends
for u,i0 in (('U6',0),('U7',8)):
    for tx,yl,net in fan(u,[XC[i0+7-k]+2.5 for k in range(8)],F,48.6):
        i=[j for j in range(16) if abs(XC[j]+2.5-tx)<1e-6][0]
        top=P2('RD%d'%i,1) if P2('RD%d'%i,1)[1]<P2('RD%d'%i,2)[1] else P2('RD%d'%i,2)
        path([(tx,yl),(tx,top[1])],net)
for u,i0 in (('U8',0),('U9',8)):
    for tx,yl,net in fan(u,[XC[i0+7-k]+5 for k in range(8)],B,35.0,True):
        i=[j for j in range(16) if abs(XC[j]+5-tx)<1e-6][0]
        top=P2('RC%d'%i,1) if P2('RC%d'%i,1)[1]<P2('RC%d'%i,2)[1] else P2('RC%d'%i,2)
        path([(tx,yl),(tx,75.6)],net,0.2,B); bd.via(tx,75.6,net,VD,VDR); path([(tx,75.6),top],net)
# driver power: VCC pin20 / DIR pin1 -> +5V riser at cx+4.2 ; OE pin19 -> GND via under body ; pin10 GND
for u in ('U1','U2','U3','U6','U7','U8','U9'):
    cx,cy=FP[u].GetPosition().x/MM,FP[u].GetPosition().y/MM
    p20=P2(u,20); p1=P2(u,1); p19=P2(u,19); p10=P2(u,10); xo=cx+4.2; v5=pn(u,20)
    path([p20,(xo,p20[1]),(xo,p1[1])],v5,0.3); path([p1,(xo,p1[1])],v5,0.3)
    c=[q for q in FP['C%d'%(['U1','U2','U3','U4','U5','U6','U7','U8','U9'].index(u)+1)].Pads()]
    cp=[q for q in c if q.GetNetname()==v5][0]; cg=[q for q in c if q.GetNetname()!=v5][0]
    path([(cp.GetPosition().x/MM,cy),(xo,cy)],v5,0.3)
    gx=cg.GetPosition().x/MM; path([(gx,cy),(gx+1.0,cy)],N('GND'),0.3); bd.via(gx+1.0,cy,N('GND'),VD,VDR)
    path([p19,(p19[0],cy)],N('GND'),0.25); bd.via(p19[0],cy,N('GND'),VD,VDR)
    path([p10,(p10[0]-1.1,p10[1])],N('GND'),0.3); bd.via(p10[0]-1.1,p10[1],N('GND'),VD,VDR)
# GCLK tie bar on U8/U9 inputs (A row up, pins 2..9)
for u in ('U8','U9'):
    ps=[P2(u,n) for n in range(2,10)]; y=ps[0][1]-1.1
    for x,yy in ps: path([(x,yy),(x,y)],N('GCLK'),0.2)
    path([(min(p[0] for p in ps),y),(max(p[0] for p in ps),y)],N('GCLK'),0.2)
# strand columns
for i,x in enumerate(XC):
    ue='UE%d'%i
    for rr,io_in,io_out,jp,col in (('RD%d'%i,6,1,2,x+2.5),('RC%d'%i,4,3,3,x+5)):
        r2=max((P2(rr,1),P2(rr,2)),key=lambda p:p[1]); a=P2(ue,io_in); o=P2(ue,io_out); j=P2('J%d'%(10+i),jp)
        net=bd.pad(FP[ue],io_in).GetNetname()
        path([r2,(r2[0],80.4),(a[0],82.4),a],net,0.25,F,0.4)
        path([o,(o[0],87.9),(j[0],89.6),j],net,0.25,F,0.4)
    v5p=P2(ue,5); path([v5p,(v5p[0],82.7)],N('+5V'),0.3); bd.via(v5p[0],82.7,N('+5V'),VD,VDR)
    fp_=FP['F%d'%(10+i)]; pa=[q for q in fp_.Pads() if q.GetNetname()==N('+5V')][0]; pb=[q for q in fp_.Pads() if q.GetNetname()!=N('+5V')][0]
    ax,ay=pa.GetPosition().x/MM,pa.GetPosition().y/MM; bx_,by_=pb.GetPosition().x/MM,pb.GetPosition().y/MM
    for dx in (-0.9,0.9): bd.via(ax+dx,ay,N('+5V'),0.6,0.35)
    j1=P2('J%d'%(10+i),1); path([(bx_,by_),(bx_,88.0),(j1[0],90.2),j1],pb.GetNetname(),0.8,F,0.8)
for k in range(10,16):
    c=FP['C%d'%k]; pv=[q for q in c.Pads() if q.GetNetname()==N('+5V')][0]
    x,y=pv.GetPosition().x/MM,pv.GetPosition().y/MM; bd.via(x+1.2,y,N('+5V'),0.6,0.35); path([(x,y),(x+1.2,y)],N('+5V'),0.5)
# output caps + C33/C34 GND -> vias
print('structured done',flush=True)
# ---------------- zones (power stage done mainly with zones) ----------------
def zone(layer,net,poly,prio=0,solid=False,clr=0.25):
    z=pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(bd.net(net)); o=z.Outline(); o.NewOutline()
    for x,y in poly: o.Append(int(x*MM),int(y*MM))
    z.SetLocalClearance(int(clr*MM)); z.SetMinThickness(int(0.2*MM)); z.SetAssignedPriority(prio)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if solid else pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(int(0.25*MM)); z.SetThermalReliefSpokeWidth(int(0.4*MM)); b.Add(z); return z
def rect(x0,y0,x1,y1): return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
zone(F,N('GND'),rect(0.3,0.3,W-0.3,H-0.3),0)
zone(B,N('GND'),rect(221.5,0.3,W-0.3,66.0),0)
zone(B,N('+5V'),[(0.3,0.3),(221.0,0.3),(221.0,66.6),(W-0.3,66.6),(W-0.3,H-0.3),(0.3,H-0.3)],1,True)
# power-stage F zones
ux,uy=FP['U31'].GetPosition().x/MM,FP['U31'].GetPosition().y/MM
zone(F,N('V12_IN'),[(224.5,3.0),(244,3.0),(244,10.5),(239.4,10.5),(238.05,18.3),(237.9,18.3),(237.9,19.8),(224.5,19.8)],3,True,0.2)
zone(F,N('+12V'),[(238.1,18.3),(238.3,18.3),(240,23.5),(240,24.5),(234.5,24.5),(229,25.5),(229,34.6),(233.4,34.6),(233.4,30.9),(236.6,30.9),(236.6,34.6),(242,34.6),(242,29.0),(240.6,24.0),(240.6,19.8),(238.2,19.8)],3,True,0.2)
zone(F,N('SW5'),[(234.45,33.3),(235.55,33.3),(235.55,36.4),(233.0,36.4),(233.0,46),(228.7,46),(228.7,39.6),(234.45,36.4)],4,True,0.2)
zone(F,N('+5V'),[(237.2,36.4),(249.5,36.4),(249.5,69.5),(237.2,69.5)],3,True,0.2)
# vias F +5V zone -> B +5V strip
for x in (238.5,240.5,247.5,249.0):
    for y in (67.5,68.8): bd.via(x,y,N('+5V'),0.6,0.35)
# ---------------- A* for logic + power small-signal ----------------
rt=Router(bd,0,0,W,66.0,step=0.25,w=0.2,clr=0.15)
rt.block_rect([0,1],221.5,0,W,66.0,None)       # power stage handled separately
rt.load_board()
def pp(pad):
    x,y=pad.GetPosition().x/MM,pad.GetPosition().y/MM
    ls=[0,1] if pad.GetAttribute()==pcbnew.PAD_ATTRIB_PTH else ([0] if pad.IsOnLayer(F) else [1])
    return [(x,y,l) for l in ls]
def P(ref,n): return pp(bd.pad(FP[ref],n))
fails=[]
def con(rt_,net,src,dst=None,to_net=False,w=None,**kw):
    ok=rt_.connect(net,src,dst,to_net,w,**kw)
    if not ok: fails.append((net,src[0][:2])); print('FAIL',net,src[0][:2],flush=True)
    return ok
# GND vias for SMD GND pads (both regions)
def gnd_via(r_,pad,NET='/GND'):
    x,y=pad.GetPosition().x/MM,pad.GetPosition().y/MM
    for rr in (0.9,1.2,1.6,2.0,2.6):
        for a in range(0,360,30):
            vx=x+rr*math.cos(math.radians(a)); vy=y+rr*math.sin(math.radians(a))
            i,j=r_.ij(vx,vy)
            if not(0<=i<r_.nx and 0<=j<r_.ny): continue
            c=r_.code(NET)
            if r_.Vg[j,i] not in (-1,c) or r_.T[1][j,i] not in (-1,c): continue
            res=r_.route(NET,[(x,y,0)],[(vx,vy,0)],False,via_cost=10**6,maxit=3000)
            if res is None: continue
            vxy=r_.xy(i,j); r_.commit(NET,res,0.3,(x,y),vxy); bd.via(vxy[0],vxy[1],NET,VD,VDR); r_.block_circle([0,1],vxy[0],vxy[1],VD/2,NET); return True
    fails.append((NET+'VIA',(round(x,2),round(y,2)))); return False
t0=time.time()
for r in FP:
    f=FP[r]
    if f.GetPosition().x/MM<221.5 and f.GetPosition().y/MM<62:
        for pad in f.Pads():
            if pad.GetNetname()==N('+5V') and pad.GetAttribute()==pcbnew.PAD_ATTRIB_SMD: gnd_via(rt,pad,N('+5V'))
print('5v vias',len(fails),flush=True)
# nets: group pads by net within the logic region, connect as trees (nearest-first)
logic=[r for r in FP if FP[r].GetPosition().x/MM<221 and FP[r].GetPosition().y/MM<62]
bynet={}
for r in logic:
    for p in FP[r].Pads():
        n=p.GetNetname()
        if n and n not in (N('GND'),) and not n.startswith('unconnected'): bynet.setdefault(n,[]).append(p)
TARGET5=[(x,70.2,1) for x in [XC[i]+8.6 for i in range(16)]]+[(x,70.2,1) for x in (6,)]
order=sorted(bynet,key=lambda n:len(bynet[n]))
for n in order:
    ps=bynet[n]
    if n==N('+5V'): continue
    if len(ps)<2: continue
    done=[ps[0]]; rest=ps[1:]
    while rest:
        p=min(rest,key=lambda q:min((q.GetPosition()-d.GetPosition()).EuclideanNorm() for d in done))
        d=min(done,key=lambda q:(q.GetPosition()-p.GetPosition()).EuclideanNorm()); con(rt,n,pp(p),pp(d)); done.append(p); rest.remove(p)
print('logic',time.time()-t0,len(fails),flush=True)
# +5V trunk to strip if nothing reached it: explicit
# power stage small signals with a fine router
rp=Router(bd,221.5,0,W,70,step=0.125,w=0.2,clr=0.15)
rp.load_board()
pw=[r for r in FP if FP[r].GetPosition().x/MM>=221.5]
ZN={N('V12_IN'),N('+12V'),N('SW5'),N('+5V'),N('GND')}
bynet={}
for r in pw:
    for p in FP[r].Pads():
        n=p.GetNetname()
        if n and n not in ZN and not n.startswith('unconnected'): bynet.setdefault(n,[]).append(p)
for n,ps in sorted(bynet.items(),key=lambda kv:len(kv[1])):
    done=[ps[0]]; rest=ps[1:]
    while rest:
        p=min(rest,key=lambda q:min((q.GetPosition()-d.GetPosition()).EuclideanNorm() for d in done))
        d=min(done,key=lambda q:(q.GetPosition()-p.GetPosition()).EuclideanNorm()); con(rp,n,pp(p),pp(d)); done.append(p); rest.remove(p)
print('power',time.time()-t0,len(fails),flush=True)
for r in FP:
    f=FP[r]; fx,fy=f.GetPosition().x/MM,f.GetPosition().y/MM
    if fy>62: continue
    r_=rp if fx>=221.5 else rt
    for pad in f.Pads():
        if pad.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD: continue
        if pad.GetNetname()==N('GND') and fx>=221.5: gnd_via(r_,pad)
print('gnd',time.time()-t0,len(fails),flush=True)
# stitching GND vias (top region only, B is GND there)
st=Router(bd,0,0,W,66,step=0.5,w=0.2,clr=0.3); st.load_board(); nst=0
for x in [6+5*i for i in range(49)]:
    for y in [6+5*j for j in range(12)]:
        if x<221: continue
        i,j=st.ij(x,y)
        if all(st.Vg[jj,ii]==-1 for jj in range(j-2,j+3) for ii in range(i-2,i+3) if 0<=jj<st.ny and 0<=ii<st.nx) and all(st.T[l][j,i]==-1 for l in (0,1)):
            bd.via(x,y,N('GND'),0.6,0.3); nst+=1
for f in b.GetFootprints():
    for t in (f.Reference(),):
        t.SetLayer(pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab)
json.dump({'fails':fails,'stitch':nst},open(os.path.join(HERE,'route_report.json'),'w'),indent=1)
bd.save(os.path.join(HERE,'branch_v1.kicad_pcb')); print('saved; fails',len(fails),fails[:30],'time',time.time()-t0)
