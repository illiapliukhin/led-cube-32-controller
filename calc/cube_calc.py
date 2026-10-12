#!/usr/bin/env python3
"""LED cube 32x32x32 architecture calculations. Run: python3 calc/cube_calc.py"""
N=32; LEDS=N**3; COLS=N*N; LAYERS=N
PITCH=0.03125                      # m (1 m / 32)
I_PK={'10mA':0.010,'15mA':0.015,'20mA':0.020}
CU_RHO=1.72e-8
def R(len_m,d_mm=None,a_mm2=None):
    a=(a_mm2 or 3.14159*(d_mm/2)**2)*1e-6; return CU_RHO*len_m/a
out=[]
p=lambda *a: out.append(' '.join(str(x) for x in a))
p(f"LEDs={LEDS} columns(cathode)={COLS} layers(anode)={LAYERS}")
for scan in (32,16,8):
    groups=32//scan; ch=COLS*groups; drv=ch//16
    p(f"\n-- 1/{scan} scan: channels={ch}, 16ch drivers={drv}, duty={1/scan:.4f}")
    for k,i in I_PK.items():
        layer_A=COLS*i              # one 'scan line' = 'groups' layers simultaneously
        p(f"  Ipk {k}: avg/LED={i/scan*1e3:.3f} mA, peak current per scan line={layer_A*groups:.1f} A (per layer FET {layer_A:.2f} A), all-on PSU LED current={layer_A*groups:.1f} A")
# bandwidth
p("\n-- Data bandwidth (frame data only, driver has SRAM+PWM)")
for bits in (8,16):
    for fps in (30,60,120):
        p(f"  {bits}bit x {fps} fps = {LEDS*bits*fps/1e6:.1f} Mbit/s; per lane (16 lanes) {LEDS*bits*fps/16/1e6:.2f} Mbit/s")
p("-- If MCU did BCM itself (MBI5124 style, no SRAM): 1024 ch x 8 planes x 32 lines x 960 Hz =",
  f"{1024*8*32*960/1e6:.0f} Mbit/s  -> not feasible on one ESP32-S3 SPI")
# MBI5153 refresh (13-bit mode, 1:32): 513 GCLK per line segment (datasheet: verify)
for gclk in (12.5e6,20e6,25e6):
    line=513; fr=gclk/(line*32)
    p(f"  GCLK {gclk/1e6:.1f} MHz: scan refresh={fr:.0f} Hz (S-PWM splits 16-bit frame into sub-periods; visual refresh = this)")
# voltage budget
p("\n-- LED rail budget @ Ipk 10 mA, layer current 10.24 A")
vf=3.1; vknee=0.5; fet=0.010*10.24; feed=R(1.2,a_mm2=1.5)*2*10.24/2  # fed from 2 points
mesh=0.15
tot=vf+vknee+fet+feed+mesh
p(f"  Vf={vf} driver knee={vknee} FET={fet:.3f} feed(1.5mm2,1.2m,2 feeds)={feed:.3f} mesh={mesh} -> need {tot:.2f} V; use 4.5-5.0 V rail")
for vr in (4.5,5.0):
    pd=(vr-tot+vknee)*COLS*0.010
    p(f"  rail {vr} V: total driver dissipation all-on={pd:.1f} W -> per chip (64) {pd/64*1000:.0f} mW")
# column wire
p(f"\n-- Column wire 0.8 mm Cu 1.05 m: R={R(1.05,0.8)*1e3:.1f} mOhm, drop @10 mA = {R(1.05,0.8)*0.01*1e6:.0f} uV (negligible)")
# layer mesh: 32 row wires each 1 m carrying up to 32x10mA
p(f"  Layer row wire 0.8 mm 1 m carries 0.32 A: worst drop (fed one end, distributed) = {R(1.0,0.8)*0.32/2*1e3:.1f} mV")
# capacitance
p("\n-- Parasitics: LED Cj ~30 pF")
p(f"  column: 32 LEDs -> {32*30} pF; layer node: 1024 LEDs -> {1024*30/1000:.1f} nF; discharge to 0.5 V via 47 ohm pull-down tau={1024*30e-12*47*1e6:.2f} us")
# power
p("\n-- Power budget (10 mA design)")
led=10.24*5.0; logic=0.5*5+64*0.02*5
p(f"  LED all-on {led:.0f} W + logic ~{logic:.0f} W -> PSU 5V >=15 A; recommend Mean Well LRS-100-5 (18 A) or LRS-150F-5 (30 A) for 15 mA option")
# mass and material
wire_m=COLS*1.05 + LAYERS*(32*1.0+2*1.0)
p(f"\n-- Wire length ~{wire_m:.0f} m of 0.8 mm tinned Cu = {wire_m*4.47/1000:.1f} kg; LEDs {LEDS*0.25/1000:.1f} kg (5 mm ~0.25 g)")
p(f"  solder joints ~{LEDS*2+COLS*2:,}")
print('\n'.join(out)); open('calc/results.txt','w').write('\n'.join(out)+'\n')
