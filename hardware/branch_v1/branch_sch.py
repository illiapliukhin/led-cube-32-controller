#!/usr/bin/env python3
"""Branch (strand) board v1 schematic: 16 HD108/SK9822 strands, clock-gated by board ID."""
import sys,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,'../../tools'))
from schgen import write, PINNAMES
BUS=['D%d'%i for i in range(16)]+['CLK','A0','A1','A2','A3','A4','A5']
def portpin(sig):
    if sig.startswith('D'): return 1+2*int(sig[1:])
    return {'CLK':33,'A0':35,'A1':37,'A2':39,'A3':34,'A4':36,'A5':38}[sig]
C=[]
def comp(ref,val,fp,pins,lcsc='',mpn=''):
    C.append(dict(ref=ref,value=val,footprint=fp,fields={'LCSC':lcsc,'MPN':mpn},pins=pins))
for J,pre in (('J1','IN_'),('J2','L_')):
    m={portpin(s):pre+s for s in BUS}
    comp(J,'BUS_%s 2x20'%('IN' if J=='J1' else 'OUT'),'Connector_IDC:IDC-Header_2x20_P2.54mm_Vertical',
         [(str(n),m.get(n,'GND').replace(pre,'') if n in m else 'GND',m.get(n,'GND')) for n in range(1,41)],'C9138','2.54-2*20P')
G=[BUS[0:8],BUS[8:16],['CLK','A0','A1','A2','A3','A4','A5',None]]
pn=PINNAMES['74AHCT245PW']
def buf(ref,ins,outs):
    pins=[]
    for n in range(1,21):
        s=str(n); name=pn[s]
        if n==1: net='+5V'
        elif n==10: net='GND'
        elif n==19: net='GND'
        elif n==20: net='+5V'
        elif 2<=n<=9: net=ins[n-2]
        else: net=outs[18-n]
        pins.append((s,name,net))
    comp(ref,'74AHCT245PW','Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm',pins,'C173388','74AHCT245PW,118')
for i,g in enumerate(G):
    buf('U%d'%(i+1),[('IN_'+s if s else 'GND') for s in g],[('L_'+s if s else None) for s in g])
# comparator
cmp_pins=[('1','~G','GND'),('10','GND','GND'),('20','VCC','+5V'),('19','~P=Q','SEL_N')]
for k,(pp,qp) in enumerate([(2,3),(4,5),(6,7),(8,9),(11,12),(13,14),(15,16),(17,18)]):
    cmp_pins+= [(str(pp),'P%d'%k,'L_A%d'%k if k<6 else 'GND'),(str(qp),'Q%d'%k,'ID%d'%k if k<6 else 'GND')]
comp('U4','74HC688D','Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm',sorted(cmp_pins,key=lambda p:int(p[0])),'C88042','74HC688D,653')
comp('U5','SN74AHC1G32DBVR','Package_TO_SOT_SMD:SOT-23-5',[('1','A','L_CLK'),('2','B','SEL_N'),('3','GND','GND'),('4','Y','GCLK'),('5','VCC','+5V')],'C7470','SN74AHC1G32DBVR')
buf('U6',['L_D%d'%i for i in range(8)],['SDR%d'%i for i in range(8)])
buf('U7',['L_D%d'%i for i in range(8,16)],['SDR%d'%i for i in range(8,16)])
buf('U8',['GCLK']*8,['SCR%d'%i for i in range(8)])
buf('U9',['GCLK']*8,['SCR%d'%i for i in range(8,16)])
for i in range(16):
    comp('RD%d'%i,'33R','Resistor_SMD:R_0603_1608Metric',[('1','1','SDR%d'%i),('2','2','SD%d'%i)],'C23140','0603WAF330JT5E')
    comp('RC%d'%i,'33R','Resistor_SMD:R_0603_1608Metric',[('1','1','SCR%d'%i),('2','2','SC%d'%i)],'C23140','0603WAF330JT5E')
    comp('J%d'%(10+i),'STRAND%d'%i,'Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical',[('1','+5V','V5S%d'%i),('2','DATA','SD%d'%i),('3','CLK','SC%d'%i),('4','GND','GND')],'C144395','B4B-XH-A(LF)(SN)')
    # per-output fuse (2 A hold PTC) and ESD clamp on the 1 m strand lines (lesson: fuse per output, ESD at connector)
    comp('F%d'%(10+i),'PTC 2A','Fuse:Fuse_1812_4532Metric',[('1','1','+5V'),('2','2','V5S%d'%i)],'C20812','SMD1812P200TF16')
    comp('UE%d'%i,'USBLC6-2SC6','Package_TO_SOT_SMD:SOT-23-6',[('1','IO1','SD%d'%i),('6','IO1b','SD%d'%i),('3','IO2','SC%d'%i),('4','IO2b','SC%d'%i),('2','GND','GND'),('5','VBUS','+5V')],'C2827654','USBLC6-2SC6')
for k in range(6):
    comp('RID%d'%k,'10k','Resistor_SMD:R_0603_1608Metric',[('1','1','+5V'),('2','2','ID%d'%k)],'C98220','RC0603FR-0710KL')
    comp('JP%d'%k,'ID%d_SET'%k,'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm',[('1','1','ID%d'%k),('2','2','GND')])
