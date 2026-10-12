#!/usr/bin/env python3
"""Main (brain) board v1: ESP32-S3 + 24x 74LVC245 line drivers -> 8 branch ports (IDC 2x20).
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
ds.m_MinClearance=int(0.127*MM); ds.m_TrackMinWidth=int(0.15*MM); ds.m_ViasMinSize=int(0.45*MM); ds.m_MinThroughDrill=int(0.3*MM)
ds.m_CopperEdgeClearance=int(0.3*MM); ds.m_HoleToHoleMin=int(0.25*MM)
nc=ds.m_NetSettings.GetDefaultNetclass(); nc.SetClearance(int(0.15*MM)); nc.SetTrackWidth(int(0.2*MM)); nc.SetViaDiameter(int(0.5*MM)); nc.SetViaDrill(int(0.3*MM))
def eline(a,c):
    s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(int(0.1*MM)); b.Add(s)
def earc(a,m,c):
    s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetArcGeometry(V(*a),V(*m),V(*c)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(int(0.1*MM)); b.Add(s)
R=4.0; k=R*(1-1/math.sqrt(2))
eline((R,0),(W-R,0)); earc((W-R,0),(W-k,k),(W,R)); eline((W,R),(W,H-R)); earc((W,H-R),(W-k,H-k),(W-R,H))
eline((W-R,H),(R,H)); earc((R,H),(k,H-k),(0,H-R)); eline((0,H-R),(0,R)); earc((0,R),(k,k),(R,0))
# ---------------- parts ----------------
def lc(c,m): return {'LCSC':c,'MPN':m}
U1=bd.fp('RF_Module','ESP32-S3-WROOM-1','U1','ESP32-S3-WROOM-1-N16R8',22,62,90,lc('C2913202','ESP32-S3-WROOM-1-N16R8'))
U2=bd.fp('Package_TO_SOT_SMD','SOT-223-3_TabPin2','U2','AMS1117-3.3',22,104,0,lc('C6186','AMS1117-3.3'))
J10=bd.fp('TerminalBlock_Phoenix','TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal','J10','5V_IN',8,118,0,lc('C8465','WJ500V-5.08-2P'))
J9=bd.fp('Connector_USB','USB_C_Receptacle_HRO_TYPE-C-31-M-12','J9','USB-C',44,124,0,lc('C165948','TYPE-C-31-M-12'))
D1=bd.fp('Diode_SMD','D_SMA','D1','SS34',44,112,180,lc('C8678','SS34'))
SW1=bd.fp('Button_Switch_SMD','SW_Push_1P1T_XKB_TS-1187A','SW1','BOOT',8,30,0,lc('C318884','TS-1187A-B-A-B'))
SW2=bd.fp('Button_Switch_SMD','SW_Push_1P1T_XKB_TS-1187A','SW2','RESET',8,40,0,lc('C318884','TS-1187A-B-A-B'))
caps=[]
def C(ref,val,x,y,rot=0,size='0603'):
    code={'100nF':('C66501','CL10B104KO8NNNC'),'10uF':('C17024','CL21A106KPFNNNE'),'47uF':('C16780','CL21A476MQYNNNE'),'1uF':('C15849','CL10A105KB8NNNC')}[val]
    fp=bd.fp('Capacitor_SMD','C_%s_%sMetric'%(size,{'0603':'1608','0805':'2012'}[size]),ref,val,x,y,rot,lc(*code)); caps.append(fp); return fp
def Rr(ref,val,x,y,rot=0):
    code={'10k':('C98220','RC0603FR-0710KL'),'5.1k':('C23186','0603WAF5101T5E'),'1k':('C21190','0603WAF1001T5E')}[val]
    return bd.fp('Resistor_SMD','R_0603_1608Metric',ref,val,x,y,rot,lc(*code))
C1=C('C1','47uF',16,112,0,'0805'); C2=C('C2','10uF',28,112,0,'0805'); C3=C('C3','10uF',30,98,0,'0805'); C4=C('C4','47uF',30,94,0,'0805')
C5=C('C5','100nF',36,84,0); C6=C('C6','1uF',14,46,90)
R1=Rr('R1','10k',14,40,90); R2=Rr('R2','5.1k',38,118,90); R3=Rr('R3','5.1k',50,118,90); R4=Rr('R4','10k',40,30,0); R5=Rr('R5','1k',40,36,0)
LED1=bd.fp('LED_SMD','LED_0603_1608Metric','D2','STATUS',46,36,0,lc('C2286','KT-0603R'))
for i,(x,y) in enumerate([(4,4),(W-4,4),(4,H-4),(W-4,H-4),(150,65)]):
    bd.fp('MountingHole','MountingHole_3.2mm_M3','H%d'%(i+1),'M3',x,y)
# ports
PORTX=[62,122,182,242]
ports=[]
for p in range(8):
    top=p<4; x=PORTX[p%4]
    if top: J=bd.fp('Connector_IDC','IDC-Header_2x20_P2.54mm_Vertical','J%d'%(p+1),'PORT%d'%p,x,9.5,90,lc('C9138','2.54-2*20P box header'))
    else:   J=bd.fp('Connector_IDC','IDC-Header_2x20_P2.54mm_Vertical','J%d'%(p+1),'PORT%d'%p,x+48.26,H-9.5,270,lc('C9138','2.54-2*20P box header'))
    bufs=[]
    for k in range(3):
        bx=x+8+k*16; by=24 if top else H-24
        u=bd.fp('Package_SO','TSSOP-20_4.4x6.5mm_P0.65mm','U%d'%(10+3*p+k),'74LVC245APW',bx,by,90 if top else 270,lc('C6082','74LVC245APW,118'))
        cc=C('C%d'%(10+3*p+k),'100nF',bx,by+(6 if top else -6),0)
        bufs.append((u,cc))
    ports.append((J,bufs,top))
# ---------------- nets ----------------
def setn(f,num,net): bd.setnet(f,num,net)
BUS=['D%d'%i for i in range(16)]+['CLK','A0','A1','A2','A3','A4','A5']
ESPMAP={'D0':4,'D1':5,'D2':6,'D3':7,'D4':8,'D5':9,'D6':10,'D7':11,'D8':12,'D9':17,'D10':18,'D11':19,'D12':20,'D13':21,'D14':22,'D15':23,
        'CLK':24,'A0':31,'A1':32,'A2':33,'A3':34,'A4':35,'A5':38,'OE_N':39,'LED':25}
for p in U1.Pads():
    n=p.GetNumber()
    if n in ('1','40','41'): p.SetNet(bd.net('GND'))
setn(U1,2,'+3V3'); setn(U1,3,'EN'); setn(U1,13,'USB_DN'); setn(U1,14,'USB_DP'); setn(U1,27,'IO0')
for net,pin in ESPMAP.items(): setn(U1,pin,net)
# LDO: 1 GND 2 OUT(tab) 3 IN
setn(U2,1,'GND'); setn(U2,2,'+3V3'); setn(U2,3,'+5V')
for p in U2.Pads():
    if p.GetNumber()=='2': p.SetNet(bd.net('+3V3'))
setn(J10,1,'+5V'); setn(J10,2,'GND')
for p in J9.Pads():
    n=p.GetNumber()
    m={'A4':'VBUS','B4':'VBUS','A9':'VBUS','B9':'VBUS','A6':'USB_DP','B6':'USB_DP','A7':'USB_DN','B7':'USB_DN','A5':'CC1','B5':'CC2'}
    p.SetNet(bd.net(m.get(n,'GND')))
def two(f,a,bn):
    ps=sorted(f.Pads(),key=lambda q:q.GetNumber()); ps[0].SetNet(bd.net(a)); ps[1].SetNet(bd.net(bn))
two(D1,'+5V','VBUS')   # D_SMA pad1 = cathode
two(C1,'GND','+5V'); two(C2,'GND','+5V'); two(C3,'GND','+3V3'); two(C4,'GND','+3V3'); two(C5,'GND','+3V3'); two(C6,'GND','EN')
two(R1,'EN','+3V3'); two(R2,'CC1','GND'); two(R3,'CC2','GND'); two(R4,'OE_N','+3V3'); two(R5,'LED','LED_K')
two(LED1,'GND','LED_K')
for sw,net in ((SW1,'IO0'),(SW2,'EN')):
    for p in sw.Pads():
        p.SetNet(bd.net(net if p.GetNumber() in ('1','2') else 'GND'))
def portpin(sig):
    if sig.startswith('D'): return 1+2*int(sig[1:])
    return {'CLK':33,'A0':35,'A1':37,'A2':39,'A3':4,'A4':8,'A5':12}[sig]
GROUPS=[BUS[0:8],BUS[8:16],['CLK','A0','A1','A2','A3','A4','A5',None]]
for p,(J,bufs,top) in enumerate(ports):
    for pad in J.Pads(): pad.SetNet(bd.net('GND'))
    for g,(u,cc) in zip(GROUPS,bufs):
        setn(u,1,'+3V3'); setn(u,10,'GND'); setn(u,19,'OE_N'); setn(u,20,'+3V3')
        for k,sig in enumerate(g):
            ain=2+k; bout=18-k
            if sig is None: setn(u,ain,'GND'); continue
            setn(u,ain,sig); on='P%d_%s'%(p,sig); setn(u,bout,on); setn(J,portpin(sig),on)
        two(cc,'GND','+3V3')
# ---------------- routing ----------------
rt=Router(bd,0,0,W,H,step=0.25,w=0.2,clr=0.15)
# antenna keepout (module antenna points to -x when rot 90)
bb=U1.GetBoundingBox(False); ax0=bb.GetX()/MM; ay0=bb.GetY()/MM; ax1=bb.GetRight()/MM; ay1=bb.GetBottom()/MM
print('module bbox',ax0,ay0,ax1,ay1)
ant=(0,ay0-1,ax0+6.5,ay1+1)   # antenna region (left 6.5 mm of module when rotated)
rt.block_rect([0,1],*ant,None)
rt.load_board()
def pp(pad):
    x,y=pad.GetPosition().x/MM,pad.GetPosition().y/MM
    ls=[0,1] if pad.GetAttribute()==pcbnew.PAD_ATTRIB_PTH else ([0] if pad.IsOnLayer(F) else [1])
    return [(x,y,l) for l in ls]
def P(f,n): return pp(bd.pad(f,n))
fails=[]
def con(net,src,dst=None,to_net=False,w=None,**kw):
    ok=rt.connect(net,src,dst,to_net,w,**kw)
    if not ok: fails.append((net,src[0][:2]))
    return ok
t0=time.time()
# 1) buffer outputs -> connector pins
for p,(J,bufs,top) in enumerate(ports):
    for g,(u,cc) in zip(GROUPS,bufs):
        for k,sig in enumerate(g):
            if sig is None: continue
            con('P%d_%s'%(p,sig),P(u,18-k),P(J,portpin(sig)))
print('outputs done',time.time()-t0,len(fails))
# 2) bus nets: ESP pin -> each buffer input, tree
order=sorted(range(8),key=lambda p:abs(PORTX[p%4]-30)+ (0 if p<4 else 5))
for sig in BUS:
    gi=[i for i,g in enumerate(GROUPS) if sig in g][0]; k=GROUPS[gi].index(sig)
    first=True
    for p in order:
        u=ports[p][1][gi][0]
        if first: ok=con(sig,P(U1,ESPMAP[sig]),P(u,2+k)); first=False
        else: ok=con(sig,P(u,2+k),None,True)
print('bus done',time.time()-t0,len(fails))
# 3) OE_N and +3V3 for buffers
con('OE_N',P(R4,1) if bd.pad(R4,1).GetNetname()=='OE_N' else P(R4,2),P(U1,ESPMAP['OE_N']))
for p in order:
    for u,cc in ports[p][1]:
        con('OE_N',P(u,19),None,True)
# misc small nets
con('LED',P(U1,ESPMAP['LED']),[q for q in pp([x for x in R5.Pads() if x.GetNetname()=='LED'][0])])
con('LED_K',[q for q in pp([x for x in R5.Pads() if x.GetNetname()=='LED_K'][0])],[q for q in pp([x for x in LED1.Pads() if x.GetNetname()=='LED_K'][0])])
for net,a,c in (('EN',(U1,3),None),('IO0',(U1,27),None)):
    pass
def padsof(f,net): return [q for x in f.Pads() if x.GetNetname()==net for q in pp(x)]
con('EN',P(U1,3),padsof(R1,'EN')); con('EN',padsof(C6,'EN'),None,True); con('EN',padsof(SW2,'EN'),None,True)
con('IO0',P(U1,27),padsof(SW1,'IO0'))
con('USB_DP',P(U1,14),padsof(J9,'USB_DP')); con('USB_DN',P(U1,13),padsof(J9,'USB_DN'))
for x in J9.Pads():
    pass
con('USB_DP',padsof(J9,'USB_DP')[0:1],None,True); con('USB_DN',padsof(J9,'USB_DN')[0:1],None,True)
con('CC1',padsof(J9,'CC1'),padsof(R2,'CC1')); con('CC2',padsof(J9,'CC2'),padsof(R3,'CC2'))
con('VBUS',padsof(J9,'VBUS')[:1],padsof(D1,'VBUS'),w=0.5)
for q in padsof(J9,'VBUS')[1:]: con('VBUS',[q],None,True,w=0.4)
# power: +5V
con('+5V',padsof(J10,'+5V'),padsof(C1,'+5V'),w=1.0); con('+5V',padsof(U2,'+5V'),None,True,w=1.0); con('+5V',padsof(C2,'+5V'),None,True,w=0.8); con('+5V',padsof(D1,'+5V'),None,True,w=0.8)
# +3V3 tree
con('+3V3',padsof(U2,'+3V3')[:1],P(U1,2),w=0.6)
for f in (C3,C4,C5,R1,R4): con('+3V3',padsof(f,'+3V3'),None,True,w=0.4)
for p in order:
    for u,cc in ports[p][1]:
        con('+3V3',P(u,20),None,True,w=0.3); con('+3V3',P(u,1),None,True); con('+3V3',padsof(cc,'+3V3'),None,True)
print('power done',time.time()-t0,len(fails))
# 4) GND: via next to every SMD GND pad
def gnd_via(pad):
    x,y=pad.GetPosition().x/MM,pad.GetPosition().y/MM
    for r in (1.0,1.4,1.8,2.4,3.0):
        for a in range(0,360,30):
            vx=x+r*math.cos(math.radians(a)); vy=y+r*math.sin(math.radians(a))
            res=rt.route('GND',[(x,y,0)],[(vx,vy,0)],False,via_cost=10**6,maxit=3000)
            if res is None: continue
            i,j=rt.ij(vx,vy)
            if not(0<=i<rt.nx and 0<=j<rt.ny): continue
            c=rt.code('GND')
            if rt.Vg[j,i] in (-1,c) and rt.T[1][j,i] in (-1,c):
                rt.commit('GND',res,0.3,(x,y),None); vxy=rt.xy(i,j); bd.via(vxy[0],vxy[1],'GND',0.5,0.3); rt.block_circle([0,1],vxy[0],vxy[1],0.25,'GND'); return True
    fails.append(('GNDVIA',(x,y))); return False
for f in b.GetFootprints():
    for pad in f.Pads():
        if pad.GetNetname()=='GND' and pad.GetAttribute()==pcbnew.PAD_ATTRIB_SMD:
            gnd_via(pad)
# 5) zones
def zone(layer):
    z=pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(bd.net('GND')); o=z.Outline(); o.NewOutline()
    for x,y in [(0.3,0.3),(W-0.3,0.3),(W-0.3,H-0.3),(0.3,H-0.3)]: o.Append(int(x*MM),int(y*MM))
    z.SetLocalClearance(int(0.25*MM)); z.SetMinThickness(int(0.2*MM)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(int(0.25*MM)); z.SetThermalReliefSpokeWidth(int(0.35*MM)); b.Add(z)
zone(F); zone(B)
ka=pcbnew.ZONE(b); ka.SetIsRuleArea(True); ka.SetDoNotAllowTracks(True); ka.SetDoNotAllowVias(True); ka.SetDoNotAllowZoneFills(True)
ls=pcbnew.LSET(); ls.AddLayer(F); ls.AddLayer(B); ka.SetLayerSet(ls); o=ka.Outline(); o.NewOutline()
for x,y in [(ant[0]+0.3,ant[1]),(ant[2],ant[1]),(ant[2],ant[3]),(ant[0]+0.3,ant[3])]: o.Append(int(x*MM),int(y*MM))
b.Add(ka)
json.dump({'fails':fails},open(os.path.join(HERE,'route_report.json'),'w'),indent=1)
bd.save(os.path.join(HERE,'main_v1.kicad_pcb')); print('saved; fails',len(fails),fails[:20],'time',time.time()-t0)
