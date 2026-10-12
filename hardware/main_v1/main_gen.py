#!/usr/bin/env python3
"""Main (brain) board v1.1: ESP32-S3 + 24x 74LVC245 line drivers -> 8 branch ports (IDC 2x20).
12 V input (shared with branch distribution) -> PTC + SS34 reverse-polarity + SMBJ15A TVS -> AP63203 buck 3.3 V.
Structured 'spine' routing (deterministic, arc-filleted) for the 23-bit bus; A* only in the MCU/power corner.
Run: ../../kpy.sh $PWD/main_gen.py"""
import sys, os, math, json, time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,'../../tools'))
import pcbnew
from pcbkit import Board, V, MM
from router import Router
F,B=pcbnew.F_Cu,pcbnew.B_Cu
bd=Board(); b=bd.b
W=300.0; H=130.0
ds=b.GetDesignSettings()
ds.m_MinClearance=int(0.127*MM); ds.m_TrackMinWidth=int(0.15*MM); ds.m_ViasMinSize=int(0.45*MM); ds.m_MinThroughDrill=int(0.2*MM)
ds.m_CopperEdgeClearance=int(0.3*MM); ds.m_HoleToHoleMin=int(0.25*MM)
ds.SetBoardThickness(int(1.6*MM))
nc=ds.m_NetSettings.GetDefaultNetclass(); nc.SetClearance(int(0.15*MM)); nc.SetTrackWidth(int(0.2*MM)); nc.SetViaDiameter(int(0.5*MM)); nc.SetViaDrill(int(0.3*MM))
def eline(a,c):
    s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(int(0.1*MM)); b.Add(s)
