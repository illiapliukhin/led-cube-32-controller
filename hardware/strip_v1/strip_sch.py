#!/usr/bin/env python3
"""1 m strip board, parametric: one 250 mm segment of a 4-segment 1 m strip (see docs/STRIP_BOARD.md).
usage: strip_sch.py N   (N = connectors per 1 m: 124, 64, 48, 32 -> n = N/4 strands per segment)
Bus in (J1) is re-driven (U1..U3) to bus out (J2) -> next segment via 2x20 IDC jumper. Clock gating per 16-strand group
(74HC688 ID compare + 1G32). Power: K identical 12 V cells (TVS, eFuse 5 A, TPS56C215 buck 5.1 V), each feeding its own
strand domain +5V_k; logic runs from +5V_0."""
import sys,os,math
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,'../../tools'))
from schgen import write, PINNAMES
N=int(sys.argv[1]); n=N//4; G=math.ceil(n/16); K=math.ceil(n*N*0.060*0.25/10.0)
BUS=['D%d'%i for i in range(16)]+['CLK','A0','A1','A2','A3','A4','A5']
def portpin(sig):
    if sig.startswith('D'): return 1+2*int(sig[1:])
    return {'CLK':33,'A0':35,'A1':37,'A2':39,'A3':34,'A4':36,'A5':38}[sig]
C=[]
def comp(ref,val,fp,pins,lcsc='',mpn=''): C.append(dict(ref=ref,value=val,footprint=fp,fields={'LCSC':lcsc,'MPN':mpn},pins=pins))
for J,pre in (('J1','IN_'),('J2','L_')):
    m={portpin(s):pre+s for s in BUS}
    comp(J,'BUS_%s 2x20'%('IN' if J=='J1' else 'OUT'),'Connector_IDC:IDC-Header_2x20_P2.54mm_Vertical',
         [(str(k),'P%d'%k,m.get(k,'GND')) for k in range(1,41)],'C9138','2.54-2*20P')
pn=PINNAMES['74AHCT245PW']
def buf(ref,ins,outs):
    pins=[]
    for k in range(1,21):
        s=str(k); net={1:'+5V',10:'GND',19:'GND',20:'+5V'}.get(k)
        if net is None: net=ins[k-2] if 2<=k<=9 else outs[18-k]
        pins.append((s,pn[s],net if net else 'unconnected-%s-%s'%(ref,s)))
    comp(ref,'74AHCT245PW','Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm',pins,'C173388','74AHCT245PW,118')
GB=[BUS[0:8],BUS[8:16],['CLK','A0','A1','A2','A3','A4','A5',None]]
for i,g in enumerate(GB): buf('U%d'%(i+1),[('IN_'+s if s else 'GND') for s in g],[('L_'+s if s else None) for s in g])
for g in range(G):
    cmp_pins=[('1','~G','GND'),('10','GND','GND'),('20','VCC','+5V'),('19','~P=Q','SEL%d_N'%g)]
    for k,(pp,qp) in enumerate([(2,3),(4,5),(6,7),(8,9),(11,12),(13,14),(15,16),(17,18)]):
        cmp_pins+=[(str(pp),'P%d'%k,'L_A%d'%k if k<6 else 'GND'),(str(qp),'Q%d'%k,'ID%d_%d'%(g,k) if k<6 else 'GND')]
    comp('U%d'%(4+2*g),'74HC688PW','Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm',sorted(cmp_pins,key=lambda p:int(p[0])),'C547141','74HC688PW,118')
    comp('U%d'%(5+2*g),'SN74AHC1G32DBVR','Package_TO_SOT_SMD:SOT-23-5',[('1','A','L_CLK'),('2','B','SEL%d_N'%g),('3','GND','GND'),('4','Y','GCLK%d'%g),('5','VCC','+5V')],'C7470','SN74AHC1G32DBVR')
    for k in range(6):
        comp('RID%d'%(10*g+k),'10k','Resistor_SMD:R_0603_1608Metric',[('1','1','+5V'),('2','2','ID%d_%d'%(g,k))],'C98220','RC0603FR-0710KL')
        comp('JP%d'%(10*g+k),'ID%d_SET'%k,'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm',[('1','1','ID%d_%d'%(g,k)),('2','2','GND')])
