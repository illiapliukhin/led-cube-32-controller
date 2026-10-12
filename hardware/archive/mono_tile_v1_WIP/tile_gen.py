#!/usr/bin/env python3
"""Generate LED-cube base tile v1 (250x250 mm, 2-layer, 4x MBI5153, 64 column holes).
Run with KiCad python: ../../kpy.sh tile_gen.py"""
import sys, os, math, json
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,'../../tools'))
import pcbnew
from pcbkit import Board, Grid, V, MM
F,B=pcbnew.F_Cu,pcbnew.B_Cu
W_SIG=0.25; W_PWR=0.5; W_OUT=0.3
bd=Board(); b=bd.b
# ---------- design rules / stackup ----------
ds=b.GetDesignSettings()
ds.m_MinClearance=int(0.127*MM); ds.m_TrackMinWidth=int(0.2*MM); ds.m_ViasMinSize=int(0.5*MM); ds.m_MinThroughDrill=int(0.3*MM)
ds.m_CopperEdgeClearance=int(0.3*MM); ds.m_HoleToHoleMin=int(0.25*MM)
nc=ds.m_NetSettings.GetDefaultNetclass(); nc.SetClearance(int(0.2*MM)); nc.SetTrackWidth(int(W_SIG*MM)); nc.SetViaDiameter(int(0.6*MM)); nc.SetViaDrill(int(0.3*MM))
# ---------- outline 250x250 with R5 corners ----------
def edge_line(a,c):
    s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(int(0.1*MM)); b.Add(s)