for i in range(1,10):
    comp('C%d'%i,'100nF','Capacitor_SMD:C_0603_1608Metric',[('1','1','+5V'),('2','2','GND')],'C66501','CL10B104KO8NNNC')
for i in range(10,16):
    comp('C%d'%i,'47uF','Capacitor_SMD:C_0805_2012Metric',[('1','1','+5V'),('2','2','GND')],'C16780','CL21A476MQYNNNE')
# ---- 12 V input -> TVS -> eFuse (rev-polarity, 4.46 A limit) -> 12 A sync buck -> +5V (local injection) ----
for j in ('J30','J31'):   # in + daisy-chain out of the 12 V bus
    comp(j,'12V_BUS','TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal',[('1','+12V','V12_IN'),('2','GND','GND')],'C8465','WJ500V-5.08-2P')
comp('D30','SMBJ15A','Diode_SMD:D_SMB',[('1','K','V12_IN'),('2','A','GND')],'C83846','SMBJ15A')
comp('U30','TPS259474LRPWR','cube:TI_RPW0010A_VQFN-HR-10_2x2mm_P0.45mm',[('1','EN/UVLO','EFEN'),('2','OVLO','EFOV'),('3','PG','PG12'),('4','PGTH','EFEN'),('5','IN','V12_IN'),('6','OUT','+12V'),('7','DVDT','DVDT'),('8','GND','GND'),('9','ILM','ILM'),('10','ITIMER','ITMR')],'C2864845','TPS259474LRPWR')
for ref,val,a_,b_,c_,m_ in (('R30','100k','V12_IN','EFEN','C25803','0603WAF1003T5E'),('R31','15k','EFEN','GND','C22809','0603WAF1502T5E'),   # UVLO = 1.2*(1+100/15) = 9.2 V
                            ('R40','100k','V12_IN','EFOV','C25803','0603WAF1003T5E'),('R32','8.2k','EFOV','GND','C25981','0603WAF8201T5E'),('R33','750R','ILM','GND','C23241','0603WAF7500T5E'),('R34','10k','PG12','+5V','C98220','RC0603FR-0710KL')):
    comp(ref,val,'Resistor_SMD:R_0603_1608Metric',[('1','1',a_),('2','2',b_)],c_,m_)
comp('C30','10nF','Capacitor_SMD:C_0603_1608Metric',[('1','1','DVDT'),('2','2','GND')],'C57112','0603B103K500NT')
comp('C31','10nF','Capacitor_SMD:C_0603_1608Metric',[('1','1','ITMR'),('2','2','GND')],'C57112','0603B103K500NT')
for k in range(32,36):
    comp('C%d'%k,'10uF/50V','Capacitor_SMD:C_1206_3216Metric',[('1','1','+12V' if k>32 else 'V12_IN'),('2','2','GND')],'C13585','CL31A106KBHNNNE')
comp('U31','TPS56C215RNNR','Package_DFN_QFN:Texas_RNN0018A',[('1','BOOT','BST'),('2','VIN','+12V'),('11','VIN_2','+12V'),('3','PGND','GND'),('4','PGND_2','GND'),('5','PGND_3','GND'),('8','PGND_4','GND'),('9','PGND_5','GND'),('10','PGND_6','GND'),
    ('6','SW','SW5'),('7','SW_2','SW5'),('12','AGND','GND'),('13','FB','FB5'),('14','SS','SS5'),('15','EN','+12V'),('16','PGOOD','PG5'),('17','VREG5','VREG5'),('18','MODE','MODE5')],'C473372','TPS56C215RNNR')
comp('L30','1.5uH 20A','Inductor_SMD:L_TaiTech_TMPC1265_13.5x12.5mm',[('1','1','SW5'),('2','2','+5V')],'C5158939','YSPI1365-1R5M')
comp('C36','100nF','Capacitor_SMD:C_0603_1608Metric',[('1','1','BST'),('2','2','SW5')],'C66501','CL10B104KO8NNNC')
comp('C37','4.7uF','Capacitor_SMD:C_0603_1608Metric',[('1','1','VREG5'),('2','2','GND')],'C19666','CL10A475KO8NNNC')
comp('C38','22nF','Capacitor_SMD:C_0603_1608Metric',[('1','1','SS5'),('2','2','GND')],'C21122','CL10B223KB8NNNC')
for ref,val,a_,b_,c_,m_ in (('R35','75k','+5V','FB5','C23242','0603WAF7502T5E'),('R36','10k','FB5','GND','C98220','RC0603FR-0710KL'),
                            ('R37','120k','VREG5','MODE5','C25808','0603WAF1203T5E'),('R38','20k','MODE5','GND','C4184','0603WAF2002T5E'),('R39','10k','PG5','+5V','C98220','RC0603FR-0710KL')):
    comp(ref,val,'Resistor_SMD:R_0603_1608Metric',[('1','1',a_),('2','2',b_)],c_,m_)
for k in range(40,46):
    comp('C%d'%k,'47uF/16V','Capacitor_SMD:C_1210_3225Metric',[('1','1','+5V'),('2','2','GND')],'C77101','GRM32ER61C476KE15L')
n=write(os.path.join(HERE,'branch_v1.kicad_sch'),C,'Branch board v1 - 16 clocked RGB strands','branch_v1')
open(os.path.join(HERE,'branch_v1.kicad_pro'),'w').write('{"meta":{"filename":"branch_v1.kicad_pro","version":1}}')
print('components',n)