# strand drivers: data buffer + clock buffer per 8 strands
nb=math.ceil(n/8)
for q in range(nb):
    S=list(range(8*q,min(n,8*q+8)))
    buf('U%d'%(20+q),[('L_D%d'%(i%16)) for i in S]+['GND']*(8-len(S)),['SDR%d'%i for i in S]+[None]*(8-len(S)))
    buf('U%d'%(30+q),[('GCLK%d'%(i//16)) for i in S]+['GND']*(8-len(S)),['SCR%d'%i for i in S]+[None]*(8-len(S)))
def dom(i): return '+5V' if i*K//n==0 else '+5V_%d'%(i*K//n)
for i in range(n):
    comp('RD%d'%i,'33R','Resistor_SMD:R_0603_1608Metric',[('1','1','SDR%d'%i),('2','2','SD%d'%i)],'C23140','0603WAF330JT5E')
    comp('RC%d'%i,'33R','Resistor_SMD:R_0603_1608Metric',[('1','1','SCR%d'%i),('2','2','SC%d'%i)],'C23140','0603WAF330JT5E')
    comp('J%d'%(100+i),'STRAND%d'%i,'Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical',[('1','+5V','V5S%d'%i),('2','DATA','SD%d'%i),('3','CLK','SC%d'%i),('4','GND','GND')],'C144395','B4B-XH-A(LF)(SN)')
    comp('F%d'%(100+i),'PTC 2A','Fuse:Fuse_1812_4532Metric',[('1','1',dom(i)),('2','2','V5S%d'%i)],'C20812','SMD1812P200TF16')
    comp('UE%d'%i,'USBLC6-2SC6','Package_TO_SOT_SMD:SOT-23-6',[('1','IO1','SD%d'%i),('6','IO1b','SD%d'%i),('3','IO2','SC%d'%i),('4','IO2b','SC%d'%i),('2','GND','GND'),('5','VBUS',dom(i))],'C2827654','USBLC6-2SC6')
for k,u in enumerate(['U%d'%x for x in [1,2,3]+[4+2*g for g in range(G)]+[5+2*g for g in range(G)]+[20+q for q in range(nb)]+[30+q for q in range(nb)]]):
    comp('C%d'%(1+k),'100nF','Capacitor_SMD:C_0603_1608Metric',[('1','1','+5V'),('2','2','GND')],'C66501','CL10B104KO8NNNC')
NDEC=k+1
# ---- K power cells: 12 V terminal -> SMBJ15A -> TPS259474L eFuse (5 A, UVLO 9.2 V, OVLO 15.8 V) -> TPS56C215 -> +5V_k ----
R=lambda base,k:'%s%d'%(base,300+20*k)
for k in range(K):
    o=300+20*k; V5='+5V' if k==0 else '+5V_%d'%k; s='_%d'%k
    I=lambda nm:nm+s
    comp('J%d'%o,'12V_IN','TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal',[('1','+12V',I('V12_IN')),('2','GND','GND')],'C8465','WJ500V-5.08-2P')
    comp('D%d'%o,'SMBJ15A','Diode_SMD:D_SMB',[('1','K',I('V12_IN')),('2','A','GND')],'C83846','SMBJ15A')
    comp('U%d'%o,'TPS259474LRPWR','cube:TI_RPW0010A_VQFN-HR-10_2x2mm_P0.45mm',[('1','EN/UVLO',I('EFEN')),('2','OVLO',I('EFOV')),('3','PG',I('PG12')),('4','PGTH',I('EFEN')),('5','IN',I('V12_IN')),('6','OUT',I('V12')),('7','DVDT',I('DVDT')),('8','GND','GND'),('9','ILM',I('ILM')),('10','ITIMER',I('ITMR'))],'C2864845','TPS259474LRPWR')
    for j,(val,a_,b_,c_,m_) in enumerate((('100k',I('V12_IN'),I('EFEN'),'C25803','0603WAF1003T5E'),('15k',I('EFEN'),'GND','C22809','0603WAF1502T5E'),
            ('100k',I('V12_IN'),I('EFOV'),'C25803','0603WAF1003T5E'),('8.2k',I('EFOV'),'GND','C25981','0603WAF8201T5E'),('680R',I('ILM'),'GND','C23228','0603WAF6800T5E'),('10k',I('PG12'),V5,'C98220','RC0603FR-0710KL'),
            ('75k',V5,I('FB5'),'C23242','0603WAF7502T5E'),('10k',I('FB5'),'GND','C98220','RC0603FR-0710KL'),('120k',I('VREG5'),I('MODE5'),'C25808','0603WAF1203T5E'),('20k',I('MODE5'),'GND','C4184','0603WAF2002T5E'),('10k',I('PG5'),V5,'C98220','RC0603FR-0710KL'))):
        comp('R%d'%(o+j),val,'Resistor_SMD:R_0603_1608Metric',[('1','1',a_),('2','2',b_)],c_,m_)
    for j,(val,a_,lc,mp) in enumerate((('10nF',I('DVDT'),'C57112','0603B103K500NT'),('10nF',I('ITMR'),'C57112','0603B103K500NT'),('4.7uF',I('VREG5'),'C19666','CL10A475KO8NNNC'),('22nF',I('SS5'),'C21122','CL10B223KB8NNNC'))):
        comp('C%d'%(o+j),val,'Capacitor_SMD:C_0603_1608Metric',[('1','1',a_),('2','2','GND')],lc,mp)
    comp('C%d'%(o+4),'100nF','Capacitor_SMD:C_0603_1608Metric',[('1','1',I('BST')),('2','2',I('SW5'))],'C66501','CL10B104KO8NNNC')
    for j in range(5,9): comp('C%d'%(o+j),'10uF/50V','Capacitor_SMD:C_1206_3216Metric',[('1','1',I('V12_IN') if j==5 else I('V12')),('2','2','GND')],'C13585','CL31A106KBHNNNE')
    for j in range(9,13): comp('C%d'%(o+j),'47uF/16V','Capacitor_SMD:C_1210_3225Metric',[('1','1',V5),('2','2','GND')],'C77101','GRM32ER61C476KE15L')
    comp('U%d'%(o+1),'TPS56C215RNNR','Package_DFN_QFN:Texas_RNN0018A',[('1','BOOT',I('BST')),('2','VIN',I('V12')),('11','VIN_2',I('V12')),('3','PGND','GND'),('4','PGND_2','GND'),('5','PGND_3','GND'),('8','PGND_4','GND'),('9','PGND_5','GND'),('10','PGND_6','GND'),
        ('6','SW',I('SW5')),('7','SW_2',I('SW5')),('12','AGND','GND'),('13','FB',I('FB5')),('14','SS',I('SS5')),('15','EN',I('V12')),('16','PGOOD',I('PG5')),('17','VREG5',I('VREG5')),('18','MODE',I('MODE5'))],'C473372','TPS56C215RNNR')
    comp('L%d'%o,'1.5uH 20A','cube:L_YJYCOIN_YSPI1365',[('1','1',I('SW5')),('2','2',V5)],'C5158939','YSPI1365-1R5M')
name='strip%d_v1'%N; d=os.path.join(HERE,name); os.makedirs(d,exist_ok=True)
cnt=write(os.path.join(d,name+'.kicad_sch'),C,'1 m strip segment (%d conn/m): %d strands, %d clock groups, %d power cells'%(N,n,G,K),name)
t=os.path.join(d,'fp-lib-table'); open(t,'w').write(open(t).read().replace('${KIPRJMOD}/../../lib','${KIPRJMOD}/../../../lib'))
open(os.path.join(d,name+'.kicad_pro'),'w').write('{"meta":{"filename":"%s.kicad_pro","version":1}}'%name)
print(name,'components',cnt,'n',n,'G',G,'K',K)