def earc(a,m,c):
    s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetArcGeometry(V(*a),V(*m),V(*c)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(int(0.1*MM)); b.Add(s)
R=4.0; k_=R*(1-1/math.sqrt(2))
eline((R,0),(W-R,0)); earc((W-R,0),(W-k_,k_),(W,R)); eline((W,R),(W,H-R)); earc((W,H-R),(W-k_,H-k_),(W-R,H))
eline((W-R,H),(R,H)); earc((R,H),(k_,H-k_),(0,H-R)); eline((0,H-R),(0,R)); earc((0,R),(k_,k_),(R,0))
def lc(c,m): return {'LCSC':c,'MPN':m}
def two(f,a,bn):
    ps=sorted(f.Pads(),key=lambda q:q.GetNumber()); ps[0].SetNet(bd.net(a)); ps[1].SetNet(bd.net(bn))
CAPS={'100nF':('C66501','CL10B104KO8NNNC','0603'),'1uF':('C1592','CL10A105KO8NNNC','0603'),'22uF':('C59461','CL10A226MQ8NRNC','0603'),
      '10uF50V':('C13585','CL31A106KBHNNNE','1206'),'47uF':('C77101','GRM32ER61C476KE15L','1210')}
MET={'0603':'1608','0805':'2012','1206':'3216','1210':'3225'}
def C(ref,val,x,y,rot=0):
    c,m,sz=CAPS[val]; return bd.fp('Capacitor_SMD','C_%s_%sMetric'%(sz,MET[sz]),ref,val,x,y,rot,lc(c,m))
RES={'10k':('C98220','RC0603FR-0710KL'),'5.1k':('C23186','0603WAF5101T5E'),'1k':('C21190','0603WAF1001T5E')}
def Rr(ref,val,x,y,rot=0): return bd.fp('Resistor_SMD','R_0603_1608Metric',ref,val,x,y,rot,lc(*RES[val]))
# ---------------- MCU + power corner ----------------
U1=bd.fp('RF_Module','ESP32-S3-WROOM-1','U1','ESP32-S3-WROOM-1-N16R8',30,65,90,lc('C2913202','ESP32-S3-WROOM-1-N16R8'))
J10=bd.fp('TerminalBlock_Phoenix','TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal','J10','12V_IN',13,119,0,lc('C8465','WJ500V-5.08-2P'))
F1=bd.fp('Fuse','Fuse_1812_4532Metric','F1','PTC 2A/16V',20,106,90,lc('C20812','SMD1812P200TF16'))
D3=bd.fp('Diode_SMD','D_SMA','D3','SS34 (rev.pol.)',22,96,0,lc('C8678','SS34'))
D4=bd.fp('Diode_SMD','D_SMB','D4','SMBJ15A',10,104,90,lc('C83846','SMBJ15A'))
U2=bd.fp('Package_TO_SOT_SMD','TSOT-23-6','U2','AP63203WU-7',36,100,0,lc('C780769','AP63203WU-7'))
L1=bd.fp('cube','L_Cjiang_FXL0630','L1','3.3uH',41,106,0,lc('C167219','FXL0630-3R3-M'))
C1=C('C1','10uF50V',30,92,0); C2=C('C2','100nF',31,100,90); C7=C('C7','100nF',39.2,99.5,90)   # C7 = BST
C3=C('C3','22uF',46,92,0); C4=C('C4','22uF',46,112,90); C5=C('C5','100nF',42,82,0); C8=C('C8','47uF',39,88,0)
J9=bd.fp('Connector_USB','USB_C_Receptacle_HRO_TYPE-C-31-M-12','J9','USB-C',32,125.5,0,lc('C165948','TYPE-C-31-M-12'))
D1=bd.fp('Diode_SMD','D_SMA','D1','SS34',27,112,0,lc('C8678','SS34'))
U3=bd.fp('Package_TO_SOT_SMD','SOT-23-6','U3','USBLC6-2SC6',44,118,0,lc('C2827654','USBLC6-2SC6'))
R2=Rr('R2','5.1k',24,120,90); R3=Rr('R3','5.1k',40,124,90)
SW1=bd.fp('Button_Switch_SMD','SW_Push_1P1T_XKB_TS-1187A','SW1','BOOT',44,44,0,lc('C318884','TS-1187A-B-A-B'))
SW2=bd.fp('Button_Switch_SMD','SW_Push_1P1T_XKB_TS-1187A','SW2','RESET',12,94,0,lc('C318884','TS-1187A-B-A-B'))
R1=Rr('R1','10k',26,86,90); C6=C('C6','1uF',30,86,90)
R4=Rr('R4','10k',44,36,0); R5=Rr('R5','1k',30,40,0)
LED1=bd.fp('LED_SMD','LED_0603_1608Metric','D2','STATUS',30,36,0,lc('C2286','KT-0603R'))
for i,(x,y) in enumerate([(4,4),(W-4,4),(4,H-4),(W-4,H-4),(153.5,42)]):
    h=bd.fp('MountingHole','MountingHole_3.2mm_M3','H%d'%(i+1),'M3',x,y); h.SetBoardOnly(True); h.SetExcludedFromBOM(True); h.SetExcludedFromPosFiles(True)
for i,(x,y) in enumerate([(12,4),(W-5,14),(W-5,H-14)]):
    h=bd.fp('Fiducial','Fiducial_1mm_Mask2mm','FID%d'%(i+1),'FID',x,y); h.SetBoardOnly(True); h.SetExcludedFromBOM(True)
# ---------------- nets: MCU/power ----------------
def setn(f,num,net): bd.setnet(f,num,net)
for p in U1.Pads():
    if p.GetNumber() in ('1','40','41'): p.SetNet(bd.net('GND'))
setn(U1,2,'+3V3'); setn(U1,3,'EN'); setn(U1,13,'USB_DN'); setn(U1,14,'USB_DP'); setn(U1,27,'IO0')
setn(J10,1,'VIN12'); setn(J10,2,'GND')
two(F1,'VIN12','V12F')                  # PTC
two(D3,'VIN','V12F')                    # SMA pad1=cathode -> VIN, anode=V12F (reverse polarity)
two(D4,'V12F','GND')                    # SMB pad1=cathode on +, anode GND
setn(U2,1,'+3V3'); setn(U2,2,'VIN'); setn(U2,3,'VIN'); setn(U2,4,'GND'); setn(U2,5,'SW'); setn(U2,6,'BST')
two(L1,'SW','+3V3'); two(C1,'VIN','GND'); two(C2,'VIN','GND')
for q in C7.Pads(): q.SetNet(bd.net('BST' if q.GetPosition().y<V(0,99.5).y else 'SW'))
two(C3,'+3V3','GND'); two(C4,'+3V3','GND'); two(C5,'+3V3','GND'); two(C8,'+3V3','GND')
for p in J9.Pads():
    m={'A4':'VBUS','B4':'VBUS','A9':'VBUS','B9':'VBUS','A6':'USB_DP','B6':'USB_DP','A7':'USB_DN','B7':'USB_DN','A5':'CC1','B5':'CC2'}
    p.SetNet(bd.net(m.get(p.GetNumber(),'GND')))
two(D1,'VIN','VBUS')
for p in J9.Pads():
    if p.GetNetname()=='GND': p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
# USBLC6-2SC6: 1 IO1, 2 GND, 3 IO2, 4 IO2, 5 VBUS, 6 IO1
setn(U3,1,'USB_DP'); setn(U3,6,'USB_DP'); setn(U3,3,'USB_DN'); setn(U3,4,'USB_DN'); setn(U3,2,'GND'); setn(U3,5,'VBUS')
two(R2,'CC1','GND'); two(R3,'CC2','GND')
two(R1,'EN','+3V3'); two(C6,'EN','GND'); two(R4,'OE_N','+3V3'); two(R5,'LED','LED_K'); two(LED1,'GND','LED_K')
for sw,net in ((SW1,'IO0'),(SW2,'EN')):
    for p in sw.Pads(): p.SetNet(bd.net(net if p.GetNumber()=='1' else 'GND'))
# ---------------- bus definition ----------------
BUS=['D%d'%i for i in range(16)]+['CLK','A0','A1','A2','A3','A4','A5']
LY0=54.0; LP=1.0
def LY(sig): return LY0+LP*BUS.index(sig)
# ESP pin -> line mapping (geometric: top-row pins -> upper lines, right column -> middle, bottom row -> lower)
TOPPINS=[39,38,35,34,33,32,31]          # leftmost first -> line 0..6
RIGHTPINS=[25,24,23,22,21,20,19,18,17]  # top first -> line 7..15
BOTPINS=[12,11,10,9,8,7,6]              # rightmost first -> line 16..22
ESPMAP={}
for i,pn in enumerate(TOPPINS+RIGHTPINS+BOTPINS): ESPMAP[BUS[i]]=pn
ESPMAP['OE_N']=5; ESPMAP['LED']=4
for net,pin in ESPMAP.items(): setn(U1,pin,net)
def portpin(sig):
    if sig.startswith('D'): return 1+2*int(sig[1:])
    return {'CLK':33,'A0':35,'A1':37,'A2':39,'A3':34,'A4':36,'A5':38}[sig]
GROUPS=[BUS[0:8],BUS[8:16],['CLK','A3','A0','A4','A1','A5','A2',None]]
GOFF=[8.89,29.21,44.45]
TOPX=[58,118,178,238]
OE_T,V3_T=29.8,31.5; OE_Bo,V3_Bo=100.2,98.5
XL=46.0; XR=288.0
ports=[]; caps=[]
for p in range(8):
    top=p<4; X0=TOPX[p%4]
    if top: J=bd.fp('Connector_IDC','IDC-Header_2x20_P2.54mm_Vertical','J%d'%(p+1),'PORT%d'%p,X0,9.5,90,lc('C9138','2.54-2*20P box header'))
    else:   J=bd.fp('Connector_IDC','IDC-Header_2x20_P2.54mm_Vertical','J%d'%(p+1),'PORT%d'%p,X0-2.5+48.26,H-9.5,270,lc('C9138','2.54-2*20P box header'))
    x1=bd.padxy(J,1)[0]; sgn=1 if top else -1
    bufs=[]
    for g in range(3):
        cx=x1+sgn*GOFF[g]; cy=24 if top else H-24
        u=bd.fp('Package_SO','TSSOP-20_4.4x6.5mm_P0.65mm','U%d'%(10+3*p+g),'74LVC245APW',cx,cy,90 if top else 270,lc('C6082','74LVC245APW,118'))
        cc=C('C%d'%(10+3*p+g),'100nF',cx-sgn*5.6,cy,0)
        bufs.append((u,cc,cx,cy))
    ports.append((J,bufs,top))
# ---- TPD4E05U06 ESD on every ribbon port (B.Cu, next to the header pins) ----
ESDGROUPS=[[1,3,5,7],[9,11,13,15],[17,19,21,23],[25,27,29,31],[33,35,37,39],[34,36,38]]
def esd_place(ref,cx,cy,face_minus_y):
    for rot in (0,90,180,270):
        u=bd.fp('Package_SON','USON-10_2.5x1.0mm_P0.5mm',ref,'TPD4E05U06DQAR',cx,cy,rot,lc('C138714','TPD4E05U06DQAR')); u.Flip(u.GetPosition(),False)
        p1=bd.padxy(u,1); p10=bd.padxy(u,10); p5=bd.padxy(u,5)
        if abs(p1[1]-p10[1])>0.5 and ((p1[1]<p10[1])==face_minus_y): return u
        b.Remove(u)
    raise RuntimeError('esd orient')
esds=[]
for p,(J,bufs,top) in enumerate(ports):
    pass
for p,(J,bufs,top) in enumerate(ports):
    for pad in J.Pads(): pad.SetNet(bd.net('GND'))
    for g,(u,cc,cx,cy) in zip(GROUPS,bufs):
        setn(u,1,'+3V3'); setn(u,10,'GND'); setn(u,19,'OE_N'); setn(u,20,'+3V3')
        for k,sig in enumerate(g):
            if sig is None: setn(u,2+k,'GND'); continue
            setn(u,2+k,sig); on='P%d_%s'%(p,sig); setn(u,18-k,on); setn(J,portpin(sig),on)
        near1=abs(bd.padxy(cc,1)[0]-cx)<abs(bd.padxy(cc,2)[0]-cx)
        two(cc,'+3V3','GND') if near1 else two(cc,'GND','+3V3')
    s_=1 if top else -1; oy=bd.padxy(J,1)[1]; ey=bd.padxy(J,2)[1]
    for gi,grp in enumerate(ESDGROUPS):
        xs=[bd.padxy(J,n)[0] for n in grp]; cx=sum(xs)/len(xs)
        even=grp[0]%2==0
        cy=(ey-s_*2.96) if even else (oy+s_*4.5)
        u=esd_place('UE%d'%(10*p+gi),cx,cy,face_minus_y=(top if not even else not top))
        io=sorted([bd.pad(u,n) for n in (1,2,4,5)],key=lambda q:q.GetPosition().x)
        for q in (3,8): bd.setnet(u,q,'GND')
        gx=sorted(grp,key=lambda n:bd.padxy(J,n)[0])
        for n,q in zip(gx,io):
            q.SetNet(bd.pad(J,n).GetNet())
        esds.append((u,J,grp,even,s_,[(n,q) for n,q in zip(gx,io)]))
# ---------------- structured routing ----------------
def path(pts,net,w=0.2,layer=F,r=0.6): bd.path(pts,w,layer,net,r)
VD,VDR=0.5,0.3
for p,(J,bufs,top) in enumerate(ports):
    s=1 if top else -1          # +1: connector is at smaller y
    for g,(u,cc,cx,cy) in zip(GROUPS,bufs):
        # --- outputs: staircase fan-out ---
        items=[]
        for k,sig in enumerate(g):
            if sig is None: continue
            bx,by=bd.padxy(u,18-k); pn=portpin(sig); jx,jy=bd.padxy(J,pn)
            if pn%2==1: items.append((bx,by,jx,jy,None,sig))
            else:
                ox,oy=bd.padxy(J,pn-1)       # odd pad in same column
                items.append((bx,by,ox+(1.27 if top else -1.27),oy,(jx,jy),sig))
        R_=sorted([it for it in items if it[2]>=it[0]],key=lambda t:t[0]); L_=sorted([it for it in items if it[2]<it[0]],key=lambda t:-t[0])
        for grp in (R_,L_):
            n=len(grp)
            for i,(bx,by,tx,ty,ev,sig) in enumerate(grp):
                rank=n-1-i; yl=by-s*(1.3+0.6*rank); net='P%d_%s'%(p,sig)
                if ev is None: path([(bx,by),(bx,yl),(tx,yl),(tx,ty)],net)
                else:
                    yv=ty+s*0.9
                    path([(bx,by),(bx,yl),(tx,yl),(tx,yv)],net); bd.via(tx,yv,net,VD,VDR)
                    ymid=ty-s*1.27
                    path([(tx,yv),(tx,ymid),(ev[0],ymid),(ev[0],ev[1])],net,0.2,B,0.4)
        # --- inputs: straight to spine line ---
        for k,sig in enumerate(g):
            ax,ay=bd.padxy(u,2+k)
            if sig is None:
                gx,gy=bd.padxy(u,10); path([(ax,ay),(ax,ay+s*0.9),(gx,ay+s*0.9),(gx,gy)],'GND',0.25); continue
            y=LY(sig); path([(ax,ay),(ax,y)],sig); bd.via(ax,y,sig,VD,VDR)
        # --- power / OE ---
        p20=bd.padxy(u,20); p1=bd.padxy(u,1); p19=bd.padxy(u,19); p10=bd.padxy(u,10)
        xo=cx-s*4.2; v3y=V3_T if top else V3_Bo; oey=OE_T if top else OE_Bo
        path([p20,(xo,p20[1]),(xo,v3y)],'+3V3',0.3); bd.via(xo,v3y,'+3V3',0.6,0.3)
        path([p1,(xo,p1[1])],'+3V3',0.3)
        cpad=[q for q in cc.Pads() if q.GetNetname()=='+3V3'][0]; cgp=[q for q in cc.Pads() if q.GetNetname()=='GND'][0]
        cxp=cpad.GetPosition().x/MM; cyp=cpad.GetPosition().y/MM; path([(cxp,cyp),(xo,cyp)],'+3V3',0.3)
        gxp=cgp.GetPosition().x/MM; path([(gxp,cyp),(gxp-s*1.0,cyp)],'GND',0.3); bd.via(gxp-s*1.0,cyp,'GND',VD,VDR)
        bcy=cy; path([p19,(p19[0],bcy)],'OE_N',0.25); bd.via(p19[0],bcy,'OE_N',VD,VDR); path([(p19[0],bcy),(p19[0],oey)],'OE_N',0.25,B)
        path([p10,(p10[0]+s*1.1,p10[1])],'GND',0.3); bd.via(p10[0]+s*1.1,p10[1],'GND',VD,VDR)
for u,J,grp,even,s_,pairs in esds:
    for n,q in pairs:
        jx,jy=bd.padxy(J,n); qx,qy=q.GetPosition().x/MM,q.GetPosition().y/MM; net=q.GetNetname()
        d=-s_ if even else s_            # direction from header pin toward ESD
        a1,b1=(0.9,0.5) if even else (1.8,1.0)
        path([(jx,jy),(jx,jy+d*a1),(qx,qy-d*b1),(qx,qy)],net,0.2,B,0.3)
    g3=bd.padxy(u,3); g8=bd.padxy(u,8); path([g3,g8],'GND',0.2,B)
def lastx(net,y,tol=0.05):
    xs=[t.GetPosition().x/MM for t in b.GetTracks() if t.GetClass()=='PCB_VIA' and t.GetNetname()==net and abs(t.GetPosition().y/MM-y)<tol]
    xs+=[e for t in b.GetTracks() if t.GetClass()!='PCB_VIA' and t.GetNetname()==net and t.GetLayer()==B for e in (t.GetStart().x/MM,t.GetEnd().x/MM) if abs(t.GetEnd().y/MM-y)<tol or abs(t.GetStart().y/MM-y)<tol]
    return max(xs)
for sig in BUS: path([(XL,LY(sig)),(lastx(sig,LY(sig)),LY(sig))],sig,0.2,B)
for y in (OE_T,OE_Bo): path([(XL,y),(lastx('OE_N',y),y)],'OE_N',0.3,B)
for y in (V3_T,V3_Bo): path([(XL,y),(lastx('+3V3',y)+0.3,y)],'+3V3',1.2,B)
print('structured done')
# ---------------- A* in MCU/power corner ----------------
rt=Router(bd,0,0,XL+8,H,step=0.25,w=0.3,clr=0.15)
bb=U1.GetBoundingBox(False); ax0=bb.GetX()/MM; ay0=bb.GetY()/MM; ay1=bb.GetBottom()/MM
ant=(0,41.0,23.4,89.0); rt.block_rect([0,1],*ant,None)
rt.block_rect([0,1],XL+1.5,0,XL+8,H,None)   # keep A* out of structured area
rt.load_board()
def pp(pad):
    x,y=pad.GetPosition().x/MM,pad.GetPosition().y/MM
    ls=[0,1] if pad.GetAttribute()==pcbnew.PAD_ATTRIB_PTH else ([0] if pad.IsOnLayer(F) else [1])
    return [(x,y,l) for l in ls]
def P(f,n): return pp(bd.pad(f,n))
def padsof(f,net): return [q for x in f.Pads() if x.GetNetname()==net for q in pp(x)]
fails=[]
def con(net,src,dst=None,to_net=False,w=None,**kw):
    ok=rt.connect(net,src,dst,to_net,w,**kw)
    if not ok: fails.append((net,src[0][:2] if src else None)); print('FAIL',net,flush=True)
    return ok
t0=time.time()
# bus: right column first, then top row, then bottom row (inner first)
orderpins=RIGHTPINS+TOPPINS[::-1]+BOTPINS
for pn in orderpins:
    sig=[s_ for s_,v in ESPMAP.items() if v==pn][0]
    con(sig,P(U1,pn),[(XL,LY(sig),1)])
print('bus',time.time()-t0,len(fails),flush=True)
con('OE_N',P(U1,5),[(XL,OE_Bo,1)]); con('OE_N',padsof(R4,'OE_N'),None,True); con('OE_N',[(XL,OE_T,1)],None,True)
con('LED',P(U1,4),padsof(R5,'LED')); con('LED_K',padsof(R5,'LED_K'),padsof(LED1,'LED_K'))
con('USB_DP',P(U1,14),padsof(U3,'USB_DP')); con('USB_DN',P(U1,13),padsof(U3,'USB_DN'))
con('USB_DP',padsof(J9,'USB_DP'),None,True); con('USB_DN',padsof(J9,'USB_DN'),None,True)
con('CC1',padsof(J9,'CC1'),padsof(R2,'CC1')); con('CC2',padsof(J9,'CC2'),padsof(R3,'CC2'))
for q in padsof(J9,'VBUS'): con('VBUS',[q],padsof(D1,'VBUS') if q is padsof(J9,'VBUS')[0] else None, q is not padsof(J9,'VBUS')[0], w=0.5)
con('VBUS',padsof(U3,'VBUS'),None,True)
con('EN',P(U1,3),padsof(R1,'EN')); con('EN',padsof(C6,'EN'),None,True); con('EN',padsof(SW2,'EN'),None,True)
con('IO0',P(U1,27),padsof(SW1,'IO0'))
# power
con('VIN12',padsof(J10,'VIN12'),padsof(F1,'VIN12'))
con('V12F',padsof(F1,'V12F'),padsof(D3,'V12F')); con('V12F',padsof(D4,'V12F'),None,True)
con('VIN',padsof(D3,'VIN'),padsof(C1,'VIN')); con('VIN',padsof(U2,'VIN'),None,True); con('VIN',padsof(C2,'VIN'),None,True); con('VIN',padsof(D1,'VIN'),None,True)
con('SW',padsof(U2,'SW'),padsof(L1,'SW')); con('BST',padsof(U2,'BST'),padsof(C7,'BST')); con('SW',padsof(C7,'SW'),None,True)
con('+3V3',padsof(L1,'+3V3'),padsof(C3,'+3V3'))
for f in (C4,U2,C8,C5): con('+3V3',padsof(f,'+3V3'),None,True)
con('+3V3',P(U1,2),None,True)
con('+3V3',[(XL,V3_T,1)],None,True); con('+3V3',[(XL,V3_Bo,1)],None,True)
for f in (R1,R4): con('+3V3',padsof(f,'+3V3'),None,True)
print('corner',time.time()-t0,len(fails),flush=True)
def gnd_via(pad):
    x,y=pad.GetPosition().x/MM,pad.GetPosition().y/MM
    lay=0 if pad.IsOnLayer(F) else 1
    for r in (0.9,1.2,1.6,2.0,2.6,3.2):
        for a in range(0,360,30):
            vx=x+r*math.cos(math.radians(a)); vy=y+r*math.sin(math.radians(a))
            i,j=rt.ij(vx,vy)
            if not(0<=i<rt.nx and 0<=j<rt.ny): continue
            c=rt.code('GND')
            if rt.Vg[j,i] not in (-1,c) or rt.T[1-lay][j,i] not in (-1,c): continue
            res=rt.route('GND',[(x,y,lay)],[(vx,vy,lay)],False,via_cost=10**6,maxit=3000)
            if res is None: continue
            vxy=rt.xy(i,j); rt.commit('GND',res,0.3,(x,y),vxy); bd.via(vxy[0],vxy[1],'GND',VD,VDR); rt.block_circle([0,1],vxy[0],vxy[1],VD/2,'GND'); return True
    fails.append(('GNDVIA',(round(x,2),round(y,2)))); return False
for f in b.GetFootprints():
    if f.GetPosition().x/MM>XL: continue
    for pad in f.Pads():
        if pad.GetNetname()=='GND' and pad.GetAttribute()==pcbnew.PAD_ATTRIB_SMD:
            if f is U1 and pad.GetNumber()=='41':
                px,py=pad.GetPosition().x/MM,pad.GetPosition().y/MM
                continue
            gnd_via(pad)
print('gnd',time.time()-t0,len(fails),flush=True)
# ---------------- zones + stitching ----------------
def zone(layer):
    z=pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(bd.net('GND')); o=z.Outline(); o.NewOutline()
    for x,y in [(0.3,0.3),(W-0.3,0.3),(W-0.3,H-0.3),(0.3,H-0.3)]: o.Append(int(x*MM),int(y*MM))
    z.SetLocalClearance(int(0.25*MM)); z.SetMinThickness(int(0.2*MM)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(int(0.25*MM)); z.SetThermalReliefSpokeWidth(int(0.35*MM)); b.Add(z)
zone(F); zone(B)

# stitching: coarse whole-board occupancy check
st=Router(bd,0,0,W,H,step=0.5,w=0.2,clr=0.3); st.block_rect([0,1],*ant,None); st.load_board()
nst=0
for x in [6+5*i for i in range(58)]:
    for y in [6+5*j for j in range(24)]:
        i,j=st.ij(x,y)
        ok=all(st.Vg[jj,ii]==-1 for jj in range(j-2,j+3) for ii in range(i-2,i+3) if 0<=jj<st.ny and 0<=ii<st.nx)
        if ok and all(st.T[l][j,i]==-1 for l in (0,1)): bd.via(x,y,'GND',0.6,0.3); nst+=1
print('stitch vias',nst)
json.dump({'fails':fails,'stitch':nst},open(os.path.join(HERE,'route_report.json'),'w'),indent=1)
bd.save(os.path.join(HERE,'main_v1.kicad_pcb')); print('saved; fails',len(fails),fails,'time',time.time()-t0)