def edge_arc(a,m,c):
    s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetArcGeometry(V(*a),V(*m),V(*c)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(int(0.1*MM)); b.Add(s)
L=250.0; R=5.0; k=R*(1-1/math.sqrt(2))
edge_line((R,0),(L-R,0)); edge_arc((L-R,0),(L-k,k),(L,R)); edge_line((L,R),(L,L-R)); edge_arc((L,L-R),(L-k,L-k),(L-R,L))
edge_line((L-R,L),(R,L)); edge_arc((R,L),(k,L-k),(0,L-R)); edge_line((0,L-R),(0,R)); edge_arc((0,R),(k,k),(R,0))
# ---------- column-hole footprint (4x4 at 31.25 mm, pad n = OUT(n-1)) ----------
P1,P0=15.625,46.875
# (pin, OUT, hole_lx, hole_ly, layer, channel_x)
MAP=[(5,0,-P1,-P0,'F',-8),(6,1,-P0,-P0,'B',-20),(7,2,-P1,-P1,'F',-10),(8,3,-P0,-P1,'B',-22),
     (9,4,-P0,P1,'B',-22),(10,5,-P1,P1,'F',-10),(11,6,-P0,P0,'B',-20),(12,7,-P1,P0,'F',-8),
     (13,8,P1,P0,'F',8),(14,9,P0,P0,'B',20),(15,10,P1,P1,'F',10),(16,11,P0,P1,'B',22),
     (17,12,P0,-P1,'B',22),(18,13,P1,-P1,'F',10),(19,14,P0,-P0,'B',20),(20,15,P1,-P0,'F',8)]
LIBDIR=os.path.join(HERE,'cube.pretty'); os.makedirs(LIBDIR,exist_ok=True)
def make_colgrid():
    f=pcbnew.FOOTPRINT(b); f.SetFPID(pcbnew.LIB_ID('cube','COL_GRID_4x4_P31.25mm'))
    for pin,out,hx,hy,_,_ in MAP:
        p=pcbnew.PAD(f); p.SetNumber(str(out+1)); p.SetAttribute(pcbnew.PAD_ATTRIB_PTH); p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        p.SetSize(V(2.2,2.2)); p.SetDrillSize(V(1.1,1.1)); p.SetLayerSet(pcbnew.PAD.PTHMask()); p.SetPosition(V(hx,hy));
        p.SetFPRelativePosition(V(hx,hy)); f.Add(p)
    t=pcbnew.PCB_TEXT(f); 
    f.SetReference('J'); f.SetValue('COL_GRID_4x4')
    io=pcbnew.PCB_IO_MGR.FindPlugin(pcbnew.PCB_IO_MGR.KICAD_SEXP)
    io.FootprintSave(LIBDIR,f)
make_colgrid()
def colgrid(ref,x,y,rot):
    f=pcbnew.FootprintLoad(LIBDIR,'COL_GRID_4x4_P31.25mm'); f.SetReference(ref); f.SetValue('COLUMN_WIRES_16'); b.Add(f); f.SetPosition(V(x,y)); f.SetOrientationDegrees(rot)
    f.SetField('LCSC',''); return f
# ---------- placement ----------
Q={'U1':(62.5,62.5,True),'U2':(187.5,62.5,True),'U3':(62.5,187.5,False),'U4':(187.5,187.5,False)}
DRV_F={'MPN':'MBI5153GP-A','LCSC':'C183654','Alt':'ICND2153AP / MBI5253GP-A (same SSOP-24 pinout)'}
fps={}
def T(u,lx,ly):
    x,y,top=Q[u]; return (x-lx,y-ly) if top else (x+lx,y+ly)
idx=0
for u,(x,y,top) in Q.items():
    idx+=1; rot=180 if top else 0
    fps[u]=bd.fp('Package_SO','SSOP-24_3.9x8.7mm_P0.635mm',u,'MBI5153GP-A',x,y,rot,DRV_F)
    fps['J'+u]=colgrid('JC%d'%idx,x,y,rot)
    fps['RX'+u]=bd.fp('Resistor_SMD','R_0603_1608Metric','R%d'%idx,'1.5k 1%',*T(u,2.5,-8.325),rot+90,{'LCSC':'C22843','MPN':'0603WAF1501T5E'})
    fps['C1'+u]=bd.fp('Capacitor_SMD','C_0603_1608Metric','C%d'%idx,'100nF',*T(u,0,-5.6),rot,{'LCSC':'C66501','MPN':'CL10B104KO8NNNC'})
    fps['C2'+u]=bd.fp('Capacitor_SMD','C_0805_2012Metric','C%d'%(idx+4),'10uF',*T(u,0,-12),rot,{'LCSC':'C17024','MPN':'CL21A106KPFNNNE'})
J1=bd.fp('Connector_IDC','IDC-Header_2x08_P2.54mm_Vertical','J1','TILE_IN 2x8',8,125,90,{'LCSC':'C3406','MPN':'2.54-2*8P box header'})
for i,(x,y) in enumerate([(5,5),(245,5),(5,245),(245,245)]):
    bd.fp('MountingHole','MountingHole_3.2mm_M3','H%d'%(i+1),'M3',x,y)
lugs=[bd.fp('MountingHole','MountingHole_4.3mm_M4_Pad_Via','H%d'%(i+5),'GND_LUG_M4',x,y) for i,(x,y) in enumerate([(125,110),(125,140)])]
for l in lugs:
    for p in l.Pads(): p.SetNet(bd.net('GND'))
# buffers
BUF=[('U5','SIN',6.0),('U6','DCLK',12.0),('U7','LE',18.0),('U8','GCLK',24.0)]
for i,(u,n,x) in enumerate(BUF):
    fps[u]=bd.fp('Package_TO_SOT_SMD','SOT-23-5',u,'SN74AHCT1G125DBVR',x,114.5,0,{'LCSC':'C7484','MPN':'SN74AHCT1G125DBVR'})
    fps['RP'+u]=bd.fp('Resistor_SMD','R_0603_1608Metric','R%d'%(10+i),'10k',x-1.6,118.6,90,{'LCSC':'C98220','MPN':'RC0603FR-0710KL'})
    fps['RS'+u]=bd.fp('Resistor_SMD','R_0603_1608Metric','R%d'%(20+i),'33R',x+2.6,118.0,90,{'LCSC':'C23140','MPN':'0603WAF330JT5E'})
    fps['CB'+u]=bd.fp('Capacitor_SMD','C_0603_1608Metric','C%d'%(10+i),'100nF',x+0.2,111.9,0,{'LCSC':'C66501','MPN':'CL10B104KO8NNNC'})
RSDO=bd.fp('Resistor_SMD','R_0603_1608Metric','R30','33R',18.16,129.6,90,{'LCSC':'C23140','MPN':'0603WAF330JT5E'})
CBULK=[bd.fp('Capacitor_SMD','C_0805_2012Metric','C%d'%(20+i),'47uF',x,y,0,{'LCSC':'C16780','MPN':'CL21A476MQYNNNE'}) for i,(x,y) in enumerate([(38,114.5),(38,135.5)])]
# ---------- nets ----------
CHAIN={'U1':('SIN_B','S12'),'U2':('S12','S24'),'U4':('S24','S43'),'U3':('S43','SDO_L')}
for u in Q:
    f=fps[u]; sin,sdo=CHAIN[u]; i=list(Q).index(u)+1
    for pin,net in [(1,'GND'),(2,sin),(3,'DCLK_B'),(4,'LE_B'),(21,'GCLK_B'),(22,sdo),(23,'REXT%d'%i),(24,'+5V')]: bd.setnet(f,pin,net)
    for pin,out,*_ in MAP:
        n='COL%d_%02d'%(i,out); bd.setnet(f,pin,n); bd.setnet(fps['J'+u],out+1,n)
    rx=fps['RX'+u]; c1=fps['C1'+u]; c2=fps['C2'+u]
# resistor/cap pad nets chosen by proximity in local frame
def nearest_pad(f,pt):
    return min(f.Pads(),key=lambda p:(p.GetPosition().x/MM-pt[0])**2+(p.GetPosition().y/MM-pt[1])**2)
for u in Q:
    i=list(Q).index(u)+1
    rx=fps['RX'+u]; pa=nearest_pad(rx,T(u,2.5,-7.5)); pa.SetNet(bd.net('REXT%d'%i))
    [p.SetNet(bd.net('GND')) for p in rx.Pads() if p.GetNumber()!=pa.GetNumber()]
    for c in (fps['C1'+u],fps['C2'+u]):
        pv=nearest_pad(c,T(u,1,-8)); pv.SetNet(bd.net('+5V')); [p.SetNet(bd.net('GND')) for p in c.Pads() if p.GetNumber()!=pv.GetNumber()]
J1NET={2:'SIN_IN',4:'DCLK_IN',6:'LE_IN',8:'GCLK_IN',9:'SDO_RET',12:'+5V',14:'+5V'}
for p in J1.Pads(): p.SetNet(bd.net(J1NET.get(int(p.GetNumber()),'GND')))
for u,n,x in BUF:
    f=fps[u]
    for pin,net in [(1,'GND'),(2,n+'_IN'),(3,'GND'),(4,n+'_Y'),(5,'+5V')]: bd.setnet(f,pin,net)
    rp=fps['RP'+u]; pa=nearest_pad(rp,(x-1.6,120)); pa.SetNet(bd.net(n+'_IN')); [p.SetNet(bd.net('GND')) for p in rp.Pads() if p.GetNumber()!=pa.GetNumber()]
    rs=fps['RS'+u]; pa=nearest_pad(rs,(x+2.6,117)); pa.SetNet(bd.net(n+'_Y'))
    [p.SetNet(bd.net('SIN_B' if n=='SIN' else n+'_B')) for p in rs.Pads() if p.GetNumber()!=pa.GetNumber()]
    cb=fps['CB'+u]; pa=nearest_pad(cb,(x+2,111.9)); pa.SetNet(bd.net('+5V')); [p.SetNet(bd.net('GND')) for p in cb.Pads() if p.GetNumber()!=pa.GetNumber()]
pa=nearest_pad(RSDO,(18.16,126)); pa.SetNet(bd.net('SDO_RET')); [p.SetNet(bd.net('SDO_L')) for p in RSDO.Pads() if p.GetNumber()!=pa.GetNumber()]
for c in CBULK:
    ps=sorted(c.Pads(),key=lambda p:p.GetPosition().x); ps[0].SetNet(bd.net('GND')); ps[1].SetNet(bd.net('+5V'))
# ---------- planned routing per driver ----------
LINE_TOP={'S24':118,'S12':119,'SIN_B':120,'GCLK_B':121,'LE_B':122,'DCLK_B':123,'+5V':124}
LINE_BOT={'+5V':126,'DCLK_B':127,'LE_B':128,'GCLK_B':129,'S43':130,'S24':131,'SDO_L':132}
PADY={i+1:-3.493+0.635*i if i<12 else None for i in range(12)}
for i in range(12): PADY[24-i]=-3.493+0.635*i
lane_end={}   # (u,net) -> board x of lane via in band
def lp(u,pts,w,layer,net,r=1.0): bd.path([T(u,*p) for p in pts],w,layer,net,r)
def lv(u,p,net): x,y=T(u,*p); bd.via(x,y,net)
for u,(qx,qy,top) in Q.items():
    sin,sdo=CHAIN[u]; i=list(Q).index(u)+1
    lines=LINE_TOP if top else LINE_BOT
    def lyl(net): y=lines[net]; return (qy-y) if top else (y-qy)
    # GND pin1
    lp(u,[(-2.6,PADY[1]),(-3.8,PADY[1]),(-3.8,-5.6)],W_SIG,F,'GND',0.4); lv(u,(-3.8,-5.6),'GND')
    # SIN/DCLK/LE lanes
    for pin,net,lx in [(2,sin,-4.4),(3,'DCLK_B',-5.0),(4,'LE_B',-5.6),(22,sdo,5.0),(21,'GCLK_B',5.6)]:
        lp(u,[(math.copysign(2.6,lx),PADY[pin]),(lx,PADY[pin]),(lx,-53.5)],W_SIG,F,net,0.4); lv(u,(lx,-53.5),net)
        lp(u,[(lx,-53.5),(lx,lyl(net))],W_SIG,B,net); lv(u,(lx,lyl(net)),net); lane_end[(u,net)]=T(u,lx,0)[0]
    # VDD
    lp(u,[(2.6,PADY[24]),(3.8,PADY[24]),(3.8,-5.6)],W_SIG,F,'+5V',0.4); lv(u,(3.8,-5.6),'+5V')
    lp(u,[(3.8,-5.6),(3.8,lyl('+5V'))],0.4,B,'+5V'); lv(u,(3.8,lyl('+5V')),'+5V'); lane_end[(u,'+5V')]=T(u,3.8,0)[0]
    # REXT
    lp(u,[(2.6,PADY[23]),(4.4,PADY[23]),(4.4,-6.6),(2.5,-6.6),(2.5,-7.5)],W_SIG,F,'REXT%d'%i,0.4)
    lp(u,[(2.5,-9.15),(2.5,-10.2)],W_SIG,F,'GND'); lv(u,(2.5,-10.2),'GND')
    # decoupling
    lp(u,[(-0.825,-5.6),(-3.8,-5.6)],W_SIG,F,'GND'); lp(u,[(0.825,-5.6),(3.8,-5.6)],W_SIG,F,'+5V')
    lp(u,[(-0.95,-12),(-2.6,-12)],0.4,F,'GND'); lv(u,(-2.6,-12),'GND'); lp(u,[(0.95,-12),(3.8,-12)],0.4,F,'+5V'); lv(u,(3.8,-12),'+5V')
    # outputs
    for pin,out,hx,hy,layer,cx in MAP:
        n='COL%d_%02d'%(i,out); py=PADY[pin]; s=math.copysign(1,cx)
        if layer=='F':
            lp(u,[(s*2.6,py),(cx,py),(cx,hy),(hx,hy)],W_OUT,F,n,3.0)
        else:
            lp(u,[(s*2.6,py),(s*4.0,py)],W_OUT,F,n); lv(u,(s*4.0,py),n)
            lp(u,[(s*4.0,py),(cx,py),(cx,hy),(hx,hy)],W_OUT,B,n,3.0)
# ---------- bus band lines (F) ----------
def hline(net,y,xa,xb,w=0.3):
    bd.seg((min(xa,xb),y),(max(xa,xb),y),w,F,net)
LEFT={'+5V':30,'DCLK_B':31,'LE_B':32,'GCLK_B':33,'SIN_B':34}
for net,y in LINE_TOP.items():
    xs=[lane_end[(u,net)] for u in ('U1','U2') if (u,net) in lane_end]
    if net in LEFT: xs.append(LEFT[net])
    if net=='S24': xs.append(246)
    hline(net,y,min(xs),max(xs),0.5 if net=='+5V' else 0.3)
for net,y in LINE_BOT.items():
    xs=[lane_end[(u,net)] for u in ('U3','U4') if (u,net) in lane_end]
    if net in LEFT: xs.append(LEFT[net])
    if net=='S24': xs.append(246)
    if net=='SDO_L': xs.append(18.16)
    hline(net,y,min(xs),max(xs),0.5 if net=='+5V' else 0.3)
for net,x in LEFT.items():
    if net=='SIN_B': bd.via(x,LINE_TOP[net],net); continue
    bd.via(x,LINE_TOP[net],net); bd.via(x,LINE_BOT[net],net); bd.seg((x,LINE_TOP[net]),(x,LINE_BOT[net]),0.5 if net=='+5V' else 0.3,B,net)
bd.via(246,118,'S24'); bd.via(246,131,'S24'); bd.seg((246,118),(246,131),0.3,B,'S24')
# SDO return
bd.path([(18.16,132),(18.16,130.425)],W_SIG,F,'SDO_L'); bd.path([(18.16,128.775),(18.16,125)],W_SIG,F,'SDO_RET')
# ---------- A* for the input/buffer cluster ----------
GX0,GY0,GX1,GY1=0.6,104,60,136.5
g=Grid(GX0,GY0,GX1,GY1,0.1)
CL=0.2+W_SIG/2+0.03
def rasterize(skipnet=None):
    for t in b.GetTracks():
        n=t.GetNetname()
        if t.GetClass()=='PCB_VIA':
            p=t.GetPosition(); r=t.GetWidth(F)/2/MM+CL
            for l in (0,1): g.block_circle(l,p.x/MM,p.y/MM,r,n)
        else:
            l=0 if t.GetLayer()==F else 1; a=t.GetStart(); e=t.GetEnd()
            g.block_seg(l,(a.x/MM,a.y/MM),(e.x/MM,e.y/MM),t.GetWidth()/2/MM+CL,n)
    for f in b.GetFootprints():
        for p in f.Pads():
            n=p.GetNetname(); pos=p.GetPosition(); bb=p.GetBoundingBox()
            ls=[0,1] if p.GetAttribute()==pcbnew.PAD_ATTRIB_PTH or p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH else ([0] if p.IsOnLayer(F) else [1])
            for l in ls:
                g.block_rect(l,bb.GetX()/MM-CL,bb.GetY()/MM-CL,bb.GetRight()/MM+CL,bb.GetBottom()/MM+CL,n)
    # board edge + hole keepouts
rasterize()
g.viamask=[[None if (g.occ[0][j][i] in (None,) and g.occ[1][j][i] is None) else '#' for i in range(g.nx)] for j in range(g.ny)]
def padpts(f,num):
    p=bd.pad(f,num); x,y=p.GetPosition().x/MM,p.GetPosition().y/MM
    ls=[0,1] if p.GetAttribute()==pcbnew.PAD_ATTRIB_PTH else [0]
    return [(x,y,l) for l in ls]
fails=[]
def commit(net,res):
    segs,vias=res
    for l,pts in segs:
        bd.path(pts,W_SIG,F if l==0 else B,net,0.3)
        for a,c in zip(pts,pts[1:]): g.block_seg(l,a,c,W_SIG/2+CL,net)
    for (x,y) in vias:
        bd.via(x,y,net)
        for l in (0,1): g.block_circle(l,x,y,0.3+CL,net)
    # vias cannot be placed close to new copper
    for l,pts in segs:
        for a,c in zip(pts,pts[1:]):
            n_=int(math.hypot(c[0]-a[0],c[1]-a[1])/0.05)+1
            for k in range(n_+1):
                x=a[0]+(c[0]-a[0])*k/n_; y=a[1]+(c[1]-a[1])*k/n_
                rr=0.3+W_SIG/2+0.2
                ia,ja=g.ij(x-rr,y-rr); ib,jb=g.ij(x+rr,y+rr)
                for j in range(max(0,ja),min(g.ny,jb+1)):
                    for i in range(max(0,ia),min(g.nx,ib+1)):
                        px,py=g.xy(i,j)
                        if (px-x)**2+(py-y)**2<=rr*rr and g.viamask[j][i]!=net: g.viamask[j][i]='#' if g.viamask[j][i] not in (None,net) else net
def connect(net,srcs,dsts,layers=(0,1)):
    res=g.route(srcs,dsts,net,layers)
    if res is None: fails.append((net,srcs[0][:2])); return False
    commit(net,res); return True
jobs=[]
for u,n,x in BUF:
    f=fps[u]; jpin={'SIN':2,'DCLK':4,'LE':6,'GCLK':8}[n]
    jobs.append((n+'_IN',padpts(J1,jpin),padpts(f,2)))
    rp=fps['RP'+u]; pa=[p for p in rp.Pads() if p.GetNetname()==n+'_IN'][0]
    jobs.append((n+'_IN',[(pa.GetPosition().x/MM,pa.GetPosition().y/MM,0)],padpts(f,2)))
    rs=fps['RS'+u]; pa=[p for p in rs.Pads() if p.GetNetname()==n+'_Y'][0]; pb=[p for p in rs.Pads() if p.GetNumber()!=pa.GetNumber()][0]
    jobs.append((n+'_Y',padpts(f,4),[(pa.GetPosition().x/MM,pa.GetPosition().y/MM,0)]))
    tgt=LEFT['SIN_B' if n=='SIN' else n+'_B']; ln='SIN_B' if n=='SIN' else n+'_B'
    jobs.append((ln,[(pb.GetPosition().x/MM,pb.GetPosition().y/MM,0)],[(tgt,LINE_TOP[ln],0),(tgt,LINE_TOP[ln],1)]))
for u,n,x in BUF:
    f=fps[u]; cb=fps['CB'+u]; pv=[p for p in cb.Pads() if p.GetNetname()=='+5V'][0]
    jobs.append(('+5V',padpts(f,5),[(pv.GetPosition().x/MM,pv.GetPosition().y/MM,0)]))
jobs.sort(key=lambda j: 0 if j[0].endswith('_IN') else (1 if j[0].endswith('_Y') else 2))
for net,s,d in jobs: connect(net,s,d)
# +5V cluster: J1.12 -> +5V left via, buffers VCC -> nearest +5V copper
connect('+5V',padpts(J1,12),[(30,124,0),(30,124,1)])
for c in CBULK:
    pv=[p for p in c.Pads() if p.GetNetname()=='+5V'][0]
    connect('+5V',[(pv.GetPosition().x/MM,pv.GetPosition().y/MM,0)],[(30,124,0),(30,124,1),(30,126,0),(30,126,1)])
for u,n,x in BUF:
    f=fps[u]
    connect('+5V',padpts(f,5),[(30,124,0),(30,124,1)]+padpts(J1,12)+padpts(J1,14))
# ---------- GND zones ----------
def zone(layer):
    z=pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(bd.net('GND'))
    o=z.Outline(); o.NewOutline()
    for x,y in [(0.5,0.5),(249.5,0.5),(249.5,249.5),(0.5,249.5)]: o.Append(int(x*MM),int(y*MM))
    z.SetLocalClearance(int(0.3*MM)); z.SetMinThickness(int(0.25*MM)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(int(0.3*MM)); z.SetThermalReliefSpokeWidth(int(0.4*MM)); b.Add(z)
zone(F); zone(B)
json.dump({'fails':fails},open(os.path.join(HERE,'route_report.json'),'w'),indent=1)
out=os.path.join(HERE,'tile_v1.kicad_pcb'); bd.save(out)
print('saved',out,'fails',fails)
