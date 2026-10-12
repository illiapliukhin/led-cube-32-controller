"""Resolution-per-size table (v1.1: HD108, 12 V bus). Output: calc/size_table.md"""
import math
BITS=64; PCLK=13.3e6; LANES=16; BR=16; PORTS=8; CHAIN=8
I_LED=0.060; ABL=0.25; APL=0.15; ETA=0.92
PX=(0.22,0.35)      # $/pixel: HD108 retail strip (superlightingled 60/m 5 m $65.98) .. custom string estimate
MB_COST=45; BR_COST=14; PSU=('LRS-600-12',600*0.9,95)  # usable W per PSU (90% load), $ each
KG_PX=0.0012; KG_WIRE_M=0.035                           # pixel node + 4-core 22AWG per m (approx); frame added separately
rows=[]
for size,N in ((1,32),(1,48),(1,64),(2,64),(2,96),(2,128)):
    leds=N**3; strands=N*N; br=math.ceil(strands/BR); mb=math.ceil(br/(PORTS*CHAIN))
    # one main board: 16 lanes, each lane carries one strand of every branch in turn (strands time-shared)
    leds_per_mb=leds/mb; bits_lane=leds_per_mb/LANES*BITS
    fps=PCLK/bits_lane; rate=leds*BITS*fps/1e6
    pmax=leds*I_LED*5; pabl=pmax*ABL; ptyp=pmax*APL
    nps=math.ceil(pabl/ETA/PSU[1])
    cost_led=(leds*PX[0],leds*PX[1]); cost_el=mb*MB_COST+br*BR_COST+nps*PSU[2]
    kg=leds*KG_PX+strands*size*1.1*KG_WIRE_M+ (40 if size==1 else 160)
    rows.append((size,N,1000*size/N,leds,strands,br,mb,mb*PORTS,rate,fps,ptyp/1e3,pabl/1e3,pmax/1e3,nps,cost_led,cost_el,kg))
o=['| Size | LEDs/axis | Pitch | LEDs | Strands (outputs) | Branch boards | Main boards / ribbon ports | Data rate | fps (16-bit) | Power typ (APL 15 %) | ABL 25 % cap | Abs. max | 12 V PSUs (LRS-600-12) | LED cost | Electronics+PSU | Weight |',
   '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
for r in rows:
    s,N,p,l,st,br,mb,po,rate,fps,pt,pa,pm,nps,cl,ce,kg=r
    o.append(f'| {s} m³ | **{N}** | {p:.1f} mm | {l:,} | {st:,} | {br} | {mb} / {po} | {rate:.0f} Mbit/s | {fps:.0f} | {pt:.1f} kW | {pa:.1f} kW | {pm:.1f} kW | {nps} | ${cl[0]/1e3:.1f}k–{cl[1]/1e3:.1f}k | ${ce/1e3:.1f}k | {kg:.0f} kg |')
open(__file__.replace('size_table.py','size_table.md'),'w').write('\n'.join(o)+'\n')
print('\n'.join(o))
